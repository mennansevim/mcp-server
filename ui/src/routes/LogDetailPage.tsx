import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getLogsConfig, getRunEvents } from '../lib/api'
import { usePolling } from '../lib/usePolling'
import type { LiveEvent, LiveRunSummary } from '../types/logs'

const DEFAULT_POLL_MS = 3000
const DEFAULT_LIMIT = 200

type GroupStatus = 'neutral' | 'running' | 'success' | 'error'
type GroupKind = 'header' | 'step' | 'result' | 'misc'

interface EventGroup {
  id: string
  kind: GroupKind
  title: string
  ts: string
  status: GroupStatus
  events: LiveEvent[]
}

const SEPARATOR_RE = /^[-=]{20,}$/

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString('tr-TR', { hour12: false })
}

function normalizeStep(step: string): string {
  const match = step.match(/^step_(\d+)/)
  if (!match) {
    return step
  }
  return `step_${match[1]}`
}

function stepTitle(step: string): string {
  const match = step.match(/^step_(\d+)$/)
  if (!match) {
    return step
  }
  return `Step ${match[1]}`
}

function inferStatus(event: LiveEvent, current: GroupStatus): GroupStatus {
  if (current === 'error') {
    return current
  }
  if (event.level === 'error' || event.message.includes('❌')) {
    return 'error'
  }
  if (event.message.includes('✅')) {
    return 'success'
  }
  if (current === 'success') {
    return current
  }
  return 'running'
}

function shouldSkip(event: LiveEvent): boolean {
  if (event.step === 'console_banner') {
    return true
  }
  const msg = event.message.trim()
  if (!msg || SEPARATOR_RE.test(msg)) {
    return true
  }
  return false
}

function groupEvents(events: LiveEvent[]): EventGroup[] {
  const groups: EventGroup[] = []
  const byId = new Map<string, EventGroup>()

  const getOrCreateGroup = (
    id: string,
    kind: GroupKind,
    title: string,
    ts: string,
    initialStatus: GroupStatus
  ): EventGroup => {
    const existing = byId.get(id)
    if (existing) {
      return existing
    }
    const created: EventGroup = {
      id,
      kind,
      title,
      ts,
      status: initialStatus,
      events: []
    }
    byId.set(id, created)
    groups.push(created)
    return created
  }

  for (const event of events) {
    if (shouldSkip(event)) {
      continue
    }

    if (event.step === 'console_header') {
      const group = getOrCreateGroup('header', 'header', 'PR Header', event.ts, 'neutral')
      group.events.push(event)
      group.ts = event.ts
      continue
    }

    if (event.step === 'summary' || event.step === 'error') {
      const group = getOrCreateGroup('result', 'result', 'Result', event.ts, 'running')
      group.events.push(event)
      group.ts = event.ts
      group.status = inferStatus(event, group.status)
      continue
    }

    if (event.step.startsWith('step_')) {
      const normalized = normalizeStep(event.step)
      const group = getOrCreateGroup(
        normalized,
        'step',
        stepTitle(normalized),
        event.ts,
        'running'
      )
      group.events.push(event)
      group.ts = event.ts
      group.status = inferStatus(event, group.status)
      continue
    }

    const group = getOrCreateGroup(`misc-${event.seq}`, 'misc', event.step, event.ts, 'running')
    group.events.push(event)
    group.ts = event.ts
    group.status = inferStatus(event, group.status)
  }

  return groups
}

export default function LogDetailPage() {
  const { runId } = useParams()
  const [run, setRun] = useState<LiveRunSummary | null>(null)
  const [events, setEvents] = useState<LiveEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pollMs, setPollMs] = useState(DEFAULT_POLL_MS)
  const [limit, setLimit] = useState(DEFAULT_LIMIT)
  const cursorRef = useRef(0)
  const groupedEvents = useMemo(() => groupEvents(events), [events])

  useEffect(() => {
    let mounted = true
    const loadConfig = async () => {
      try {
        const cfg = await getLogsConfig()
        if (!mounted) {
          return
        }
        setPollMs(Math.max(1000, cfg.poll_interval_seconds * 1000))
        setLimit(Math.max(20, cfg.max_events_per_poll))
      } catch {
        if (mounted) {
          setPollMs(DEFAULT_POLL_MS)
          setLimit(DEFAULT_LIMIT)
        }
      }
    }
    void loadConfig()
    return () => {
      mounted = false
    }
  }, [])

  const loadEvents = useCallback(async () => {
    if (!runId) {
      return
    }

    try {
      const data = await getRunEvents(runId, cursorRef.current, limit)
      setRun(data.run)
      if (data.events.length > 0) {
        setEvents((prev) => {
          const seen = new Set(prev.map((item) => item.seq))
          const fresh = data.events.filter((item) => !seen.has(item.seq))
          return fresh.length > 0 ? [...prev, ...fresh] : prev
        })
      }
      cursorRef.current = data.next_cursor
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    }
  }, [limit, runId])

  usePolling(loadEvents, pollMs, Boolean(runId))

  return (
    <main className="page">
      <header className="panel">
        <h1>Run Detail</h1>
        <p>
          <Link to="/logs">Back to dashboard</Link>
        </p>
        <p>
          <Link to="/config">Open config</Link>
        </p>
        <p>Run ID: {runId}</p>

        {run ? (
          <section className="run-summary">
            <strong>
              PR #{run.pr_id} - {run.title}
            </strong>
            <p>
              Status: {run.status}
              {run.score != null ? ` | Score: ${run.score}/10` : ''}
              {run.issues != null ? ` | Issues: ${run.issues}` : ''}
            </p>
          </section>
        ) : null}

        {error ? <p className="error-text">{error}</p> : null}

        <ul className="timeline">
          {groupedEvents.map((group) => (
            <li
              className={`timeline-event group-card status-${group.status}`}
              data-testid={`group-card-${group.id}`}
              key={group.id}
            >
              <div className="timeline-head">
                <strong>{group.title}</strong>
                <span>{formatTime(group.ts)}</span>
              </div>
              <ul className="group-lines">
                {group.events.map((event) => (
                  <li key={event.seq}>{event.message}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>

        {events.length === 0 && !error ? <p>Waiting for events...</p> : null}
      </header>
    </main>
  )
}
