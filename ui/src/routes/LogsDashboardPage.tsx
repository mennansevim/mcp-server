import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLogsConfig, getRuns } from '../lib/api'
import { usePolling } from '../lib/usePolling'
import type { LiveRunSummary, RunStatus } from '../types/logs'

const DEFAULT_POLL_MS = 3000

function StatusBadge({ status }: { status: RunStatus }) {
  const map: Record<RunStatus, { cls: string; label: string }> = {
    active: { cls: 'badge badge-active', label: 'Running' },
    completed: { cls: 'badge badge-completed', label: 'Done' },
    error: { cls: 'badge badge-error', label: 'Error' },
  }
  const { cls, label } = map[status] ?? map.active
  return <span className={cls}>{label}</span>
}

function RunCard({ run }: { run: LiveRunSummary }) {
  return (
    <Link to={`/logs/${run.run_id}`} className="run-card">
      <div className="run-card-header">
        <span className="run-card-pr">PR #{run.pr_id}</span>
        <StatusBadge status={run.status} />
      </div>
      <p className="run-card-title">{run.title || 'Untitled'}</p>
      <div className="run-card-info">
        <span className="run-card-chip">{run.platform.toUpperCase()}</span>
        <span className="run-card-chip">{run.author}</span>
        {run.source_branch && (
          <span className="run-card-branch">
            {run.source_branch} &rarr; {run.target_branch || 'main'}
          </span>
        )}
      </div>
      {(run.score !== null && run.score !== undefined) && (
        <div className="run-card-footer">
          <span className={`run-card-score ${run.score >= 7 ? 'score-good' : run.score >= 4 ? 'score-mid' : 'score-bad'}`}>
            Score: {run.score}/10
          </span>
          {run.issues != null && <span className="run-card-issues">{run.issues} issues</span>}
          {run.critical != null && run.critical > 0 && (
            <span className="run-card-critical">{run.critical} critical</span>
          )}
        </div>
      )}
    </Link>
  )
}

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
        if (mounted) setPollMs(Math.max(1000, cfg.poll_interval_seconds * 1000))
      } catch {
        if (mounted) setPollMs(DEFAULT_POLL_MS)
      }
    }
    void loadConfig()
    return () => { mounted = false }
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

  const activeCount = runs.filter(r => r.status === 'active').length
  const errorCount = runs.filter(r => r.status === 'error').length
  const doneCount = runs.filter(r => r.status === 'completed').length

  return (
    <>
      <div className="page-header">
        <div>
          <h1>PR Runs</h1>
          <p className="page-subtitle">Live review tracking &middot; polling every {Math.round(pollMs / 1000)}s</p>
        </div>
      </div>

      <div className="stat-grid stat-grid-sm">
        <div className="stat-card stat-card-accent-green">
          <p className="stat-value">{activeCount}</p>
          <p className="stat-label">Active</p>
        </div>
        <div className="stat-card stat-card-accent-blue">
          <p className="stat-value">{doneCount}</p>
          <p className="stat-label">Completed</p>
        </div>
        <div className="stat-card stat-card-accent-red">
          <p className="stat-value">{errorCount}</p>
          <p className="stat-label">Errors</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">{runs.length}</p>
          <p className="stat-label">Total</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <div className="empty-state">Loading runs...</div>}
      {!loading && runs.length === 0 && (
        <div className="empty-state">
          <p className="empty-icon">&#128269;</p>
          <p>No PR runs yet</p>
          <p className="empty-hint">Runs will appear here when a webhook triggers a code review.</p>
        </div>
      )}

      {runs.length > 0 && (
        <div className="run-grid">
          {runs.map((run) => (
            <RunCard key={run.run_id} run={run} />
          ))}
        </div>
      )}
    </>
  )
}
