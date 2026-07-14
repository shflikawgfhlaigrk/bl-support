# Support surface v1.2 — inbound eval (price index active)

- Total messages: **50** (source: read-only IMAP INBOX, last 50 messages (data/inbound.json))
- Price index: **ACTIVE** (9 live-verified rows)
- ANSWERED with citation: **0** (of which verified-price: **0**)
- REFUSED (escalated to human): **50**
- Uncited answers (MUST be 0): **0**

Most real inbound is internal briefs / vendor / recruiting mail, not product-support questions, so a high REFUSE rate is CORRECT — the engine escalates rather than guessing. Price questions that name a product with a LIVE-verified price answer WITH a citation.

| # | From | Subject | Verdict | Citation | Reason |
|---|------|---------|---------|----------|--------|
| 0 | @mail.instagram.com | Your email confirmation code | REFUSED | — | below-threshold(coverage=0.06<0.34) |
| 1 | @gmail.com | Re: agreements | REFUSED | — | below-threshold(coverage=0.21<0.34) |
| 2 | @google.com | Notes: Meeting Jul 13, 2026 at 7:00 PM EDT | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 3 | @mail.notion.so | Notion 3.6: HTML blocks | REFUSED | — | below-sensitive-threshold(coverage=0.07<0.5) |
| 4 | @higgsfield.ai | New device signed in to your Higgsfield[.] | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 5 | @google.com | Michael, review your Google Account settin | REFUSED | — | below-threshold(coverage=0.15<0.34) |
| 6 | @accounts.google.com | Security alert | REFUSED | — | below-threshold(coverage=0.12<0.34) |
| 7 | @askforfunding.com | Three Active Investors from Ask For Fundin | REFUSED | — | below-threshold(coverage=0.10<0.34) |
| 8 | @linear.app | Reminder to post a project update for Utah | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 9 | @slack.com | Linear mentioned you in #Linear | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 10 | @askforfunding.com | Funded Deals This Week | REFUSED | — | below-threshold(coverage=0.05<0.34) |
| 11 | @gmail.com | Re: Marketing | REFUSED | — | below-threshold(coverage=0.06<0.34) |
| 12 | @gmail.com | Appointment canceled: Black label Software | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 13 | @alerts.getflex.com | We’re giving 10 Flex members up to $2K tow | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 14 | @qualtrics-survey.com | Your experience with Twilio | REFUSED | — | below-threshold(coverage=0.05<0.34) |
| 15 | @google.com | Notes: “interview 2” Jul 13, 2026 | REFUSED | — | below-threshold(coverage=0.11<0.34) |
| 16 | @gmail.com | Re: Marketing | REFUSED | — | below-threshold(coverage=0.13<0.34) |
| 17 | @google.com | Share request for "Sales" | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 18 | @amazon.com | Your package was removed from the Amazon L | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 19 | @otter.ai | Your upcoming meetings | REFUSED | — | below-threshold(overlap=2<3, coverage=0.06<0.34) |
| 20 | @gmail.com | Utah morning brief — 2026-07-12 | REFUSED | — | below-threshold(coverage=0.04<0.34) |
| 21 | @gmail.com | Re: Black Label Internship | REFUSED | — | below-threshold(coverage=0.07<0.34, content-overlap=1<2) |
| 22 | @email.claude.com | Fable 5 access and increased Claude Code r | REFUSED | — | below-threshold(overlap=2<3, coverage=0.12<0.34) |
| 23 | @gmail.com | Re: Black Label Internship | REFUSED | — | below-threshold(coverage=0.06<0.34) |
| 24 | @gmail.com | Re: Black Label Internship | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 25 | @email.openai.com | Your scheduled tasks are getting better | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 26 | @blvigil.com | Utah morning brief — 2026-07-11 | REFUSED | — | below-threshold(coverage=0.04<0.34) |
| 27 | @sentry.io | Reminder: Create a project (free trial end | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 28 | @visible.vc | Continue Building Your Fundraising Momentu | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 29 | @otter.ai | We'd love to hear from you Michael | REFUSED | — | below-threshold(overlap=2<3, coverage=0.06<0.34) |
| 30 | @gmail.com | Appointment booked: Black label Software ( | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 31 | @gmail.com | Westend Drum Cheat Sheet (FL Studio) | REFUSED | — | below-threshold(overlap=2<3, coverage=0.03<0.34) |
| 32 | @gmail.com | Frozen-Dairy Distributor Contacts — 829 le | REFUSED | — | below-threshold(coverage=0.12<0.34) |
| 33 | @linear.app | Reminder to post a project update for Utah | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 34 | @info.getflex.com | Your Flex Rent Line of Credit statement is | REFUSED | — | below-sensitive-threshold(coverage=0.10<0.5) |
| 35 | @askforfunding.com | Founders like you got funded this week. Yo | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 36 | @slack.com | Linear mentioned you in #Linear | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 37 | @mail.docusign.com | You're in! Welcome to Docusign | REFUSED | — | below-threshold(overlap=2<3, coverage=0.11<0.34) |
| 38 | @visible.vc | The investor reply you forgot to follow up | REFUSED | — | below-sensitive-threshold(overlap=3<4, coverage=0.05<0.5) |
| 39 | @info.getflex.com | Got a minute? Leave Flex a review. | REFUSED | — | below-threshold(overlap=2<3, coverage=0.05<0.34) |
| 40 | @mg.homedepot.com | Projects Get Done Here 📍 For $100 a Month | REFUSED | — | below-threshold(overlap=2<3, coverage=0.05<0.34) |
| 41 | @slack.com | Your trial of Slack’s Pro plan has ended | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 42 | @e.mail.realtor.com | / Top US Listings: See What's Trending / | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 43 | @al.mail.deepseek.com | Your verification code for DeepSeek | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 44 | @askforfunding.com | Three Active Investors from Ask For Fundin | REFUSED | — | below-threshold(coverage=0.10<0.34) |
| 45 | @google.com | Aden left a review for Black Label Trading | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 46 | @google.com | cade left a review for black label bots | REFUSED | — | below-threshold(coverage=0.11<0.34, content-overlap=1<2) |
| 47 | @linear.app | Reminder to post a project update for Utah | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 48 | @slack.com | Linear mentioned you in #Linear | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 49 | @updates.linear.app | New login to Linear | REFUSED | — | below-threshold(overlap=1<3, coverage=0.11<0.34, content-overlap=1<2) |
