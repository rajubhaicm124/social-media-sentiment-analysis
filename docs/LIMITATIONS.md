# API Limitations, Ethics and Privacy

Read this before citing any number produced by SocialScope AI.

## Privacy and ethics notice

> SocialScope AI analyses data available through supported platform APIs and
> permitted public sources. It does not bypass privacy settings,
> authentication, security controls, or platform restrictions.

* Only fields the platform itself publishes on public content are collected.
* No private account data is requested, stored or inferred.
* API credentials live only in the server environment; they are never sent to
  the browser and never committed.
* The display name is a local browser preference used to label analyses, not an
  identity, and it stores no personal information.
* The app does not track users and uses no third-party analytics.
* The bundled demo dataset is synthetic. It is not real social-media data and
  must never be presented as a platform metric.

## Data actually available per platform

### YouTube — YouTube Data API v3

**Available**

* Video ID, title, description, channel ID and channel name
* Published date, category ID, video duration
* View count, like count, comment count
* Public comment text, author display name, author channel ID, published date
* Comment reply count, and `totalReplyCount`
* Official thumbnail URLs
* Duration and tags (only when the API returns them)

**Not available**

| Field | Why |
|---|---|
| **Share count** | The YouTube Data API v3 exposes no share metric at all. Always reported as unavailable. |
| Comment like count | Returned only to the content owner (or via the authenticated `mine` context). |
| Channel subscriber count | Returned only for the authenticated owner's own channel. |
| Video tags | Absent from most video responses; the app falls back to hashtags found in the description and marks the source. |
| Removed / held / hidden comments | Not accessible through any permitted endpoint. |
| Deleted, private or age-restricted videos | Return an empty item list; reported as an error, not as zero data. |

**Sampling.** Each `commentThreads` page costs one unit of the standard quota,
so retrieval is capped by `MAX_COMMENT_PAGES` (default 5, up to 100 comments per
page). A thread larger than the cap is **sampled**, and the analysis says so
explicitly rather than implying complete coverage.

### Facebook — Meta Graph API

**Available (Page-owned content only)**

* Post ID, text, creation time, post type, permalink
* Page name and Page ID
* Reaction totals, share count, comment count
* Comment text, author, timestamp, like count
* Video view count for video posts

**Not available**

| Field | Why |
|---|---|
| Posts on personal profiles | The Graph API cannot read them; a Page token is mandatory. |
| Insights for unowned content | Restricted to content the token's Page manages. |
| Comment moderation status | Never exposed. |
| Full reaction breakdown | Requires extra permissions and separate calls. |

Only the **first comment page** is retrieved (limit 100). Larger threads are
noted in the analysis notes.

### Instagram — Meta Graph API

**Available (professional account media only)**

* Media ID, caption, timestamp, media type
* Like count, comment count
* Media insights: reach, impressions, views (owner only)
* Comment text for owned media

**Not available**

| Field | Why |
|---|---|
| **Share count** | Not exposed by the Instagram Graph API. Always reported as unavailable. |
| Any public post by shortcode | The API **cannot resolve a shortcode**. The app lists the authorised account's media and matches the shortcode; if the media is not owned by that account, the limitation is reported explicitly. |
| Hashtag / mention insights | Restricted to the owning account. |
| Personal (non-professional) accounts | Not supported by the API. |

Media insights are optional. If the `insights` call fails, those metrics stay
`null` and are reported as unavailable — the app does not fall back to a proxy
number.

## General constraints

**Authentication is always required.** No platform offers public analytics
without a credential. Without one, `/api/analyze` returns HTTP 503 naming the
environment variable to set. It never returns demo data as if it were live.

**Rate limits and quota.** YouTube charges quota units per call; a 10,000-unit
daily default supports roughly 6,000 comment pages. SocialScope AI adds its own
sliding-window limit per client (default 30 requests / 60 seconds) on the
analysis endpoints. Exceeding either returns HTTP 429 with a friendly message.

**Moderation is permanent.** Comments removed by moderators, hidden by creators,
or deleted by authors are gone. Any comment dataset is therefore a lower bound
on the true audience response, and comment counts can exceed the number of
records actually retrieved.

**Sentiment is an estimate.** VADER is a deterministic lexicon model: fast,
reproducible and transparent, but it is not a human judgement. Accuracy drops
for sarcasm, irony, emoji-only comments, code-switching, very short text, and
domain jargon. The app reports the engine in use and shows the TextBlob
comparison so the classification can be sanity-checked.

**Correlation is not causation.** The reported Pearson coefficients describe
co-movement within one dataset at one point in time. They do not establish that
one metric causes another, and they are confounded by posting time, audience
size and platform ranking.

**Timezones.** Timestamps are stored in UTC. Hour-of-day peaks reflect UTC, not
the analyser's local time — the UI states this.

**Language detection is a heuristic.** A small marker-word heuristic labels each
record; it is not a certified language identifier.

## Academic honesty

This project exists to demonstrate a defensible DAE process:

* Unavailable metrics are displayed as unavailable, never approximated.
* Synthetic demo data is banner-labelled in the interface, stored with
  `data_mode="demo"`, and marked inside every export.
* Insight sentences are generated from calculated values; the limitations list
  is always shown with the results.
* The original pre-cleaning dataset is preserved and downloadable, so every
  figure can be traced back to its source.

If a figure cannot be obtained lawfully, the correct result is an honest gap.
