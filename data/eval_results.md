# Support surface v1 — inbound eval

- Total messages: **50** (source: read-only IMAP INBOX, last 50 messages (data/inbound.json))
- ANSWERED (grounded + cited): **0**
- REFUSED (escalated to human): **50**
- Uncited answers (MUST be 0): **0**

Most real inbound is internal briefs / vendor / recruiting mail, not product-support questions, so a high REFUSE rate is CORRECT — the engine escalates rather than guessing.

| # | From | Subject | Verdict | Citation | Reason |
|---|------|---------|---------|----------|--------|
| 0 | @gmail.com | Utah morning brief — 2026-07-12 | REFUSED | — | below-threshold(coverage=0.04<0.34) |
| 1 | @gmail.com | Re: Black Label Internship | REFUSED | — | below-threshold(coverage=0.07<0.34, content-overlap=1<2) |
| 2 | @email.claude.com | Fable 5 access and increased Claude Code r | REFUSED | — | below-threshold(overlap=2<3, coverage=0.12<0.34) |
| 3 | @gmail.com | Re: Black Label Internship | REFUSED | — | below-threshold(coverage=0.06<0.34) |
| 4 | @gmail.com | Re: Black Label Internship | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 5 | @email.openai.com | Your scheduled tasks are getting better | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 6 | @blvigil.com | Utah morning brief — 2026-07-11 | REFUSED | — | below-threshold(coverage=0.04<0.34) |
| 7 | @sentry.io | Reminder: Create a project (free trial end | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 8 | @visible.vc | Continue Building Your Fundraising Momentu | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 9 | @otter.ai | We'd love to hear from you Michael | REFUSED | — | below-threshold(overlap=2<3, coverage=0.06<0.34) |
| 10 | @gmail.com | Appointment booked: Black label Software ( | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 11 | @gmail.com | Westend Drum Cheat Sheet (FL Studio) | REFUSED | — | below-threshold(overlap=2<3, coverage=0.03<0.34) |
| 12 | @gmail.com | Frozen-Dairy Distributor Contacts — 829 le | REFUSED | — | below-threshold(coverage=0.12<0.34) |
| 13 | @linear.app | Reminder to post a project update for Utah | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 14 | @info.getflex.com | Your Flex Rent Line of Credit statement is | REFUSED | — | below-sensitive-threshold(coverage=0.10<0.5) |
| 15 | @askforfunding.com | Founders like you got funded this week. Yo | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 16 | @slack.com | Linear mentioned you in #Linear | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 17 | @mail.docusign.com | You're in! Welcome to Docusign | REFUSED | — | below-threshold(overlap=2<3, coverage=0.11<0.34) |
| 18 | @visible.vc | The investor reply you forgot to follow up | REFUSED | — | below-sensitive-threshold(overlap=3<4, coverage=0.05<0.5) |
| 19 | @info.getflex.com | Got a minute? Leave Flex a review. | REFUSED | — | below-threshold(overlap=2<3, coverage=0.05<0.34) |
| 20 | @mg.homedepot.com | Projects Get Done Here 📍 For $100 a Month | REFUSED | — | below-threshold(overlap=2<3, coverage=0.05<0.34) |
| 21 | @slack.com | Your trial of Slack’s Pro plan has ended | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 22 | @e.mail.realtor.com | / Top US Listings: See What's Trending / | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 23 | @al.mail.deepseek.com | Your verification code for DeepSeek | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 24 | @askforfunding.com | Three Active Investors from Ask For Fundin | REFUSED | — | below-threshold(coverage=0.10<0.34) |
| 25 | @google.com | Aden left a review for Black Label Trading | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 26 | @google.com | cade left a review for black label bots | REFUSED | — | below-threshold(coverage=0.11<0.34, content-overlap=1<2) |
| 27 | @linear.app | Reminder to post a project update for Utah | REFUSED | — | below-threshold(coverage=0.10<0.34, content-overlap=1<2) |
| 28 | @slack.com | Linear mentioned you in #Linear | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 29 | @updates.linear.app | New login to Linear | REFUSED | — | below-threshold(overlap=1<3, coverage=0.11<0.34, content-overlap=1<2) |
| 30 | @accounts.google.com | Security alert | REFUSED | — | below-threshold(coverage=0.11<0.34) |
| 31 | @accounts.google.com | Security alert for mthburnsbarber@gmail.co | REFUSED | — | below-threshold(coverage=0.11<0.34) |
| 32 | @accounts.google.com | Security alert for mthburnsbarber@gmail.co | REFUSED | — | below-threshold(coverage=0.11<0.34) |
| 33 | @accounts.google.com | Security alert | REFUSED | — | below-threshold(coverage=0.11<0.34) |
| 34 | @google.com | You are now a manager of black label bots | REFUSED | — | below-threshold(coverage=0.11<0.34) |
| 35 | @google.com | michael barber invited you to manage black | REFUSED | — | below-threshold(coverage=0.13<0.34) |
| 36 | @google.com | Invite only: Help shape the future of Goog | REFUSED | — | below-threshold(coverage=0.10<0.34) |
| 37 | @askforfunding.com | michael, Investors Capable of Providing $2 | REFUSED | — | below-threshold(coverage=0.07<0.34, content-overlap=0<2) |
| 38 | @rentcafe.com | Summer Savings at The Quinn - We Welcome Y | REFUSED | — | below-sensitive-threshold(overlap=3<4, coverage=0.06<0.5) |
| 39 | @sentry.io | No project = missed bugs | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 40 | @askforfunding.com | Recently Funded Companies on AskForFunding | REFUSED | — | below-threshold(overlap=2<3, coverage=0.05<0.34) |
| 41 | @account.docusign.net | Your code is 633951 | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 42 | @mg.homedepot.com | ⭕️ Ending SOON ⭕️ 4th of July Deals | REFUSED | — | below-threshold(overlap=2<3, coverage=0.05<0.34) |
| 43 | @email.slackhq.com | Michael, try creating a channel in Slack | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 44 | @google.com | Updates to Google Play Terms of Service | REFUSED | — | below-threshold(coverage=0.07<0.34) |
| 45 | @e.mail.realtor.com | See new homes before anyone else | REFUSED | — | below-threshold(coverage=0.06<0.34) |
| 46 | @email.claude.com | Fable 5 access is extended through Sunday | REFUSED | — | below-threshold(overlap=1<3, coverage=0.10<0.34, content-overlap=1<2) |
| 47 | @leasing-thompsonthrift.com | Re: Apartment Inquiry at The Quinn Luxury  | REFUSED | — | below-threshold(coverage=0.08<0.34) |
| 48 | @google.com | Black Label Trading, your performance repo | REFUSED | — | below-threshold(coverage=0.09<0.34) |
| 49 | @askforfunding.com | Three Active Investors from Ask For Fundin | REFUSED | — | below-threshold(coverage=0.10<0.34) |
