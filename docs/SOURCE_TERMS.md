# Source terms: YouTube Data API and Product Hunt API

Read on 2026-10-18 for sources slice 2 (YouTube, Product Hunt) and 2026-10-19 (the Risk candidates). These two had credentials ready, but both of their plan rows said the terms had to be checked before wiring. Each finding quotes a primary source. **UNCONFIRMED** marks a point those sources do not settle. The outcome: both rows move to "held" in `web/i18n/sources-plan.json`, and no collector is written.

Why the licence matters: dehype's code is AGPL-3.0-or-later and its published data is CC BY-SA 4.0. That licence lets anyone reuse the data, commercially included. Each day's input manifest is also kept for good, in a dated GitHub Release and the public ledger.

## YouTube Data API

Sources:
- Developer Policies (DP), "Last updated 2026-10-15": https://developers.google.com/youtube/terms/developer-policies
- API Services Terms of Service (ToS), "Last updated 2026-09-14": https://developers.google.com/youtube/terms/api-services-terms-of-service
- Derived metrics policy: https://developers.google.com/youtube/terms/derived-metrics-policy
- Branding Guidelines: https://developers.google.com/youtube/terms/branding-guidelines

**Storage.** Titles and statistics fetched with an API key are Non-Authorized Data (DP IV).
- DP III.E.4.e: "may temporarily store limited amounts of Non-Authorized Data for as long as is necessary for the purposes of the API Client but not longer than 30 calendar days ... after 30 calendar days, the API Client must either delete or refresh the stored data."
- DP III.E.4.c: "an API Client must not store statistics retrieved as Non-Authorized Data for more than 30 days."

Consequence: the permanent manifest and ledger could carry no YouTube API Data at all, and the history database would need a 30-day purge.

**Counts.**
- DP III.E.4.i: "must not (i) replace API Data with similar, independently calculated data, or (ii) access or use API Data to create new or derived data or metrics." Among its examples of what is not allowed: "a score that factors in likes, total views, or any other API Data".
- DP III.E.2.a: "Do not aggregate API Data except that you may only aggregate API Data relating to YouTube channels that are under the same content owner".
- DP III.L and the derived metrics policy: an exception applies only to "audited developers with analytics use cases that have explicitly applied for permission". Even then, statistics may be kept "for up to 36 calendar months", not for good.

**Summed view counts are not allowed**, for three reasons: they would sum across channels, they would be built from views, and they would be kept for good. **A per-story count of matching videos is UNCONFIRMED.** It is dehype's own number, not one YouTube returns, but clause (ii) can be read to forbid any metric derived from API Data.

**Display and credentials.**
- DP III.A.1: an API Client "must display a link to YouTube's Terms of Service" and state that users agree to them.
- DP III.A.2: an API Client needs a privacy policy that names YouTube API Services and links the Google Privacy Policy.
- DP III.D.2.d: "must not ... embed your API Credentials in open source projects". The key would stay an Actions secret.

**Licence.** ToS §16.2 grants "no other rights or licenses", and DP III.G.1.a forbids anyone to "redistribute, or sublicense all or any portion of YouTube API Services". So no figure that is API Data can carry CC BY-SA.

**Verdict: held.** The video count could be wired only after an answer on DP III.E.4.i(ii). It would also need the 30-day purge, no YouTube data in the manifest or ledger, a "dehype count, not from YouTube" label, and the YouTube ToS and privacy links on the page. Views stay out in every case. The owner decides whether to ask Google, accept the reading, or drop YouTube.

## Product Hunt API

Sources:
- API docs: https://api.producthunt.com/v2/docs
- Rate limits: https://api.producthunt.com/v2/docs/rate_limits/headers
- Terms (https://www.producthunt.com/tos, "Effective date: August 17th 2014"; https://www.producthunt.com/legal shows the same date).

https://www.producthunt.com/terms returns 404, and the terms page refuses direct download, so the terms quotes below are fragments read through a fetch tool.

**Commercial use.**
- API docs: "The Product Hunt API must not be used for commercial purposes. If you would like to use it for your business, please contact us at hello@producthunt.com."
- Terms: "You will only use the Services for your own internal, personal, non-commercial use".
- Terms: you won't "use, copy, reproduce, modify, translate, publish, broadcast, transmit, distribute" Content you do not own.

dehype's own use is non-commercial. But publishing launch names and upvotes under CC BY-SA would let others reuse them commercially, which these clauses forbid. Whether upvote counts alone are protected Content is UNCONFIRMED.

**Attribution and limits.** Attribution is requested, not required ("We kindly ask that you include attribution in your project, linking back to Product Hunt"). The quota is "6250 complexity points for every 15 minutes" on GraphQL.

**Verdict: held** until Product Hunt gives written permission (hello@producthunt.com) that covers republication under CC BY-SA.

## Revisit triggers (YouTube, Product Hunt)

Held is not dropped, and only the owner decides to drop or to ask. Each row is reopened when one of these happens:
- **YouTube:**
  - Google answers DP III.E.4.i(ii) for a per-story count of matching videos;
  - the Developer Policies change that clause (check each "Last updated" date);
  - the owner accepts the narrow "own count" reading with the conditions above.
- **Product Hunt:**
  - Product Hunt grants written permission covering CC BY-SA republication;
  - its API terms drop the commercial-use ban.

The agent may draft the questions to Google and to Product Hunt; only the owner sends them.

Owner task while both are held: revoke or restrict the unused `YOUTUBE_API_KEY` and `PRODUCTHUNT_TOKEN` in BWS.

## Risk panel candidates (read 2026-10-19)

These are terms only. The Risk panel stays "no qualified source" until the owner answers O12 (what the risk log is for); no fetcher is written before that.

Several primary pages could not be read directly: federalregister.gov's HTML pages redirect to a bot block, eur-lex.europa.eu pages came back empty, and oecd.org answered 403. Clauses marked † are search-engine extracts of those pages, to check in a browser before any wiring.

**Federal Register API.** Wire with conditions.
- Reuse: "There are no restrictions on the republication of material appearing in the Federal Register" (daily issue masthead, https://www.govinfo.gov/content/pkg/FR-2026-05-29/pdf/FR-2026-05-29-FrontMatter.pdf). US government works carry no copyright (https://www.govinfo.gov/about/policies), and "customary credit should be given to the Government department or agency which prepared the material".
- Access: "programmatic access to these sites is limited to access to our extensive developer APIs" (https://unblock.federalregister.gov/). The API answers without a key; pagination stops at "the first 2000 results"†. The rate limit is UNCONFIRMED.
- Disclaimer: FederalRegister.gov "is not an official legal edition of the Federal Register"†, while the govinfo PDF is the official legal equivalent.
- Conditions: use the API only, never the HTML pages; store the govinfo `pdf_url` beside `html_url` and label FederalRegister.gov unofficial; credit the issuing agency; keep requests few; exclude third-party copyrighted material.

**EUR-Lex.** Wire with conditions, after the † clauses are checked.
- Editorial content, summaries and consolidated texts are "licensed under the Creative Commons Attribution 4.0 International licence"†, and legal documents "can be reused for commercial or non-commercial purposes"† (https://eur-lex.europa.eu/content/legal-notice/legal-notice.html).
- Metadata is CC0 1.0 under the Commission's 2019 reuse decision (https://digital-strategy.ec.europa.eu/en/news/rules-reuse-commission-information). Reusers must "acknowledge the source and indicate any changes" (https://op.europa.eu/en/web/about-us/legal-notices/publications-office-of-the-european-union-copyright), and third-party content "requires prior authorisation".
- Access: the SOAP web service is "freely available after registration"† (EU Login) with a capped daily number of calls†. The Cellar SPARQL terms are UNCONFIRMED.
- Conditions: "© European Union" with a EUR-Lex link and a note of changes; metadata and summaries only, no logos; skip third-party items; register or confirm the SPARQL terms first.

**OECD AI Incidents Monitor.** Held.
- "© 2026 OECD. All rights reserved" (https://oecd.ai/en/incidents). The incident data "is provided by Event Registry", and the OECD "cannot and do not grant any rights to use or otherwise exploit these protected materials" (https://oecd.ai/en/incidents-methodology).
- The earlier scouting note "no bulk or API" was partly wrong: the page offers "Download results", under unstated terms. Whether an API exists is UNCONFIRMED.
