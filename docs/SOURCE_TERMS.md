# Source terms: YouTube Data API and Product Hunt API

Read on 2026-10-18 for sources slice 2. These two had credentials ready, but both of their plan rows said the terms had to be checked before wiring. Each finding quotes a primary source. **UNCONFIRMED** marks a point those sources do not settle. The outcome: both rows move to "held" in `web/i18n/sources-plan.json`, and no collector is written.

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
