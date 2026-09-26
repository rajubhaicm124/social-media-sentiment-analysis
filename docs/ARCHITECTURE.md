# Architecture

## Layer map

```text
┌────────────────────────────────────────────────────────────────┐
│  Browser — React + TypeScript + Vite + Tailwind + ECharts       │
│  Landing · Welcome · Dashboard · Analysis · Table · Exports      │
└───────────────┬────────────────────────────────────────────────┘
                │ JSON over HTTP (typed client in services/api.ts)
┌───────────────▼────────────────────────────────────────────────┐
│  API layer — FastAPI routers                                     │
│  api/analysis.py   detect · analyze · demo · read results         │
│  api/export.py     CSV · XLSX · HTML/PDF                          │
│  api/history.py    history · profile                              │
│  core/             errors · rate limiting · URL safety            │
└───────────────┬────────────────────────────────────────────────┘
┌───────────────▼────────────────────────────────────────────────┐
│  Pipeline — analysis/                                            │
│  cleaning → sentiment → engagement → statistics → keywords        │
│           → insights → charts                                     │
└───────────────┬──────────────────────────────┬──────────────────┘
                │                              │
┌───────────────▼──────────────┐  ┌────────────▼──────────────────┐
│  Adapters — platforms/        │  │  Persistence — repository.py  │
│  youtube · facebook ·         │  │  SQLAlchemy ORM → SQLite or   │
│  instagram · demo             │  │  PostgreSQL                   │
│  (official APIs only)         │  │                               │
└───────────────┬───────────────┘  └───────────────────────────────┘
                │
      ┌─────────▼─────────┐
      │ YouTube Data API  │
      │ Meta Graph API    │
      └───────────────────┘
```

## Design decisions

### 1. The adapter boundary is the extension point

`PlatformAdapter` defines one job: return the data the official API exposes, and
declare which fields were available. Adding a platform requires a new adapter
module, an entry in `PLATFORM_SPECS`, and one line in `ADAPTERS`. No pipeline,
API or frontend code changes.

The base class owns HTTP concerns — timeouts, status-code translation, and
turning platform error payloads into `PlatformAPIError` — so adapters contain
only field mapping.

### 2. Unavailable is a first-class value

`None` propagates from the adapter through the pipeline, the database, the API
and every export. It is never coerced to `0`.

* `engagement.py` returns `engagement_rate_available: false` and omits the rate
  when an input is missing.
* The frontend `MetricTile` prints *"Data unavailable through the current
  platform API."* instead of a number.
* ECharts receives `null` rather than `0`, so the bar is genuinely absent
  instead of a misleading zero-height bar.
* The CSV leaves the cell empty.

This is the single most important design rule in the project.

### 3. Two datasets, both preserved

The adapter's untouched output is kept as `raw_records` and written to
`data/raw/<id>.json` for audit. The cleaned, scored records are what every
statistic is computed from. The cleaning report counts exactly what was removed
at each stage, and the raw dataset remains downloadable.

### 4. Sentiment is deterministic and self-describing

VADER is the classifier; TextBlob supplies polarity and subjectivity for
comparison. Both are optional at runtime — `engine_status()` reports which are
actually installed, and the UI and the limitations list say so. There is no
hidden fallback that could quietly change the numbers.

### 5. Statistics without a scientific stack

`statistics.py` implements mean, median, mode, variance, standard deviation,
percentiles and Pearson correlation in plain Python. The DAE figures are
therefore reproducible on a bare install. pandas/numpy are listed in
`requirements-optional.txt` for notebook work, not imported by the runtime.

### 6. Charts are computed server-side

`pipeline.build_charts` emits finished series. The frontend binds them to
ECharts without reshaping, so chart logic is testable in Python and identical
for every client.

### 7. The rate limiter sits on the API edge

`core/ratelimit.py` is an in-process sliding window keyed by client IP, applied
to the analysis endpoints only. `/detect` is exempt because the UI calls it
while typing.

## Data model

```text
analyses
  id · public_id · source_url · platform · data_mode · status
  content_id · channel_id · author_name · title · content_type
  published_at · thumbnail_url
  available_fields[] · unavailable_fields[]
  views · likes · comment_count · shares · subscribers      ← NULL = not provided
  total_records · removed_records · engagement_rate
  positive_pct · neutral_pct · negative_pct · avg_sentiment
  analysis_seconds · sentiment_method
  raw_payload{} · metrics{} · charts{} · statistics{}
  trends{} · keywords[] · hashtags[] · insights[] · limitations[]
  user_name · created_at
        │ 1
        │
        ├───────► social_records        (one row per analysed text record)
        │           record_type · comment_id · author_* · raw_text · clean_text
        │           word_count · char_count · language · published_at
        │           like_count · reply_count
        │           sentiment · compound · positive/negative/neutral
        │           polarity · subjectivity · final_score · confidence · engines{}
        │           hashtags[] · mentions[] · keywords[] · emotion
        │           is_duplicate · is_spam · is_outlier · flags[]
        │
        └───────► reports               (export audit trail)
                    report_type · filename · byte_size · created_at
```

`NULL` in any metric column is meaningful and is the mechanism behind
"unavailable is a first-class value".

## Request flow

1. The UI debounces the URL, calls `POST /detect`, and shows the platform.
2. `POST /analyze` validates the URL, detects the platform, checks credentials,
   and rate-limits the client.
3. The adapter fetches content and comments with paging, then declares
   availability.
4. The pipeline cleans, scores, computes engagement, statistics, keywords,
   charts, insights and limitations.
5. `repository.save_analysis` writes the analysis and every record in one
   transaction; the raw snapshot is written to `data/raw/`.
6. The complete payload is returned, so the first paint needs no extra calls.

## Security

| Concern | Mitigation |
|---|---|
| Credential exposure | Keys read from the environment only; the API never returns them, and `/health` returns booleans |
| SSRF / unsafe schemes | Only `http`/`https`, real hostnames required, `localhost` rejected |
| Lookalike domains | Exact suffix matching, so `evil.com/youtube.com` is rejected |
| Rate abuse | Sliding-window limiter on analysis endpoints |
| Slow upstreams | Client timeouts on every platform call |
| Injection | SQLAlchemy parameter binding; ORM throughout |
| XSS | React escapes by default; no `dangerouslySetInnerHTML`; the HTML report escapes all interpolated values |
| Error leakage | Central handlers return friendly messages and log the detail server-side |
| Header injection | Filenames are generated, not taken from user input |

## Known trade-offs

* **Synchronous analysis.** Simple to run and reason about, but a very large
  comment thread would hold a request open. A job queue is the next step.
* **In-process rate limiter.** Correct for a single worker; multi-worker
  deployments need shared state such as Redis.
* **No authentication.** The display name is a local preference, not an
  identity. Anyone with the URL can read analyses.
* **SQLite default.** Ideal for a local academic project; PostgreSQL is
  configured but not load-tested.
* **Full ECharts import.** A ~340 kB gzipped vendor chunk, split into its own
  file so it caches independently. Per-chart imports would trim it at the cost
  of significant complexity.
