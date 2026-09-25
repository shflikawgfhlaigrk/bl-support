"""No temporary-file writes or shared probe races in answer admission."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
import sys
from support import answerer


def test_planted_probe_symlink_is_never_opened(tmp_path, monkeypatch):
    victim=tmp_path/'victim';victim.write_text('preserved')
    probe=tmp_path/'probe.txt';probe.symlink_to(victim)
    monkeypatch.setattr(answerer,'Path',lambda value:probe)
    monkeypatch.setitem(sys.modules,'claim_linter',SimpleNamespace(scan_text=lambda text:[],lint=lambda paths:[]))
    assert answerer._claim_clean('synthetic text')
    assert victim.read_text()=='preserved' and probe.is_symlink()


def test_parallel_answers_are_scanned_independently(monkeypatch):
    monkeypatch.setitem(sys.modules,'claim_linter',SimpleNamespace(scan_text=lambda text:[] if text=='clean' else [('unsupported','reason',text)]))
    texts=['clean','unsupported']*50
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(answerer._claim_clean,texts))
    assert results==[text=='clean' for text in texts]


def test_linter_failure_is_a_controlled_refusal(monkeypatch):
    def broken(text):raise RuntimeError('synthetic scanner failure')
    monkeypatch.setitem(sys.modules,'claim_linter',SimpleNamespace(scan_text=broken))
    assert not answerer._claim_clean('ordinary text')


def test_same_real_claim_rules_are_applied_in_memory(tmp_path):
    import claim_linter
    for text in ['Set up your mailbox in settings.', 'Guaranteed profits from automated trading.']:
        source=tmp_path/'comparison.txt';source.write_text(text)
        assert answerer._claim_clean(text)==(not claim_linter.lint([source]))
