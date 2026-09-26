/** Shared API types. Mirrors the FastAPI response contracts. */

export type PlatformKey = 'youtube' | 'facebook' | 'instagram'
export type SentimentKey = 'positive' | 'neutral' | 'negative'

export interface SentimentCounts {
  total: number
  positive: number
  neutral: number
  negative: number
  positive_pct: number
  neutral_pct: number
  negative_pct: number
  avg_compound: number
  avg_polarity: number
  avg_subjectivity: number
  distribution: { name: string; key: SentimentKey; value: number }[]
}

export interface EngagementMetrics {
  views: number | null
  likes: number | null
  comments: number | null
  shares: number | null
  subscribers: number | null
  total_interactions: number | null
  engagement_rate: number | null
  engagement_rate_available: boolean
  interactions_included: string[]
  likes_per_analyzed_comment: number | null
  analyzed_comments: number
  unavailable_fields: string[]
  notes: string[]
}

export interface SocialRecord {
  id: number
  record_type: string
  comment_id: string | null
  author_id: string | null
  author_name: string | null
  parent_id: string | null
  raw_text: string
  clean_text: string
  word_count: number
  char_count: number
  language: string | null
  published_at: string | null
  like_count: number | null
  reply_count: number | null
  sentiment: SentimentKey
  compound: number | null
  positive: number | null
  negative: number | null
  neutral: number | null
  polarity: number | null
  subjectivity: number | null
  final_score: number | null
  confidence: number | null
  engines: {
    primary?: string
    textblob_source?: string
    vader?: { positive: number; negative: number; neutral: number; compound: number }
    textblob?: { polarity: number; subjectivity: number }
  }
  hashtags: string[]
  mentions: string[]
  keywords: string[]
  emotion: string | null
  is_duplicate: boolean
  is_spam: boolean
  is_outlier: boolean
  flags: string[]
}

export interface CleaningReport {
  input_count: number
  removed_empty: number
  removed_duplicate: number
  removed_spam: number
  invalid_dates: number
  outliers?: number
  output_count: number
  steps: { step: string; detail: string }[]
}

export interface DescriptiveStats {
  count: number
  mean: number | null
  median: number | null
  mode: number | null
  min: number | null
  max: number | null
  std_dev: number | null
  variance: number | null
  q1: number | null
  q3: number | null
  range: number | null
  sum: number
}

export interface CorrelationPair {
  x: string
  y: string
  coefficient: number
  strength: string
  direction: string
}

export interface Analysis {
  analysis_id: string
  source_url: string
  platform: PlatformKey
  data_mode: 'live' | 'demo'
  status: string
  user_name: string | null
  created_at: string | null
  content: Record<string, unknown>
  provenance: Record<string, unknown>
  notes: string[]
  cleaning_report: CleaningReport
  available_fields: string[]
  unavailable_fields: string[]
  total_records: number
  removed_records: number
  analysis_seconds: number
  sentiment_summary: SentimentCounts
  sentiment_status: Record<string, unknown>
  sentiment_method: string | null
  sentiment_comparison: SentimentComparisonRow[]
  engagement: EngagementMetrics
  comment_engagement: Record<string, unknown>
  statistics: AnalysisStatistics
  trends: Record<string, unknown>
  charts: AnalysisCharts
  keywords: KeywordRow[]
  hashtags: HashtagRow[]
  insights: Insight[]
  limitations: string[]
  records: SocialRecord[]
  demo_notice?: string
}

export interface SentimentComparisonRow {
  comment_id: string | null
  text: string
  vader_compound: number | null
  textblob_polarity: number | null
  textblob_subjectivity: number | null
  sentiment: SentimentKey
}

export interface AnalysisStatistics {
  descriptive: Record<string, DescriptiveStats>
  correlations: {
    fields: string[]
    keys: string[]
    matrix: (number | null)[][]
    pairs: CorrelationPair[]
  }
  comment_length: {
    characters: DescriptiveStats
    words: DescriptiveStats
    histogram: { label: string; count: number }[]
  }
  hourly: { distribution: { hour: string; count: number }[]; peak_hour: string | null; available: boolean }
  sentiment_keywords: { sentiment: string; keywords: string[] }[]
}

export interface AnalysisCharts {
  engagement_bars: { categories: string[]; values: (number | null)[] }
  sentiment_donut: { name: string; key: SentimentKey; value: number }[]
  sentiment_scores: { categories: string[]; values: number[] }
  sentiment_timeline: {
    categories: string[]
    series: { name: string; data: number[] }[]
    available: boolean
  }
  likes_vs_sentiment: {
    id: string | null
    likes: number
    sentiment: number
    text: string
    sentiment_label: SentimentKey
  }[]
  comment_length_histogram: { label: string; count: number }[]
  hourly_activity: { hour: string; count: number }[]
  keyword_bars: { name: string; value: number }[]
  hashtag_bars: { name: string; value: number }[]
  word_cloud: { text: string; value: number }[]
  top_comments: {
    most_liked: TopComment[]
    most_positive: TopComment[]
    most_negative: TopComment[]
  }
  correlation_matrix: AnalysisStatistics['correlations']
}

export interface TopComment {
  comment_id: string | null
  text: string
  author_name: string | null
  like_count: number | null
  published_at: string | null
  sentiment: SentimentKey
  compound: number | null
}

export interface KeywordRow {
  word: string
  count: number
  tfidf: number
  document_frequency: number
}

export interface HashtagRow {
  hashtag: string
  count: number
  avg_sentiment: number
  sentiment: SentimentKey
}

export interface Insight {
  title: string
  text: string
  kind: string
}

export interface HistoryItem {
  analysis_id: string
  url: string
  platform: PlatformKey
  title: string | null
  author: string | null
  data_mode: 'live' | 'demo'
  status: string
  created_at: string | null
  total_records: number
  removed_records: number
  views: number | null
  likes: number | null
  comment_count: number | null
  shares: number | null
  engagement_rate: number | null
  positive_pct: number | null
  neutral_pct: number | null
  negative_pct: number | null
  avg_sentiment: number | null
  sentiment_method: string | null
  analysis_seconds: number
  user_name: string | null
}

export interface ProfileStats {
  user_name: string | null
  total_analyses: number
  total_records_analyzed: number
  total_comments_analyzed: number
  average_sentiment: number | null
  favorite_platform: string | null
  platform_breakdown: Record<string, number>
  last_analysis: HistoryItem | null
  first_analysis_at: string | null
}

export interface PlatformInfo {
  key: PlatformKey
  label: string
  configured: boolean
  credential_env_var: string
  url_examples: string[]
  limitations: string[]
}

export interface DetectResult {
  url: string
  platform: PlatformKey
  platform_label: string
  detected: boolean
  configured: boolean
  message: string
}

export interface CommentsPage {
  analysis_id: string
  total: number
  page: number
  page_size: number
  pages: number
  records: SocialRecord[]
}

export interface TimeSeriesPoint {
  period: string
  count: number
  positive: number
  neutral: number
  negative: number
  avg_sentiment: number
}

export interface Trends {
  daily: { granularity: string; available: boolean; points: TimeSeriesPoint[]; peak_period: string | null; peak_count: number }
  weekly: { granularity: string; available: boolean; points: TimeSeriesPoint[]; peak_period: string | null; peak_count: number }
  hourly_of_day: AnalysisStatistics['hourly']
}
