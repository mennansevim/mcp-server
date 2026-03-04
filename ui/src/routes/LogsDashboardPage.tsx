import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ActiveRunRow from '../components/ActiveRunRow'
import { getLogsConfig, getRuns } from '../lib/api'
import { usePolling } from '../lib/usePolling'
import type { LiveRunSummary } from '../types/logs'

const DEFAULT_POLL_MS = 3000

export default function LogsDashboardPage() {
  const [runs, setRuns] = useState<LiveRunSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pollMs, setPollMs] = useState(DEFAULT_POLL_MS)

  useEffect(() => {
    let mounted = true
    const loadConfig = async () => {
      try {
        const cfg = await getLogsConfig()
        if (mounted) {
          setPollMs(Math.max(1000, cfg.poll_interval_seconds * 1000))
        }
      } catch {
        if (mounted) {
          setPollMs(DEFAULT_POLL_MS)
        }
      }
    }

    void loadConfig()
    return () => {
      mounted = false
    }
  }, [])

  const loadRuns = useCallback(async () => {
    try {
      const data = await getRuns()
      setRuns(data.runs)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load runs')
    } finally {
      setLoading(false)
    }
  }, [])

  usePolling(loadRuns, pollMs, true)

  return (
    <main className="page">
      <header className="panel">
        <h1>PR Runs</h1>
        <p>Polling every {Math.round(pollMs / 1000)}s</p>
        <p>
          <Link to="/config">Open config</Link>
        </p>

        {error ? <p className="error-text">{error}</p> : null}

        {loading ? <p>Loading runs...</p> : null}

        {!loading && runs.length === 0 ? <p>No runs right now.</p> : null}

        {runs.length > 0 ? (
          <ul className="run-list">
            {runs.map((run) => (
              <ActiveRunRow key={run.run_id} run={run} />
            ))}
          </ul>
        ) : null}
      </header>
    </main>
  )
}
