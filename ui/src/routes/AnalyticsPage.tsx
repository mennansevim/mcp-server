import { useCallback, useEffect, useState } from 'react'

interface Overview {
  total_reviews: number
  avg_score: number
  avg_security_score: number
  total_issues: number
  total_critical: number
  total_security_issues: number
  total_ai_slop: number
  blocked_merges: number
  secret_leaks: number
}

interface TrendPoint {
  ts: string
  score: number
  security_score: number
  pr_id: string
}

interface TopIssue {
  category: string
  count: number
}

interface SecurityBreakdown {
  owasp_distribution: Record<string, number>
  threat_types: Record<string, number>
  total_secret_leaks: number
  avg_security_score: number
}

interface AuthorStat {
  author: string
  reviews: number
  avg_score: number
  total_issues: number
  blocked: number
}

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<T>
}

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="stat-card">
      <p className="stat-value" style={color ? { color } : undefined}>{value}</p>
      <p className="stat-label">{label}</p>
      {sub ? <p className="stat-sub">{sub}</p> : null}
    </div>
  )
}

function ScoreBar({ value, max = 10 }: { value: number; max?: number }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  const color = value >= 8 ? '#16a34a' : value >= 6 ? '#ca8a04' : value >= 4 ? '#ea580c' : '#dc2626'
  return (
    <div className="score-bar-bg">
      <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [topIssues, setTopIssues] = useState<TopIssue[]>([])
  const [security, setSecurity] = useState<SecurityBreakdown | null>(null)
  const [authors, setAuthors] = useState<AuthorStat[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [ov, tr, ti, sec, au] = await Promise.all([
        fetchJson<Overview>('/api/analytics/overview'),
        fetchJson<{ trend: TrendPoint[] }>('/api/analytics/trend'),
        fetchJson<{ top_issues: TopIssue[] }>('/api/analytics/top-issues'),
        fetchJson<SecurityBreakdown>('/api/analytics/security'),
        fetchJson<{ authors: AuthorStat[] }>('/api/analytics/authors'),
      ])
      setOverview(ov)
      setTrend(tr.trend)
      setTopIssues(ti.top_issues)
      setSecurity(sec)
      setAuthors(au.authors)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    }
  }, [])

  useEffect(() => { void load() }, [load])

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Review Analytics</h1>
          <p className="page-subtitle">Aggregated insights from all code reviews.</p>
        </div>
      </div>

        {error ? <div className="alert alert-error">{error}</div> : null}

        {overview ? (
          <section className="stat-grid">
            <StatCard label="Total Reviews" value={overview.total_reviews} />
            <StatCard label="Avg Score" value={`${overview.avg_score}/10`} color={overview.avg_score >= 7 ? '#16a34a' : '#ea580c'} />
            <StatCard label="Avg Security" value={`${overview.avg_security_score}/10`} color={overview.avg_security_score >= 7 ? '#16a34a' : '#dc2626'} />
            <StatCard label="Total Issues" value={overview.total_issues} />
            <StatCard label="Critical" value={overview.total_critical} color="#dc2626" />
            <StatCard label="Security Issues" value={overview.total_security_issues} color="#b91c1c" />
            <StatCard label="AI Slop" value={overview.total_ai_slop} color="#ea580c" />
            <StatCard label="Blocked Merges" value={overview.blocked_merges} color="#dc2626" />
            <StatCard label="Secret Leaks" value={overview.secret_leaks} color={overview.secret_leaks > 0 ? '#dc2626' : '#16a34a'} />
          </section>
        ) : null}

        {trend.length > 0 ? (
          <section className="analytics-section">
            <h2>Score Trend</h2>
            <div className="trend-list">
              {trend.map((p, i) => (
                <div key={i} className="trend-row">
                  <span className="trend-pr">PR #{p.pr_id}</span>
                  <span className="trend-scores">
                    Q: {p.score}/10 &nbsp; S: {p.security_score}/10
                  </span>
                  <ScoreBar value={p.score} />
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {security ? (
          <section className="analytics-section">
            <h2>🔒 Security Breakdown</h2>
            <p>Avg Security Score: <strong>{security.avg_security_score}/10</strong> &nbsp; Secret Leaks: <strong>{security.total_secret_leaks}</strong></p>
            {Object.keys(security.owasp_distribution).length > 0 ? (
              <>
                <h3>OWASP Categories Hit</h3>
                <div className="bar-chart">
                  {Object.entries(security.owasp_distribution)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cat, count]) => (
                      <div key={cat} className="bar-row">
                        <span className="bar-label">{cat}</span>
                        <div className="bar-bg"><div className="bar-fill bar-red" style={{ width: `${Math.min(100, count * 20)}%` }} /></div>
                        <span className="bar-count">{count}</span>
                      </div>
                    ))}
                </div>
              </>
            ) : null}
            {Object.keys(security.threat_types).length > 0 ? (
              <>
                <h3>Threat Types</h3>
                <div className="bar-chart">
                  {Object.entries(security.threat_types)
                    .sort(([, a], [, b]) => b - a)
                    .map(([type, count]) => (
                      <div key={type} className="bar-row">
                        <span className="bar-label">{type}</span>
                        <div className="bar-bg"><div className="bar-fill bar-orange" style={{ width: `${Math.min(100, count * 15)}%` }} /></div>
                        <span className="bar-count">{count}</span>
                      </div>
                    ))}
                </div>
              </>
            ) : null}
          </section>
        ) : null}

        {topIssues.length > 0 ? (
          <section className="analytics-section">
            <h2>Top Issue Categories</h2>
            <div className="bar-chart">
              {topIssues.map((item) => (
                <div key={item.category} className="bar-row">
                  <span className="bar-label">{item.category}</span>
                  <div className="bar-bg"><div className="bar-fill bar-blue" style={{ width: `${Math.min(100, item.count * 10)}%` }} /></div>
                  <span className="bar-count">{item.count}</span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {authors.length > 0 ? (
          <section className="analytics-section">
            <h2>Author Stats</h2>
            <table className="analytics-table">
              <thead>
                <tr><th>Author</th><th>Reviews</th><th>Avg Score</th><th>Issues</th><th>Blocked</th></tr>
              </thead>
              <tbody>
                {authors.map((a) => (
                  <tr key={a.author}>
                    <td><strong>{a.author}</strong></td>
                    <td>{a.reviews}</td>
                    <td>{a.avg_score}/10</td>
                    <td>{a.total_issues}</td>
                    <td style={a.blocked > 0 ? { color: '#dc2626', fontWeight: 700 } : undefined}>{a.blocked}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ) : null}

        {!overview && !error ? <div className="empty-state">Loading analytics...</div> : null}
        {overview && overview.total_reviews === 0 ? (
          <div className="empty-state">
            <p className="empty-icon">&#128200;</p>
            <p>No review data yet</p>
            <p className="empty-hint">Analytics will populate after the first PR review.</p>
          </div>
        ) : null}
    </>
  )
}
