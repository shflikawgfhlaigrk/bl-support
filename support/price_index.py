#!/usr/bin/env python3
"""price_index.py — a LIVE-VERIFIED, cite-or-refuse price index.

The support engine's default is to refuse price questions (a wrong price is the most
costly thing it could say). This module lets it answer "how much is <product>" WITH a
citation instead — but ONLY for a product whose price it can prove live, in this same
build, from three INDEPENDENT sources that must agree:

  1. Served storefront asset — blacklabelbots.com/assets/stripe-links.js — is the price
     the site DISPLAYS, next to the exact checkout link the buyer clicks (TRIAL[key]).
  2. Served product page — the price token must appear in the live-curled product page a
     buyer actually reads (e.g. blacklabelbots.com/trading shows "$49/mo").
  3. Stripe (read-only) — the price object resolved from THAT payment link's line item.
     Resolved by following the link, never mapped by amount (metadata/routing only), so a
     stale duplicate price at the same dollar figure can never be picked.
  4. Canonical price gate — the agreed price must pass support.price_gate.CANONICAL.

A row is ADMITTED only when all four agree AND the link/price/product are all active.
Any product missing a same-session four-way agreement is REFUSED (left out of the index),
so the answerer falls CLOSED and escalates rather than guessing. (Example: `signals` is
served at $100/mo but $100/mo is not in the canonical gate → it is correctly excluded.)

Each admitted row carries its citations: the storefront URL(s) it was read from AND the
Stripe price_id it was resolved to. Zero runtime deps: urllib + the read-only Stripe key.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import price_gate

STOREFRONT = "https://blacklabelbots.com"
ASSET_URL = f"{STOREFRONT}/assets/stripe-links.js"
STRIPE_KEY_PATH = Path.home() / ".utah" / "secrets" / "stripe.json"


@dataclass(frozen=True)
class Product:
    key: str            # stripe-links.js key (checkout routing key)
    display: str        # human name surfaced in the answer
    aliases: frozenset  # question tokens that identify this product
    page: str           # served product page whose live HTML must show the price


# The current public slate (keys match the served stripe-links.js LINKS/TRIAL maps).
# `page` is a real served URL a buyer reads; its live HTML must contain the price token.
PRODUCTS = [
    Product("sovereign", "Black Label Sovereign", frozenset({"sovereign"}), f"{STOREFRONT}/sovereign"),
    Product("trading", "Black Label Trading", frozenset({"trading"}), f"{STOREFRONT}/trading"),
    Product("marketing", "Black Label Marketing", frozenset({"marketing"}), f"{STOREFRONT}/marketing"),
    Product("realestate", "Black Label Real Estate", frozenset({"realestate", "estate"}), f"{STOREFRONT}/realestate"),
    Product("academy", "Black Label Academy", frozenset({"academy"}), f"{STOREFRONT}/academy"),
    Product("circuit", "Black Label Circuit", frozenset({"circuit"}), f"{STOREFRONT}/circuit"),
    Product("sunset", "Black Label Sunset", frozenset({"sunset", "mixing", "mastering"}), f"{STOREFRONT}/"),
    Product("homefront", "Black Label Vigil", frozenset({"vigil", "homefront"}), f"{STOREFRONT}/homefront"),
    Product("customWeb", "Custom Website", frozenset({"website", "site"}), f"{STOREFRONT}/"),
]


@dataclass
class PriceRow:
    key: str
    display: str
    price: str                 # canonical, gate-clean price string, e.g. "$49/mo"
    aliases: frozenset
    price_id: str              # Stripe price object id (citation)
    checkout_url: str          # the served checkout link the buyer clicks (citation)
    storefront_url: str        # the served product page the price was read from (citation)
    asset_url: str = ASSET_URL # the served asset the displayed price was read from

    def citation(self) -> str:
        return f"{self.storefront_url} · Stripe price {self.price_id}"


# --- price normalization ---------------------------------------------------------
def normalize_price(p: str) -> str:
    """'$49 / month' -> '$49/mo'; drop thousands sep and spaces; lowercase suffix."""
    t = p.strip().replace(" ", "").replace(",", "").lower()
    t = t.replace("/month", "/mo").replace("/year", "/yr")
    return t


def price_str_from_stripe(unit_amount: int | None, interval: str | None) -> str:
    amt = (unit_amount or 0) / 100
    base = f"${amt:.0f}" if amt == int(amt) else f"${amt:.2f}"
    if interval == "month":
        return base + "/mo"
    if interval == "year":
        return base + "/yr"
    return base


# --- live fetchers (default; injectable for hermetic tests) ----------------------
class LiveFetchers:
    """Real network fetchers: served storefront + read-only Stripe price objects."""

    def __init__(self, stripe_key: str | None = None, timeout: int = 30):
        self.timeout = timeout
        if stripe_key is None:
            stripe_key = json.loads(STRIPE_KEY_PATH.read_text())["secret_key"]
        self._key = stripe_key
        self._url2plink: dict[str, dict] | None = None

    def _get(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "blb-support-price-build"})
        return urllib.request.urlopen(req, timeout=self.timeout).read().decode("utf-8", "replace")

    def _api(self, path: str) -> dict:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/" + path,
            headers={"Authorization": "Bearer " + self._key},
        )
        return json.loads(urllib.request.urlopen(req, timeout=self.timeout).read())

    def get_asset(self, url: str) -> str:
        return self._get(url)

    def get_page(self, url: str) -> str:
        return self._get(url)

    def _load_payment_links(self) -> dict[str, dict]:
        if self._url2plink is not None:
            return self._url2plink
        out: dict[str, dict] = {}
        starting_after = None
        for _ in range(20):  # hard page cap
            q = "payment_links?limit=100" + (f"&starting_after={starting_after}" if starting_after else "")
            d = self._api(q)
            for p in d.get("data", []):
                out[p["url"]] = {"id": p["id"], "active": p.get("active", False)}
            if not d.get("has_more"):
                break
            starting_after = d["data"][-1]["id"]
        self._url2plink = out
        return out

    def stripe_price_for_link(self, checkout_url: str) -> dict | None:
        """Resolve the served checkout link -> its line-item price object (or None).

        Never maps by amount: it follows the exact link the buyer clicks, so a stale
        duplicate price at the same dollar figure cannot be substituted.
        """
        pl = self._load_payment_links().get(checkout_url)
        if not pl:
            return None
        li = self._api(f"payment_links/{pl['id']}/line_items?expand[]=data.price.product")
        data = li.get("data") or []
        if len(data) != 1:  # a single-product link only; anything else is ambiguous -> refuse
            return None
        pr = data[0].get("price") or {}
        prod = pr.get("product") or {}
        return {
            "price_id": pr.get("id"),
            "price": price_str_from_stripe(pr.get("unit_amount"), (pr.get("recurring") or {}).get("interval")),
            "price_active": bool(pr.get("active")),
            "product_active": bool(prod.get("active")) if isinstance(prod, dict) else False,
            "link_active": bool(pl["active"]),
        }


# --- the build -------------------------------------------------------------------
def parse_served_asset(js: str) -> tuple[dict, dict]:
    """Parse LINKS (checkout urls) and TRIAL (displayed prices) from stripe-links.js."""
    links = dict(re.findall(r"(\w+):\s*'(https://buy\.stripe\.com/[^']+)'", js))
    trial = dict(re.findall(r"(\w+):\s*\{\s*model:\s*'[^']+',\s*price:\s*'([^']+)'", js))
    return links, trial


def build_index(fetchers: object | None = None) -> tuple[list[PriceRow], list[dict]]:
    """Return (admitted_rows, admission_log). Fail-closed on any disagreement."""
    if fetchers is None:
        fetchers = LiveFetchers()

    log: list[dict] = []
    rows: list[PriceRow] = []

    try:
        js = fetchers.get_asset(ASSET_URL)
    except Exception as e:  # served asset unreachable -> admit nothing
        return [], [{"key": "*", "admitted": False, "reason": f"asset-fetch-failed: {e}"}]
    links, trial = parse_served_asset(js)

    for prod in PRODUCTS:
        entry: dict = {"key": prod.key, "admitted": False}
        checkout_url = links.get(prod.key)
        if not checkout_url:
            entry["reason"] = "no served checkout link"
            log.append(entry)
            continue

        # Displayed price: TRIAL map when present (recurring/one-time slate), else a
        # link-only product (customWeb) has no TRIAL entry -> displayed price comes from
        # the product page + Stripe only (two independent sources still required).
        displayed = trial.get(prod.key)

        try:
            sp = fetchers.stripe_price_for_link(checkout_url)
        except Exception as e:
            entry["reason"] = f"stripe-resolve-failed: {e}"
            log.append(entry)
            continue
        if not sp or not sp.get("price_id"):
            entry["reason"] = "stripe price not resolvable from link"
            log.append(entry)
            continue
        if not (sp["link_active"] and sp["price_active"] and sp["product_active"]):
            entry["reason"] = (f"inactive: link={sp['link_active']} "
                               f"price={sp['price_active']} product={sp['product_active']}")
            log.append(entry)
            continue

        stripe_price = normalize_price(sp["price"])

        # (1) served asset must agree with Stripe (when a displayed price exists).
        if displayed is not None and normalize_price(displayed) != stripe_price:
            entry["reason"] = f"served/stripe mismatch: displayed={displayed} stripe={sp['price']}"
            log.append(entry)
            continue

        # (2) the price token must appear in the LIVE product page a buyer reads.
        try:
            page = fetchers.get_page(prod.page)
        except Exception as e:
            entry["reason"] = f"page-fetch-failed: {e}"
            log.append(entry)
            continue
        if not _page_shows_price(page, stripe_price):
            entry["reason"] = f"price {sp['price']} not shown on served page {prod.page}"
            log.append(entry)
            continue

        # (3) canonical price gate — the last, founder-confirmed check.
        if not price_gate.check(sp["price"]):
            entry["reason"] = f"non-canonical price {sp['price']} (fail-closed)"
            log.append(entry)
            continue

        rows.append(PriceRow(
            key=prod.key, display=prod.display, price=sp["price"], aliases=prod.aliases,
            price_id=sp["price_id"], checkout_url=checkout_url, storefront_url=prod.page,
        ))
        entry.update(admitted=True, price=sp["price"], price_id=sp["price_id"],
                     storefront_url=prod.page, checkout_url=checkout_url)
        log.append(entry)

    return rows, log


def _page_shows_price(page_html: str, norm_price: str) -> bool:
    """True if the normalized price token appears in the page's text (spacing-tolerant)."""
    # collapse whitespace and thousands sep, lowercase, then look for the token with
    # optional spaces around '/', e.g. '$49 / mo' or '$49/mo'.
    txt = re.sub(r"\s+", " ", page_html).replace(",", "").lower()
    m = re.match(r"^\$(\d+(?:\.\d{2})?)(/(?:mo|yr))?$", norm_price)
    if not m:
        return False
    amt, suf = m.group(1), (m.group(2) or "")
    if suf:
        unit = suf[1:]  # mo|yr
        long = "month" if unit == "mo" else "year"
        pat = rf"\$\s?{re.escape(amt)}\s?/\s?(?:{unit}|{long})"
    else:
        pat = rf"\$\s?{re.escape(amt)}(?!\d)"
    return re.search(pat, txt) is not None


def index_to_dicts(rows: list[PriceRow]) -> list[dict]:
    return [{
        "key": r.key, "display": r.display, "price": r.price, "price_id": r.price_id,
        "checkout_url": r.checkout_url, "storefront_url": r.storefront_url,
        "asset_url": r.asset_url, "aliases": sorted(r.aliases),
    } for r in rows]


if __name__ == "__main__":
    rows, log = build_index()
    print(f"admitted {len(rows)} price rows "
          f"({sum(1 for e in log if not e.get('admitted'))} refused)\n")
    for r in rows:
        print(f"  {r.display:26} {r.price:8}  [{r.citation()}]")
    print("\nrefused:")
    for e in log:
        if not e.get("admitted"):
            print(f"  {e['key']:12} {e.get('reason')}")
