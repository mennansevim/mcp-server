import { Link } from 'react-router-dom'
import type { LiveRunSummary } from '../types/logs'

interface ActiveRunRowProps {
  run: LiveRunSummary
}

export default function ActiveRunRow({ run }: ActiveRunRowProps) {
  const dotClass =
    run.status === 'active'
      ? 'dot-active'
      : run.status === 'error'
        ? 'dot-error'
        : 'dot-completed'

  return (
    <li className="run-row">
      <span
        aria-label={run.status}
        className={dotClass}
        data-testid={`status-dot-${run.run_id}`}
      />
      <div className="run-main">
        <Link className="run-link" to={`/logs/${run.run_id}`}>
          PR #{run.pr_id}
        </Link>
        <p className="run-title">{run.title}</p>
      </div>
      <div className="run-meta">
        <span>{run.platform.toUpperCase()}</span>
        <span>{run.author}</span>
        <span>{run.status.toUpperCase()}</span>
        <span>
          {(run.source_branch || '-') + ' -> ' + (run.target_branch || '-')}
        </span>
      </div>
    </li>
  )
}
