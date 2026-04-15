import { useCallback, useEffect, useRef, useState } from 'react'

const BASE = import.meta.env.VITE_API_BASE ?? ''

interface FileResult {
  file: string
  language?: string
  score?: number
  total_issues?: number
  truncated?: boolean
  review_time_sec?: number
  skipped?: boolean
  reason?: string
  error?: string
  issues?: Issue[]
}

interface Issue {
  severity: string
  title: string
  description: string
  category: string
  suggestion?: string
}

interface Summary {
  total_files: number
  reviewed: number
  skipped: number
  errors: number
  avg_score: number
  total_issues: number
  critical: number
  high: number
  medium: number
  low: number
}

interface ReviewData {
  id: string
  filename: string
  status: string
  status_message: string | null
  total_files: number
  reviewed_count: number
  current_file: string | null
  current_file_started_at: number | null
  started_at: number | null
  results: FileResult[]
  summary: Summary | null
  plan?: PlanFile[]
}

interface PlanFile {
  file: string
  language: string
  size: number
  category: string
}

type Phase = 'upload' | 'plan' | 'reviewing' | 'done'

const PROVIDERS = [
  { value: '', label: 'Varsayılan (Server Config)' },
  { value: 'groq', label: 'Groq — Llama 3.3 70B (Hızlı)' },
  { value: 'openai', label: 'OpenAI — GPT-4o' },
  { value: 'anthropic', label: 'Anthropic — Claude 3.5 Sonnet' },
]

const FOCUS_OPTIONS = [
  { value: 'security', label: 'Security' },
  { value: 'bugs', label: 'Bugs' },
  { value: 'performance', label: 'Performance' },
  { value: 'compilation', label: 'Compilation' },
  { value: 'code_quality', label: 'Code Quality' },
]

function sevColor(s: string) {
  switch (s) {
    case 'critical': return '#ef4444'
    case 'high': return '#f97316'
    case 'medium': return '#eab308'
    case 'low': return '#3b82f6'
    default: return '#6b7280'
  }
}

function scoreColor(s: number) {
  if (s >= 8) return '#22c55e'
  if (s >= 5) return '#eab308'
  return '#ef4444'
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="stat-card">
      <p className="stat-value" style={color ? { color } : undefined}>{value}</p>
      <p className="stat-label">{label}</p>
    </div>
  )
}

const selectStyle: React.CSSProperties = {
  padding: '8px 12px',
  borderRadius: 6,
  border: '1px solid #333',
  background: '#1a1a24',
  color: '#ccc',
  fontSize: 13,
  width: '100%',
}

const btnPrimary: React.CSSProperties = {
  padding: '10px 28px',
  borderRadius: 8,
  background: '#6366f1',
  color: '#fff',
  border: 'none',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 600,
}

const btnDanger: React.CSSProperties = {
  padding: '10px 28px',
  borderRadius: 8,
  background: '#dc2626',
  color: '#fff',
  border: 'none',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 600,
}

const btnOutline: React.CSSProperties = {
  padding: '8px 20px',
  borderRadius: 6,
  border: '1px solid #444',
  background: 'transparent',
  color: '#ccc',
  cursor: 'pointer',
  fontSize: 13,
}

export default function ProjectReviewPage() {
  const [phase, setPhase] = useState<Phase>('upload')
  const [reviewId, setReviewId] = useState<string | null>(null)
  const [review, setReview] = useState<ReviewData | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedFile, setExpandedFile] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [plan, setPlan] = useState<PlanFile[] | null>(null)
  const [ignoredByReviewignore, setIgnoredByReviewignore] = useState(0)
  const [provider, setProvider] = useState('')
  const [focusAreas, setFocusAreas] = useState(['security', 'bugs', 'performance', 'compilation'])
  const [excludeCategories, setExcludeCategories] = useState<Set<string>>(new Set(['auto_generated', 'config']))
  const [tick, setTick] = useState(0)
  const fileRef = useRef<HTMLInputElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startedLocalRef = useRef<number | null>(null)

  const pollReview = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${BASE}/api/project-review/${id}`)
      if (!res.ok) return
      const data: ReviewData = await res.json()
      setReview(data)
      if (data.status === 'done' || data.status === 'failed') {
        setPhase('done')
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
        if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null }
      } else if (data.status === 'cancelled') {
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
        if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null }
      }
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      if (tickRef.current) clearInterval(tickRef.current)
    }
  }, [])

  const handleFileSelect = () => {
    const input = fileRef.current
    if (!input?.files?.length) return
    const file = input.files[0]
    if (!file.name.endsWith('.zip')) {
      setError('Sadece .zip dosyaları kabul edilir.')
      return
    }
    setSelectedFile(file)
    setError(null)
    fetchPlan(file)
  }

  const fetchPlan = async (file: File) => {
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${BASE}/api/project-review/plan`, { method: 'POST', body: form })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setPlan(data.files)
      setIgnoredByReviewignore(data.ignored_by_reviewignore || 0)
      setPhase('plan')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const startReview = async () => {
    if (!selectedFile) return
    setPhase('reviewing')
    setError(null)
    startedLocalRef.current = Date.now()

    const form = new FormData()
    form.append('file', selectedFile)
    form.append('focus', focusAreas.join(','))
    if (provider) form.append('provider', provider)
    form.append('exclude_categories', Array.from(excludeCategories).join(','))

    try {
      const res = await fetch(`${BASE}/api/project-review/upload`, { method: 'POST', body: form })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || `HTTP ${res.status}`)
      }
      const { review_id } = await res.json()
      setReviewId(review_id)
      pollReview(review_id)
      pollRef.current = setInterval(() => pollReview(review_id), 2000)
      tickRef.current = setInterval(() => setTick(t => t + 1), 1000)
    } catch (e: any) {
      setError(e.message)
      setPhase('plan')
    }
  }

  const cancelReview = async () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null }
    if (reviewId) {
      await fetch(`${BASE}/api/project-review/${reviewId}/cancel`, { method: 'POST' }).catch(() => {})
    }
    handleReset()
  }

  const handleReset = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null }
    setPhase('upload')
    setReviewId(null)
    setReview(null)
    setPlan(null)
    setSelectedFile(null)
    setError(null)
    setExpandedFile(null)
    startedLocalRef.current = null
    if (fileRef.current) fileRef.current.value = ''
  }

  const toggleFocus = (val: string) => {
    setFocusAreas(prev => prev.includes(val) ? prev.filter(f => f !== val) : [...prev, val])
  }

  const pct = review && review.total_files > 0
    ? Math.round((review.reviewed_count / review.total_files) * 100)
    : 0

  const filteredPlan = plan?.filter(f => !excludeCategories.has(f.category)) ?? []
  const langCounts = filteredPlan.reduce<Record<string, number>>((acc, f) => {
    acc[f.language] = (acc[f.language] || 0) + 1
    return acc
  }, {})

  const categoryCounts = plan?.reduce<Record<string, number>>((acc, f) => {
    acc[f.category] = (acc[f.category] || 0) + 1
    return acc
  }, {}) ?? {}

  const CATEGORY_LABELS: Record<string, string> = {
    source: '📝 Kaynak Kod',
    test: '🧪 Test Dosyaları',
    auto_generated: '🤖 Otomatik Üretilen',
    boilerplate: '📄 Boilerplate',
    config: '⚙️ Konfigürasyon',
  }

  const toggleCategory = (cat: string) => {
    setExcludeCategories(prev => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h2 style={{ marginBottom: 8, color: '#e0e0e0' }}>Project Review</h2>
      <p style={{ color: '#999', marginBottom: 24, fontSize: 14 }}>
        ZIP olarak proje yükleyin — önce plan görün, sonra AI ile review başlatın.
      </p>

      {/* ─── PHASE: UPLOAD ─── */}
      {phase === 'upload' && (
        <div style={{
          border: '2px dashed var(--clr-border, #333)',
          borderRadius: 12,
          padding: 40,
          textAlign: 'center',
          background: 'var(--clr-surface, #111)',
        }}>
          <input ref={fileRef} type="file" accept=".zip" style={{ display: 'none' }} onChange={handleFileSelect} />
          <p style={{ fontSize: 40, marginBottom: 12 }}>📦</p>
          <p style={{ marginBottom: 16, fontSize: 15, color: '#ccc' }}>Projenizi .zip olarak yükleyin</p>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            style={{ ...btnPrimary, background: uploading ? '#555' : '#6366f1', cursor: uploading ? 'wait' : 'pointer' }}
          >
            {uploading ? 'Analiz ediliyor...' : 'ZIP Dosyası Seç'}
          </button>
          {error && <p style={{ color: '#ef4444', marginTop: 12 }}>{error}</p>}
        </div>
      )}

      {/* ─── PHASE: PLAN ─── */}
      {phase === 'plan' && plan && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{
            border: '1px solid var(--clr-border, #333)',
            borderRadius: 12,
            padding: 24,
            background: 'var(--clr-surface, #111)',
          }}>
            <h3 style={{ marginBottom: 16, color: '#e0e0e0' }}>📋 Review Planı — {selectedFile?.name}</h3>

            {ignoredByReviewignore > 0 && (
              <div style={{
                background: 'rgba(251,191,36,0.08)',
                border: '1px solid rgba(251,191,36,0.25)',
                borderRadius: 8,
                padding: '10px 14px',
                marginBottom: 16,
                fontSize: 13,
                color: '#fbbf24',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}>
                <span style={{ fontSize: 16 }}>🚫</span>
                <span>
                  <strong>.reviewignore</strong> kurallarına göre <strong>{ignoredByReviewignore}</strong> dosya otomatik olarak elendi
                  (Migrations, obj, bin, config, vb.)
                </span>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12, marginBottom: 20 }}>
              <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '14px 16px', textAlign: 'center' }}>
                <p style={{ fontSize: 24, fontWeight: 700, color: '#4ade80', margin: 0 }}>{filteredPlan.length}</p>
                <p style={{ fontSize: 11, color: '#888', margin: '4px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>Review Edilecek</p>
              </div>
              <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '14px 16px', textAlign: 'center' }}>
                <p style={{ fontSize: 24, fontWeight: 700, color: '#f87171', margin: 0 }}>{(plan?.length ?? 0) - filteredPlan.length}</p>
                <p style={{ fontSize: 11, color: '#888', margin: '4px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>Kategori Elenen</p>
              </div>
              <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '14px 16px', textAlign: 'center' }}>
                <p style={{ fontSize: 24, fontWeight: 700, color: '#fbbf24', margin: 0 }}>{ignoredByReviewignore}</p>
                <p style={{ fontSize: 11, color: '#888', margin: '4px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>.reviewignore</p>
              </div>
              <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '14px 16px', textAlign: 'center' }}>
                <p style={{ fontSize: 24, fontWeight: 700, color: '#e0e0e0', margin: 0 }}>{Object.keys(langCounts).length}</p>
                <p style={{ fontSize: 11, color: '#888', margin: '4px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>Dil Sayısı</p>
              </div>
              <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '14px 16px', textAlign: 'center' }}>
                <p style={{ fontSize: 24, fontWeight: 700, color: '#e0e0e0', margin: 0 }}>{Math.round(filteredPlan.reduce((s, f) => s + f.size, 0) / 1024)} KB</p>
                <p style={{ fontSize: 11, color: '#888', margin: '4px 0 0', textTransform: 'uppercase', letterSpacing: 1 }}>Toplam Boyut</p>
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 10, color: '#bbb' }}>📂 Dosya Kategorileri</p>
              <p style={{ fontSize: 11, color: '#777', marginBottom: 10 }}>
                Otomatik üretilen, konfigürasyon ve boilerplate dosyalar varsayılan olarak elenmiştir. Toggle ile dahil edebilirsiniz.
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {Object.entries(categoryCounts).sort((a, b) => b[1] - a[1]).map(([cat, count]) => {
                  const isExcluded = excludeCategories.has(cat)
                  return (
                    <button
                      key={cat}
                      onClick={() => toggleCategory(cat)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: 8,
                        border: `1px solid ${isExcluded ? '#444' : '#4ade80'}`,
                        background: isExcluded ? 'rgba(100,100,100,0.1)' : 'rgba(74,222,128,0.1)',
                        color: isExcluded ? '#666' : '#4ade80',
                        cursor: 'pointer',
                        fontSize: 13,
                        textDecoration: isExcluded ? 'line-through' : 'none',
                        transition: 'all 0.2s',
                      }}
                    >
                      {CATEGORY_LABELS[cat] || cat} <strong>({count})</strong>
                    </button>
                  )
                })}
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#bbb' }}>Dil Dağılımı</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {Object.entries(langCounts).sort((a, b) => b[1] - a[1]).map(([lang, count]) => (
                  <span key={lang} style={{
                    fontSize: 12,
                    padding: '4px 10px',
                    borderRadius: 6,
                    background: '#252538',
                    border: '1px solid #3a3a50',
                    color: '#ccc',
                  }}>
                    {lang} <strong style={{ color: '#818cf8' }}>{count}</strong>
                  </span>
                ))}
              </div>
            </div>

            <details style={{ marginBottom: 4 }}>
              <summary style={{ cursor: 'pointer', fontSize: 13, color: '#aaa', marginBottom: 8 }}>
                Review edilecek dosyalar ({filteredPlan.length})
              </summary>
              <div style={{ maxHeight: 200, overflow: 'auto', fontSize: 12, color: '#999' }}>
                {filteredPlan.map(f => (
                  <div key={f.file} style={{ padding: '3px 0', borderBottom: '1px solid #222' }}>
                    <span style={{ color: '#4ade80', marginRight: 6 }}>●</span>
                    {f.file} <span style={{ color: '#666' }}>({f.language}, {Math.round(f.size / 1024)}KB)</span>
                  </div>
                ))}
              </div>
            </details>
            {plan.length - filteredPlan.length > 0 && (
              <details style={{ marginTop: 8 }}>
                <summary style={{ cursor: 'pointer', fontSize: 13, color: '#666', marginBottom: 8 }}>
                  Elenen dosyalar ({plan.length - filteredPlan.length})
                </summary>
                <div style={{ maxHeight: 200, overflow: 'auto', fontSize: 12, color: '#666' }}>
                  {plan.filter(f => excludeCategories.has(f.category)).map(f => (
                    <div key={f.file} style={{ padding: '3px 0', borderBottom: '1px solid #1a1a1a' }}>
                      <span style={{ color: '#f87171', marginRight: 6 }}>✕</span>
                      {f.file} <span style={{ color: '#555' }}>({CATEGORY_LABELS[f.category] || f.category})</span>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>

          <div style={{
            border: '1px solid var(--clr-border, #333)',
            borderRadius: 12,
            padding: 24,
            background: 'var(--clr-surface, #111)',
          }}>
            <h3 style={{ marginBottom: 16, color: '#e0e0e0' }}>⚙️ Review Ayarları</h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div>
                <label style={{ fontSize: 12, color: '#aaa', display: 'block', marginBottom: 6 }}>AI Provider</label>
                <select value={provider} onChange={e => setProvider(e.target.value)} style={selectStyle}>
                  {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 12, color: '#aaa', display: 'block', marginBottom: 6 }}>Tahmini Süre</label>
                <p style={{ fontSize: 22, fontWeight: 700, color: '#818cf8', marginTop: 4 }}>
                  ~{Math.ceil(filteredPlan.length * (provider === 'groq' || !provider ? 10 : 25))}s
                </p>
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 12, color: '#aaa', display: 'block', marginBottom: 8 }}>Focus Alanları</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {FOCUS_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => toggleFocus(opt.value)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: 6,
                      border: `1px solid ${focusAreas.includes(opt.value) ? '#6366f1' : '#333'}`,
                      background: focusAreas.includes(opt.value) ? 'rgba(99,102,241,0.15)' : 'transparent',
                      color: focusAreas.includes(opt.value) ? '#818cf8' : '#888',
                      cursor: 'pointer',
                      fontSize: 13,
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={startReview} style={btnPrimary} disabled={focusAreas.length === 0 || filteredPlan.length === 0}>
                Review Başlat ({filteredPlan.length} dosya)
              </button>
              <button onClick={handleReset} style={btnOutline}>
                İptal
              </button>
            </div>
            {error && <p style={{ color: '#ef4444', marginTop: 12 }}>{error}</p>}
          </div>
        </div>
      )}

      {/* ─── PHASE: REVIEWING ─── */}
      {phase === 'reviewing' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <style>{`
            @keyframes spin { to { transform: rotate(360deg) } }
            @keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.4 } }
          `}</style>

          {/* Header + progress */}
          <div style={{
            border: '1px solid var(--clr-border, #333)',
            borderRadius: 12,
            padding: 24,
            background: 'var(--clr-surface, #111)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: 15 }}>
                  {review ? 'Review devam ediyor' : 'Review başlatılıyor...'}
                </span>
                {review && (
                  <span style={{ color: '#888', fontSize: 13, marginLeft: 12 }}>
                    {review.filename}
                  </span>
                )}
              </div>
              <button onClick={cancelReview} style={btnDanger}>
                İptal Et
              </button>
            </div>

            {(() => {
              void tick
              const elapsed = review?.started_at ? Math.round(Date.now() / 1000 - review.started_at) : (startedLocalRef.current ? Math.round((Date.now() - startedLocalRef.current) / 1000) : 0)
              const mins = Math.floor(elapsed / 60)
              const secs = elapsed % 60
              const timeStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`

              const isPreReview = !review || review.status === 'extracting' || review.status === 'scanning'
              const statusMsg = review?.status_message ?? 'Başlatılıyor...'

              if (isPreReview) {
                const steps = [
                  { key: 'upload', label: 'ZIP yüklendi', done: true },
                  { key: 'extract', label: 'Dosyalar açılıyor', done: review?.status !== 'extracting' && !!review },
                  { key: 'scan', label: 'Dosyalar taranıyor', done: review?.status === 'reviewing' },
                  { key: 'review', label: 'AI Review başlıyor', done: false },
                ]
                const activeIdx = steps.findIndex(s => !s.done)
                return (
                  <div>
                    <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                      {steps.map((s, i) => (
                        <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{
                            width: 20, height: 20, borderRadius: '50%',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 11, fontWeight: 700,
                            ...(s.done
                              ? { background: '#22c55e', color: '#000' }
                              : i === activeIdx
                                ? { border: '2px solid #6366f1', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite' }
                                : { border: '2px solid #333', color: '#555' }),
                          }}>
                            {s.done ? '✓' : ''}
                          </div>
                          <span style={{ fontSize: 12, color: s.done ? '#22c55e' : i === activeIdx ? '#ccc' : '#555' }}>
                            {s.label}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#aaa', fontSize: 13 }}>{statusMsg}</span>
                      <span style={{ color: '#6366f1', fontSize: 13, fontFamily: 'monospace' }}>{timeStr}</span>
                    </div>
                  </div>
                )
              }

              const done = review!.results.filter(r => !r.skipped && !r.error)
              const scores = done.map(r => r.score ?? 0)
              const avgNow = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '-'
              const issuesNow = done.reduce((s, r) => s + (r.total_issues ?? 0), 0)

              return (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                    <span style={{ color: '#aaa' }}>
                      {review!.reviewed_count} / {review!.total_files} dosya tamamlandı
                    </span>
                    <span style={{ color: '#6366f1', fontWeight: 600 }}>{pct}%</span>
                  </div>
                  <div style={{ height: 6, borderRadius: 3, background: '#222', overflow: 'hidden', marginBottom: 16 }}>
                    <div style={{
                      height: '100%',
                      width: `${pct}%`,
                      background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                      borderRadius: 3,
                      transition: 'width 0.3s ease',
                    }} />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, fontSize: 12 }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#6366f1', fontFamily: 'monospace' }}>{timeStr}</div>
                      <div style={{ color: '#666' }}>Geçen Süre</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: scores.length ? scoreColor(Number(avgNow)) : '#666' }}>{avgNow}</div>
                      <div style={{ color: '#666' }}>Ort. Score</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#ccc' }}>{issuesNow}</div>
                      <div style={{ color: '#666' }}>Issue</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: review!.results.filter(r => r.error).length > 0 ? '#ef4444' : '#ccc' }}>{review!.results.filter(r => r.error).length}</div>
                      <div style={{ color: '#666' }}>Hata</div>
                    </div>
                  </div>
                </>
              )
            })()}
          </div>

          {/* Live process log */}
          {review && (
            <div style={{
              border: '1px solid var(--clr-border, #333)',
              borderRadius: 12,
              background: 'var(--clr-surface, #111)',
              overflow: 'hidden',
            }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Process Akışı</span>
                <span style={{ fontSize: 11, color: '#666' }}>
                  {review.results.length} tamamlandı
                  {review.results.filter(r => r.skipped).length > 0 && ` / ${review.results.filter(r => r.skipped).length} atlandı`}
                </span>
              </div>

              <div style={{ maxHeight: 340, overflowY: 'auto', fontSize: 12 }}>
                {/* Current file being processed */}
                {review.current_file && (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '24px 1fr 70px 60px',
                    alignItems: 'center',
                    padding: '10px 16px',
                    background: 'rgba(99,102,241,0.08)',
                    borderBottom: '1px solid #1a1a2e',
                  }}>
                    <div style={{
                      width: 14, height: 14, borderRadius: '50%',
                      border: '2px solid #6366f1', borderTopColor: 'transparent',
                      animation: 'spin 0.8s linear infinite',
                    }} />
                    <span style={{ color: '#e0e0e0', fontWeight: 500 }}>
                      {review.current_file}
                    </span>
                    <span style={{ color: '#6366f1', fontSize: 11, textAlign: 'center' }}>
                      {(() => {
                        if (!review.current_file_started_at) return 'processing...'
                        const elapsed = Math.round(Date.now() / 1000 - review.current_file_started_at)
                        const stuck = elapsed > 30
                        return (
                          <span style={{ color: stuck ? '#ef4444' : '#6366f1', animation: stuck ? 'pulse 1s infinite' : undefined }}>
                            {elapsed}s {stuck ? '(yavaş!)' : ''}
                          </span>
                        )
                      })()}
                    </span>
                    <span style={{ color: '#555', textAlign: 'center', fontSize: 11 }}>
                      {review.reviewed_count + 1}/{review.total_files}
                    </span>
                  </div>
                )}

                {/* Completed files (newest first) */}
                {[...review.results].reverse().map((r) => (
                  <div
                    key={r.file}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '24px 1fr 70px 60px',
                      alignItems: 'center',
                      padding: '8px 16px',
                      borderBottom: '1px solid #1a1a1a',
                    }}
                  >
                    <span style={{ fontSize: 14 }}>
                      {r.error ? '❌' : r.skipped ? '⏭️' : (r.score ?? 0) >= 8 ? '🟢' : (r.score ?? 0) >= 5 ? '🟡' : '🔴'}
                    </span>
                    <span style={{ color: r.error ? '#ef4444' : r.skipped ? '#666' : '#ccc' }}>
                      {r.file}
                      {r.skipped && <span style={{ color: '#555', marginLeft: 6 }}>({r.reason})</span>}
                    </span>
                    <span style={{
                      textAlign: 'center',
                      fontWeight: 600,
                      fontSize: 11,
                      color: r.error ? '#ef4444' : r.skipped ? '#444' : scoreColor(r.score ?? 0),
                    }}>
                      {r.error ? 'HATA' : r.skipped ? '-' : `${r.score}/10`}
                    </span>
                    <span style={{ textAlign: 'center', color: '#555', fontSize: 11 }}>
                      {r.review_time_sec ? `${r.review_time_sec}s` : '-'}
                    </span>
                  </div>
                ))}

                {review.results.length === 0 && !review.current_file && (
                  <div style={{ padding: 20, textAlign: 'center', color: '#555' }}>
                    İlk dosya bekleniyor...
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── PHASE: DONE — Executive Report ─── */}
      {phase === 'done' && review?.status === 'failed' && (
        <div style={{
          border: '1px solid #dc2626',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(220,38,38,0.08)',
          marginBottom: 20,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ color: '#ef4444', margin: 0 }}>Review Başarısız</h3>
            <button onClick={handleReset} style={btnOutline}>Yeni Review</button>
          </div>
          <p style={{ color: '#ccc', fontSize: 14, margin: '0 0 12px', lineHeight: 1.6 }}>
            {review.status_message || 'AI review sırasında çok fazla hata oluştu. Review güvenilir değil.'}
          </p>
          <div style={{ display: 'flex', gap: 12, fontSize: 13 }}>
            <span style={{ color: '#22c55e' }}>Başarılı: {review.summary?.reviewed ?? 0}</span>
            <span style={{ color: '#ef4444' }}>Hatalı: {review.summary?.errors ?? 0}</span>
            <span style={{ color: '#888' }}>Atlandı: {review.summary?.skipped ?? 0}</span>
          </div>
          {review.summary && review.summary.reviewed > 0 && (
            <p style={{ color: '#aaa', fontSize: 13, marginTop: 12 }}>
              Aşağıda sadece başarıyla review edilen dosyaların sonuçları gösterilmektedir. Rapor eksik olabilir.
            </p>
          )}
        </div>
      )}
      {phase === 'done' && review?.summary && (() => {
        const s = review.summary
        const reviewed = review.results.filter(r => !r.skipped && !r.error)
        const riskLevel = s.critical > 0 ? 'HIGH' : s.high > 0 ? 'MEDIUM' : s.medium > 0 ? 'LOW' : 'NONE'
        const riskColor = s.critical > 0 ? '#ef4444' : s.high > 0 ? '#f97316' : s.medium > 0 ? '#eab308' : '#22c55e'
        const debtHours = (s.critical * 2 + s.high * 1 + s.medium * 0.5 + s.low * 0.15).toFixed(1)
        const scoreClr = scoreColor(s.avg_score)
        const secIssues = review.results.flatMap(r => (r.issues ?? []).filter(i => ['security', 'injection', 'broken_auth', 'sensitive_data', 'xss', 'secret_leak'].includes(i.category?.toLowerCase())))
        const secScore = secIssues.length === 0 ? 10 : Math.max(0, 10 - secIssues.length * 2)
        const secColor = secScore <= 4 ? '#ef4444' : secScore <= 7 ? '#f97316' : '#22c55e'
        const allIssues = review.results.flatMap(r => (r.issues ?? []).map(iss => ({ ...iss, _file: r.file })))
        const filesWithIssues = review.results.filter(r => !r.skipped && !r.error && (r.total_issues ?? 0) > 0).sort((a, b) => (a.score ?? 10) - (b.score ?? 10))

        const badgeStyle = (bg: string): React.CSSProperties => ({
          display: 'inline-flex', alignItems: 'center', gap: 4,
          padding: '3px 10px', borderRadius: 4, fontSize: 11, fontWeight: 700,
          background: bg, color: '#fff', letterSpacing: 0.3,
        })

        const catMap: Record<string, string> = {
          security: 'Security', injection: 'Security', broken_auth: 'Security', sensitive_data: 'Security',
          xss: 'Security', secret_leak: 'Security', bugs: 'Reliability', bug: 'Reliability',
          performance: 'Reliability', compilation: 'Reliability', code_quality: 'Maintainability',
          best_practices: 'Maintainability', style: 'Maintainability', ai_slop: 'Maintainability',
        }
        const riskAreas: Record<string, { count: number; maxSev: string }> = {}
        for (const iss of allIssues) {
          const area = catMap[iss.category?.toLowerCase()] ?? 'Maintainability'
          if (!riskAreas[area]) riskAreas[area] = { count: 0, maxSev: 'info' }
          riskAreas[area].count++
          const sevOrder = ['critical', 'high', 'medium', 'low', 'info']
          if (sevOrder.indexOf(iss.severity) < sevOrder.indexOf(riskAreas[area].maxSev)) {
            riskAreas[area].maxSev = iss.severity
          }
        }

        const sevEmoji = (sev: string) => ({ critical: '🔴', high: '🟠', medium: '🟡', low: '🔵', info: 'ℹ️' }[sev] ?? '⚪')
        const progressBar = (val: number, max = 10) => {
          const filled = Math.round(val / max * 10)
          return '🟩'.repeat(filled) + '⬜'.repeat(10 - filled)
        }

        return (
          <div style={{
            border: '1px solid var(--clr-border, #333)',
            borderRadius: 12,
            background: 'var(--clr-surface, #111)',
            overflow: 'hidden',
          }}>
            {/* Header */}
            <div style={{ padding: '24px 28px', borderBottom: '1px solid #222' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ color: '#e0e0e0', margin: 0, fontSize: 18 }}>📊 MCP AI Project Review</h3>
                <button onClick={handleReset} style={btnOutline}>Yeni Review</button>
              </div>

              {/* Badges */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                <span style={badgeStyle(scoreClr)}>Quality {s.avg_score}/10</span>
                <span style={badgeStyle(secColor)}>Security {secScore}/10</span>
                <span style={badgeStyle(riskColor)}>Risk {riskLevel}</span>
                <span style={badgeStyle('#3b82f6')}>Issues {s.total_issues}</span>
                <span style={badgeStyle('#7c3aed')}>Tech Debt +{debtHours}h</span>
                <span style={badgeStyle('#6b7280')}>Files {s.reviewed}</span>
              </div>

              {/* Score bar */}
              <div style={{ fontSize: 14, marginBottom: 4 }}>
                <span style={{ marginRight: 8, color: '#aaa' }}>Quality:</span>
                <span style={{ letterSpacing: 1 }}>{progressBar(s.avg_score)}</span>
                <span style={{ marginLeft: 8, fontWeight: 700, color: scoreClr }}>{s.avg_score}/10</span>
              </div>
              <div style={{ fontSize: 14 }}>
                <span style={{ marginRight: 8, color: '#aaa' }}>Security:</span>
                <span style={{ letterSpacing: 1 }}>{progressBar(secScore)}</span>
                <span style={{ marginLeft: 8, fontWeight: 700, color: secColor }}>{secScore}/10</span>
              </div>
            </div>

            {/* Overview Table */}
            {Object.keys(riskAreas).length > 0 && (
              <div style={{ padding: '20px 28px', borderBottom: '1px solid #222' }}>
                <h4 style={{ color: '#ccc', margin: '0 0 12px', fontSize: 14 }}>Overview</h4>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #333' }}>
                      <th style={{ padding: '6px 0', textAlign: 'left', color: '#888', fontWeight: 600 }}>Risk Area</th>
                      <th style={{ padding: '6px 0', textAlign: 'center', color: '#888', fontWeight: 600 }}>Level</th>
                      <th style={{ padding: '6px 0', textAlign: 'center', color: '#888', fontWeight: 600 }}>Issues</th>
                    </tr>
                  </thead>
                  <tbody>
                    {['Security', 'Reliability', 'Maintainability'].filter(a => riskAreas[a]).map(area => (
                      <tr key={area} style={{ borderBottom: '1px solid #1a1a1a' }}>
                        <td style={{ padding: '8px 0', color: '#ddd', fontWeight: 600 }}>{area}</td>
                        <td style={{ padding: '8px 0', textAlign: 'center' }}>
                          {sevEmoji(riskAreas[area].maxSev)} <span style={{ color: sevColor(riskAreas[area].maxSev) }}>{riskAreas[area].maxSev.charAt(0).toUpperCase() + riskAreas[area].maxSev.slice(1)}</span>
                        </td>
                        <td style={{ padding: '8px 0', textAlign: 'center', color: '#ccc' }}>{riskAreas[area].count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Verdict */}
            <div style={{ padding: '16px 28px', borderBottom: '1px solid #222' }}>
              {s.critical > 0 ? (
                <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', borderLeft: '4px solid #ef4444' }}>
                  <span style={{ color: '#ef4444', fontWeight: 700 }}>❌ MERGE BLOCKED</span>
                  <span style={{ color: '#ccc', marginLeft: 8 }}>— {s.critical} critical issue(s). Fix effort: ~{debtHours}h</span>
                </div>
              ) : s.high > 0 ? (
                <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(249,115,22,0.1)', borderLeft: '4px solid #f97316' }}>
                  <span style={{ color: '#f97316', fontWeight: 700 }}>⚠️ REVIEW NEEDED</span>
                  <span style={{ color: '#ccc', marginLeft: 8 }}>— {s.high} high-severity issue(s). Consider fixing.</span>
                </div>
              ) : s.errors > s.reviewed ? (
                <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', borderLeft: '4px solid #ef4444' }}>
                  <span style={{ color: '#ef4444', fontWeight: 700 }}>❌ REVIEW FAILED</span>
                  <span style={{ color: '#ccc', marginLeft: 8 }}>— {s.errors} dosyada AI hatası. Rapor güvenilir değil. Farklı bir provider seçip tekrar deneyin.</span>
                </div>
              ) : (
                <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(34,197,94,0.1)', borderLeft: '4px solid #22c55e' }}>
                  <span style={{ color: '#22c55e', fontWeight: 700 }}>✅ APPROVED</span>
                  <span style={{ color: '#ccc', marginLeft: 8 }}>— No blocking issues. Project looks healthy.</span>
                </div>
              )}
            </div>

            {/* Project Summary */}
            <div style={{ padding: '20px 28px', borderBottom: '1px solid #222' }}>
              <h4 style={{ color: '#ccc', margin: '0 0 8px', fontSize: 14 }}>📋 Proje Özeti</h4>
              <p style={{ color: '#aaa', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                {review.filename} projesi {s.reviewed} dosya üzerinden AI ile incelendi.
                Ortalama kod kalitesi <strong style={{ color: scoreClr }}>{s.avg_score}/10</strong>.
                {s.total_issues === 0 ? (
                  <> Herhangi bir sorun tespit edilmedi. Proje sağlıklı görünüyor.</>
                ) : (
                  <> Toplamda <strong style={{ color: '#ccc' }}>{s.total_issues}</strong> sorun tespit edildi
                  {s.critical > 0 && <> (<strong style={{ color: '#ef4444' }}>{s.critical} critical</strong>)</>}
                  {s.high > 0 && <>{s.critical > 0 ? ', ' : ' ('}<strong style={{ color: '#f97316' }}>{s.high} high</strong>{s.critical === 0 ? ')' : ')'}</>}
                  . Tahmini düzeltme eforu <strong style={{ color: '#7c3aed' }}>{debtHours} saat</strong>.
                  {' '}{reviewed.length > 0 && <>En düşük puanlı dosya: <code style={{ color: '#818cf8', background: '#1a1a2e', padding: '1px 5px', borderRadius: 3 }}>{reviewed.sort((a, b) => (a.score ?? 10) - (b.score ?? 10))[0]?.file}</code> ({reviewed.sort((a, b) => (a.score ?? 10) - (b.score ?? 10))[0]?.score}/10).</>}
                  </>
                )}
              </p>
            </div>

            {/* File-by-file issues */}
            {filesWithIssues.length > 0 && (
              <div style={{ padding: '20px 28px' }}>
                <h4 style={{ color: '#ccc', margin: '0 0 16px', fontSize: 14 }}>🎯 Dosya Bazlı Sorunlar</h4>

                {filesWithIssues.map(r => (
                  <div key={r.file} style={{ marginBottom: 24 }}>
                    {/* File header */}
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
                      padding: '8px 12px', borderRadius: 6, background: '#1a1a2e',
                    }}>
                      <span style={{ fontSize: 16 }}>{(r.score ?? 0) >= 8 ? '🟢' : (r.score ?? 0) >= 5 ? '🟡' : '🔴'}</span>
                      <code style={{ color: '#e0e0e0', fontSize: 13, flex: 1 }}>{r.file}</code>
                      <span style={{ fontWeight: 700, color: scoreColor(r.score ?? 0), fontSize: 13 }}>{r.score}/10</span>
                      <span style={{ color: '#666', fontSize: 12 }}>{r.total_issues} issue{(r.total_issues ?? 0) > 1 ? 's' : ''}</span>
                    </div>

                    {/* Issues under this file */}
                    {(r.issues ?? []).map((iss, i) => {
                      const catLabel: Record<string, string> = {
                        compilation: '🔧 Compilation', security: '🔒 Security', performance: '⚡ Performance',
                        bugs: '🐛 Bug', bug: '🐛 Bug', code_quality: '✨ Code Quality',
                        best_practices: '📐 Best Practices', style: '🎨 Style', ai_slop: '🤖 AI Slop',
                      }
                      return (
                        <div key={i} style={{ marginLeft: 16, marginBottom: 12, paddingLeft: 12, borderLeft: `3px solid ${sevColor(iss.severity)}` }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span style={badgeStyle(sevColor(iss.severity))}>{iss.severity.toUpperCase()}</span>
                            <span style={{ fontWeight: 600, fontSize: 13, color: '#e0e0e0' }}>{iss.title}</span>
                          </div>
                          <div style={{ fontSize: 11, color: '#777', marginBottom: 4 }}>
                            📍 <code style={{ color: '#818cf8' }}>{r.file}</code> • {catLabel[iss.category?.toLowerCase()] ?? iss.category}
                          </div>
                          <p style={{ color: '#bbb', fontSize: 12, margin: '4px 0', lineHeight: 1.5 }}>{iss.description}</p>
                          {iss.suggestion && (
                            <div style={{ marginTop: 4, padding: '6px 10px', borderRadius: 4, background: '#0f0f1a', fontSize: 12 }}>
                              <span style={{ color: '#818cf8' }}>💡 Suggestion:</span>{' '}
                              <span style={{ color: '#aaa' }}>{iss.suggestion}</span>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                ))}

                {/* Clean files */}
                {(() => {
                  const clean = reviewed.filter(r => (r.total_issues ?? 0) === 0)
                  if (clean.length === 0) return null
                  return (
                    <details style={{ marginTop: 8 }}>
                      <summary style={{ cursor: 'pointer', fontSize: 13, color: '#22c55e', marginBottom: 8 }}>
                        ✅ {clean.length} dosyada sorun bulunamadı
                      </summary>
                      <div style={{ fontSize: 12, color: '#666', paddingLeft: 16 }}>
                        {clean.map(r => (
                          <div key={r.file} style={{ padding: '2px 0' }}>
                            🟢 {r.file} — {r.score}/10
                          </div>
                        ))}
                      </div>
                    </details>
                  )
                })()}
              </div>
            )}

            {/* No issues */}
            {filesWithIssues.length === 0 && (
              <div style={{ padding: '24px 28px', textAlign: 'center', color: '#22c55e', fontSize: 15 }}>
                ✅ Tüm dosyalar temiz — herhangi bir sorun bulunamadı.
              </div>
            )}
          </div>
        )
      })()}
    </div>
  )
}
