import { Fragment, useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, ChevronUp, Copy, Check, Filter, RotateCcw, X } from 'lucide-react'
import { getComments } from '../services/api'
import type { SocialRecord } from '../types'
import { Badge, Button, EmptyState, SearchInput, Select, SentimentBadge } from './ui'
import { formatDateTime, formatScore, truncate } from '../utils/format'

const PAGE_SIZE = 15

type SortKey = 'published_at' | 'likes' | 'sentiment' | 'length'

/**
 * Server-backed data table. Search/filter/sort/pagination run through the API
 * so the same behaviour works on large datasets.
 */
export function RecordsTable({
  analysisId,
  initialRecords,
}: {
  analysisId: string
  initialRecords: SocialRecord[]
}) {
  const [records, setRecords] = useState<SocialRecord[]>(initialRecords)
  const [total, setTotal] = useState(initialRecords.length)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(false)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [sentiment, setSentiment] = useState('all')
  const [sortKey, setSortKey] = useState<SortKey>('published_at')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [minLikes, setMinLikes] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [copiedId, setCopiedId] = useState<number | null>(null)

  // Debounce the search box so typing does not spam the API.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 350)
    return () => window.clearTimeout(timer)
  }, [search])

  const hasFilters =
    debouncedSearch !== '' ||
    sentiment !== 'all' ||
    minLikes !== '' ||
    dateFrom !== '' ||
    dateTo !== ''

  const fetchRecords = useCallback(async () => {
    setLoading(true)
    try {
      const response = await getComments(analysisId, {
        search: debouncedSearch || undefined,
        sentiment: sentiment === 'all' ? undefined : sentiment,
        min_likes: minLikes ? Number(minLikes) : undefined,
        date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        date_to: dateTo ? new Date(`${dateTo}T23:59:59`).toISOString() : undefined,
        sort: sortKey,
        order,
        page,
        page_size: PAGE_SIZE,
      })
      setRecords(response.records)
      setTotal(response.total)
      setPages(response.pages)
    } catch {
      // The analysis page surfaces load errors; here we simply keep the last
      // good page so the table does not flash empty.
    } finally {
      setLoading(false)
    }
  }, [analysisId, debouncedSearch, sentiment, minLikes, dateFrom, dateTo, sortKey, order, page])

  useEffect(() => {
    void fetchRecords()
  }, [fetchRecords])

  const resetFilters = () => {
    setSearch('')
    setSentiment('all')
    setMinLikes('')
    setDateFrom('')
    setDateTo('')
    setPage(1)
  }

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setOrder((current) => (current === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setOrder('desc')
    }
    setPage(1)
  }

  const copyRow = async (record: SocialRecord) => {
    const text = [
      `comment_id: ${record.comment_id ?? '—'}`,
      `author: ${record.author_name ?? '—'}`,
      `published_at: ${record.published_at ?? '—'}`,
      `likes: ${record.like_count ?? 'unavailable'}`,
      `sentiment: ${record.sentiment} (${formatScore(record.final_score)})`,
      `text: ${record.raw_text}`,
    ].join('\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(record.id)
      window.setTimeout(() => setCopiedId(null), 1600)
    } catch {
      // Clipboard can be blocked; nothing destructive happens.
    }
  }

  const sortIndicator = (key: SortKey) =>
    sortKey === key ? (
      order === 'asc' ? (
        <ChevronUp size={13} className="text-brand" />
      ) : (
        <ChevronDown size={13} className="text-brand" />
      )
    ) : null

  const headerCell = (key: SortKey, label: string, extraClass = '') => (
    <th className={`px-3 py-2.5 text-left ${extraClass}`} scope="col" aria-sort={sortKey === key ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}>
      <button
        type="button"
        onClick={() => toggleSort(key)}
        className="flex items-center gap-1 text-[11px] font-bold tracking-wide uppercase transition hover:text-ink"
      >
        {label}
        {sortIndicator(key)}
      </button>
    </th>
  )

  return (
    <div>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2.5 border-b border-line p-4">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search comments, authors, keywords…"
          className="min-w-[220px] flex-1"
        />
        <Select
          value={sentiment}
          onChange={(value) => {
            setSentiment(value)
            setPage(1)
          }}
          options={[
            { value: 'all', label: 'All sentiment' },
            { value: 'positive', label: 'Positive' },
            { value: 'neutral', label: 'Neutral' },
            { value: 'negative', label: 'Negative' },
          ]}
          className="w-40"
        />
        <Button
          size="md"
          variant={showFilters ? 'primary' : 'secondary'}
          onClick={() => setShowFilters((value) => !value)}
          icon={<Filter size={14} />}
        >
          Filters
        </Button>
        {hasFilters ? (
          <Button size="md" variant="ghost" onClick={resetFilters} icon={<RotateCcw size={14} />}>
            Reset
          </Button>
        ) : null}
        <Badge tone="muted" className="ml-auto">
          {total.toLocaleString()} record{total === 1 ? '' : 's'}
        </Badge>
      </div>

      {showFilters ? (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="grid gap-3 overflow-hidden border-b border-line bg-ink/2 p-4 sm:grid-cols-3"
        >
          <div>
            <label htmlFor="min-likes" className="mb-1.5 block text-[11px] font-semibold text-muted">
              Minimum likes
            </label>
            <input
              id="min-likes"
              type="number"
              min={0}
              value={minLikes}
              onChange={(event) => {
                setMinLikes(event.target.value)
                setPage(1)
              }}
              placeholder="Any"
              className="w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none focus:border-brand"
            />
          </div>
          <div>
            <label htmlFor="date-from" className="mb-1.5 block text-[11px] font-semibold text-muted">
              From date
            </label>
            <input
              id="date-from"
              type="date"
              value={dateFrom}
              onChange={(event) => {
                setDateFrom(event.target.value)
                setPage(1)
              }}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none focus:border-brand"
            />
          </div>
          <div>
            <label htmlFor="date-to" className="mb-1.5 block text-[11px] font-semibold text-muted">
              To date
            </label>
            <input
              id="date-to"
              type="date"
              value={dateTo}
              onChange={(event) => {
                setDateTo(event.target.value)
                setPage(1)
              }}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink outline-none focus:border-brand"
            />
          </div>
        </motion.div>
      ) : null}

      {/* Table */}
      {records.length === 0 && !loading ? (
        <EmptyState
          title="No matching records"
          description="Adjust the search text or clear the filters to see more comments."
          action={
            hasFilters ? (
              <Button variant="secondary" onClick={resetFilters} icon={<X size={14} />}>
                Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className={`overflow-x-auto transition-opacity ${loading ? 'opacity-55' : 'opacity-100'}`}>
          <table className="data-table w-full min-w-[860px] text-sm">
            <thead className="border-b border-line">
              <tr className="text-muted">
                {headerCell('published_at', 'Comment')}
                {headerCell('likes', 'Likes', 'text-right')}
                {headerCell('sentiment', 'Sentiment')}
                {headerCell('length', 'Length', 'text-right')}
                <th className="px-3 py-2.5 text-left text-[11px] font-bold tracking-wide uppercase">Published</th>
                <th className="px-3 py-2.5 text-right text-[11px] font-bold tracking-wide uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <Fragment key={record.id}>
                  <tr className="border-b border-line/60 transition-colors last:border-0 hover:bg-ink/3">
                    <td className="max-w-md px-3 py-3">
                      <button
                        type="button"
                        onClick={() => setExpanded(expanded === record.id ? null : record.id)}
                        className="flex w-full items-start gap-2 text-left"
                        aria-expanded={expanded === record.id}
                      >
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[13px] text-ink">
                            {truncate(record.raw_text, 120)}
                          </span>
                          <span className="mt-0.5 block text-[11px] text-muted">
                            {record.author_name ?? 'Unknown author'}
                            {record.record_type === 'caption' ? ' · caption' : ''}
                          </span>
                        </span>
                        {expanded === record.id ? (
                          <ChevronUp size={14} className="mt-0.5 shrink-0 text-muted" />
                        ) : (
                          <ChevronDown size={14} className="mt-0.5 shrink-0 text-muted" />
                        )}
                      </button>

                      {expanded === record.id ? (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="mt-2.5 space-y-2 overflow-hidden rounded-xl bg-ink/4 p-3"
                        >
                          <p className="text-xs leading-relaxed whitespace-pre-wrap text-ink">
                            {record.raw_text}
                          </p>
                          <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] sm:grid-cols-4">
                            {[
                              { label: 'Compound', value: formatScore(record.compound) },
                              { label: 'Polarity', value: formatScore(record.polarity) },
                              { label: 'Subjectivity', value: formatScore(record.subjectivity) },
                              { label: 'Confidence', value: formatScore(record.confidence) },
                            ].map((item) => (
                              <div key={item.label}>
                                <dt className="text-muted">{item.label}</dt>
                                <dd className="font-semibold tabular-nums text-ink">{item.value}</dd>
                              </div>
                            ))}
                          </dl>
                          {record.hashtags.length || record.keywords.length ? (
                            <div className="flex flex-wrap gap-1.5">
                              {record.hashtags.map((tag) => (
                                <Badge key={tag} tone="brand">
                                  #{tag}
                                </Badge>
                              ))}
                              {record.keywords.slice(0, 5).map((word) => (
                                <Badge key={word} tone="muted">
                                  {word}
                                </Badge>
                              ))}
                            </div>
                          ) : null}
                          {record.flags.length ? (
                            <p className="text-[11px] text-amber-500">Flags: {record.flags.join(', ')}</p>
                          ) : null}
                        </motion.div>
                      ) : null}
                    </td>

                    <td className="px-3 py-3 text-right tabular-nums">
                      {record.like_count === null ? (
                        <span
                          className="text-[11px] text-muted italic"
                          title="Not available through the platform API"
                        >
                          n/a
                        </span>
                      ) : (
                        <span className="text-ink">{record.like_count.toLocaleString()}</span>
                      )}
                    </td>

                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <SentimentBadge sentiment={record.sentiment} />
                        <span className="text-xs tabular-nums text-muted">
                          {formatScore(record.final_score, 2)}
                        </span>
                      </div>
                    </td>

                    <td className="px-3 py-3 text-right text-xs tabular-nums text-muted">
                      {record.char_count}
                    </td>

                    <td className="px-3 py-3 text-xs whitespace-nowrap text-muted">
                      {formatDateTime(record.published_at)}
                    </td>

                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => copyRow(record)}
                        className="rounded-lg p-1.5 text-muted transition hover:bg-ink/6 hover:text-ink"
                        aria-label={`Copy row for ${record.comment_id ?? record.id}`}
                        title="Copy row"
                      >
                        {copiedId === record.id ? (
                          <Check size={14} className="text-positive" />
                        ) : (
                          <Copy size={14} />
                        )}
                      </button>
                    </td>
                  </tr>
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pages > 1 ? (
        <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-3">
          <p className="text-xs text-muted">
            Page {page} of {pages}
          </p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage((value) => Math.max(1, value - 1))}
            >
              Previous
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={page >= pages}
              onClick={() => setPage((value) => Math.min(pages, value + 1))}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
