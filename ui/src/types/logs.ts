export type RunStatus = 'active' | 'completed' | 'error'

export interface LiveRunSummary {
  run_id: string
  platform: string
  pr_id: string
  title: string
  author: string
  source_branch?: string | null
  target_branch?: string | null
  repo?: string | null
  started_at?: string
  updated_at?: string
  status: RunStatus
  score?: number | null
  issues?: number | null
  critical?: number | null
  error?: string | null
}

export interface LiveEvent {
  seq: number
  ts: string
  level: string
  step: string
  message: string
  meta: Record<string, unknown>
}

export interface LogsConfig {
  poll_interval_seconds: number
  max_events_per_poll: number
}

export interface ActiveRunsResponse {
  count: number
  runs: LiveRunSummary[]
}

export interface RunEventsResponse {
  run: LiveRunSummary
  events: LiveEvent[]
  next_cursor: number
}

export type ReviewTemplate = 'default' | 'detailed' | 'executive'

export interface EditableConfig {
  ui: {
    logs: {
      poll_interval_seconds: number
      max_events_per_poll: number
    }
  }
  review: {
    comment_strategy: 'summary' | 'inline' | 'both'
    template: ReviewTemplate
    focus: string[]
  }
  ai: {
    provider: 'openai' | 'anthropic' | 'groq'
    model: string
  }
}
