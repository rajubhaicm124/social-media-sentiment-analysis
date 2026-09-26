# SocialScope AI — API Contract

Base URL in development: `http://localhost:8000/api`
Interactive reference: `http://localhost:8000/docs`

## Conventions

* All request and response bodies are JSON.
* Analysis identifiers are 16-character hex strings (`public_id`), not the
  auto-increment database key.
* All timestamps are ISO-8601 in UTC.
* Numeric metric fields are `null` when the platform API did not return them.
  `null` never means zero.
* Errors always use the same envelope:

```json
{ "error": { "code": "invalid_url", "message": "…", "detail": {} } }
```

## System

### `GET /health`

Returns service status, environment, database dialect, per-platform credential
presence (**booleans only** — never key values), the active sentiment engine,
demo-mode state and the rate-limit configuration.

### `GET /platforms`

```json
{
  "platforms": [
    {
      "key": "youtube",
      "label": "YouTube",
      "configured": true,
      "credential_env_var": "YOUTUBE_API_KEY",
      "url_examples": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
      "limitations": ["Share count is not exposed by the YouTube Data API v3…"]
    }
  ],
  "demo_mode_enabled": true
}
```

## Analysis

### `POST /detect`

```json
{ "url": "https://youtu.be/dQw4w9WgXcQ" }
```

Returns `platform`, `platform_label`, `configured` and a human-readable
`message`. Detecting a URL is intentionally **not** rate-limited, because the
frontend calls it on every keystroke.

### `POST /analyze`

```json
{ "url": "https://www.youtube.com/watch?v=…", "user_name": "Aarav" }
```

Runs the full pipeline and returns the complete analysis object. Same contract
for `/analyze/youtube`, `/analyze/facebook` and `/analyze/instagram`, except
those assert the detected platform and return `platform_mismatch` (422) if the
URL belongs to a different one.

The response includes:

| Key | Description |
|---|---|
| `analysis_id`, `platform`, `data_mode`, `status` | Identity and provenance |
| `content` | Platform-specific content metadata |
| `provenance` | API name and endpoints called |
| `available_fields` / `unavailable_fields` | What the API did and did not return |
| `total_records` / `removed_records` | Cleaning outcome |
| `cleaning_report` | Per-stage removal counts |
| `sentiment_summary` / `sentiment_status` / `sentiment_comparison` | NLP results |
| `engagement` / `comment_engagement` | Engagement metrics with availability flags |
| `statistics` | Descriptive stats, correlations, length and hourly histograms |
| `trends` | Daily, weekly and hour-of-day series |
| `charts` | Pre-computed series for every visualisation |
| `keywords`, `hashtags` | Frequency with sentiment where relevant |
| `insights` | Sentences built from calculated values |
| `limitations` | Per-analysis caveats |
| `records` | Every analysed record |

### `POST /demo`

```json
{ "platform": "youtube", "user_name": "Aarav" }
```

Runs the same pipeline over a bundled **synthetic** dataset. The response adds
`demo_notice`, and `limitations[0]` always begins with `DEMO DATA`.

## Reading results

### `GET /analysis/{id}`

The full analysis object, identical to the `POST /analyze` response.

### `GET /analysis/{id}/comments`

| Parameter | Default | Notes |
|---|---|---|
| `search` | — | Matches text, author, keywords and hashtags |
| `sentiment` | — | `positive`, `neutral`, `negative` |
| `date_from` / `date_to` | — | ISO-8601 |
| `min_likes` | — | Integer |
| `sort` | `published_at` | `published_at`, `likes`, `sentiment`, `length` |
| `order` | `desc` | `asc` or `desc` (pattern-validated) |
| `page` / `page_size` | `1` / `25` | `page_size` max 500 |

Returns `total`, `page`, `pages` and the `records` slice.

### `GET /analysis/{id}/sentiment`

The summary counts, the active engine status, and one comparison row per record
with VADER compound, TextBlob polarity, TextBlob subjectivity and the final
label.

### `GET /analysis/{id}/engagement`

Engagement metrics (including `engagement_rate_available` and
`interactions_included`), per-comment engagement, correlations and the list of
unavailable fields.

## History and profile

| Method | Route | Notes |
|---|---|---|
| `GET` | `/history` | Optional `user_name`, `platform`, `limit` (max 500) |
| `GET` | `/history/{id}` | One summary row |
| `DELETE` | `/history/{id}` | Deletes the analysis, its records and its export metadata |
| `GET` | `/profile` | Current totals; optional `user_name` |
| `GET` | `/profile/{name}` | Totals for one name |
| `POST` | `/profile/rename` | `{ "user_name": "New", "previous_name": "Old" }` reassigns stored analyses |

## Exports

| Method | Route | Returns |
|---|---|---|
| `GET` | `/analysis/{id}/export/csv` | `text/csv`; `?dataset=clean` (default) or `raw` |
| `GET` | `/analysis/{id}/export/excel` | Styled `.xlsx` workbook |
| `GET` | `/analysis/{id}/export/report` | `?format=html` (default) or `pdf` |

Every export is generated from the stored analysis on the server and is logged
in the `reports` table. Each response carries a `Content-Disposition` filename.

## Status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 404 | Unknown analysis or route |
| 422 | Validation failure, invalid/unsupported URL, platform mismatch, or no public data |
| 429 | Rate limit exceeded (`rate_limited`) |
| 502 | Upstream platform API failure |
| 503 | Live analysis requested without a credential |
| 500 | Unexpected error (logged server-side, never traced to the client) |
