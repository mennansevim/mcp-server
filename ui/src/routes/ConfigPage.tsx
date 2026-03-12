import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getEditableConfig, updateEditableConfig } from '../lib/api'
import type { EditableConfig } from '../types/logs'

const AI_MODEL_OPTIONS: Record<EditableConfig['ai']['provider'], string[]> = {
  openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo-preview'],
  anthropic: ['claude-3-5-sonnet-20241022'],
  groq: ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'mixtral-8x7b-32768']
}

const DEFAULT_CONFIG: EditableConfig = {
  ui: { logs: { poll_interval_seconds: 3, max_events_per_poll: 200 } },
  review: { comment_strategy: 'summary', focus: ['security', 'bugs'] },
  ai: { provider: 'openai', model: 'gpt-4o-mini' }
}

function normalizeConfig(input: EditableConfig): EditableConfig {
  const provider = input.ai?.provider && input.ai.provider in AI_MODEL_OPTIONS
    ? input.ai.provider
    : DEFAULT_CONFIG.ai.provider
  const model = AI_MODEL_OPTIONS[provider].includes(input.ai?.model)
    ? input.ai.model
    : AI_MODEL_OPTIONS[provider][0]

  return {
    ui: {
      logs: {
        poll_interval_seconds: Number(input.ui?.logs?.poll_interval_seconds || DEFAULT_CONFIG.ui.logs.poll_interval_seconds),
        max_events_per_poll: Number(input.ui?.logs?.max_events_per_poll || DEFAULT_CONFIG.ui.logs.max_events_per_poll)
      }
    },
    review: {
      comment_strategy: input.review?.comment_strategy || DEFAULT_CONFIG.review.comment_strategy,
      focus: Array.isArray(input.review?.focus) ? input.review.focus : DEFAULT_CONFIG.review.focus
    },
    ai: { provider, model }
  }
}

export default function ConfigPage() {
  const [config, setConfig] = useState<EditableConfig>(DEFAULT_CONFIG)
  const [focusText, setFocusText] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const data = await getEditableConfig()
        if (!mounted) {
          return
        }
        const normalized = normalizeConfig(data)
        setConfig(normalized)
        setFocusText((normalized.review.focus || []).join(', '))
        setError(null)
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load config')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      mounted = false
    }
  }, [])

  const parsedFocus = useMemo(
    () => focusText.split(',').map((item) => item.trim()).filter(Boolean),
    [focusText]
  )

  useEffect(() => {
    if (!toast) {
      return
    }
    const timer = window.setTimeout(() => {
      setToast(null)
    }, 2200)
    return () => window.clearTimeout(timer)
  }, [toast])

  const onSave = async () => {
    setSaving(true)
    setError(null)

    try {
      const payload: EditableConfig = {
        ui: {
          logs: {
            poll_interval_seconds: Math.max(1, Number(config.ui.logs.poll_interval_seconds) || 1),
            max_events_per_poll: Math.max(20, Number(config.ui.logs.max_events_per_poll) || 20)
          }
        },
        review: {
          comment_strategy: config.review.comment_strategy,
          focus: parsedFocus
        },
        ai: {
          provider: config.ai.provider,
          model: config.ai.model
        },
      }

      const updated = await updateEditableConfig(payload)
      setConfig(updated)
      setFocusText((updated.review.focus || []).join(', '))
      setToast({ type: 'success', message: 'Saved' })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save config'
      setError(msg)
      setToast({ type: 'error', message: msg })
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="page">
      <header className="panel">
        <h1>Config</h1>
        <p>
          <Link to="/logs">Back to dashboard</Link>
        </p>

        {loading ? <p>Loading config...</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
        {toast ? (
          <div className={`toast toast-${toast.type}`} role="status">
            {toast.message}
          </div>
        ) : null}

        <section className="config-grid">
          <label>
            Poll Interval (sec)
            <input
              type="number"
              min={1}
              value={config.ui.logs.poll_interval_seconds}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  ui: {
                    ...prev.ui,
                    logs: {
                      ...prev.ui.logs,
                      poll_interval_seconds: Number(e.target.value)
                    }
                  }
                }))
              }
            />
          </label>

          <label>
            Max Events Per Poll
            <input
              type="number"
              min={20}
              value={config.ui.logs.max_events_per_poll}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  ui: {
                    ...prev.ui,
                    logs: {
                      ...prev.ui.logs,
                      max_events_per_poll: Number(e.target.value)
                    }
                  }
                }))
              }
            />
          </label>

          <label>
            LLM Provider
            <select
              value={config.ai.provider}
              onChange={(e) => {
                const provider = e.target.value as EditableConfig['ai']['provider']
                setConfig((prev) => ({
                  ...prev,
                  ai: {
                    provider,
                    model: AI_MODEL_OPTIONS[provider][0]
                  }
                }))
              }}
            >
              <option value="openai">openai</option>
              <option value="anthropic">anthropic</option>
              <option value="groq">groq</option>
            </select>
          </label>

          <label>
            LLM Model
            <select
              value={config.ai.model}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  ai: {
                    ...prev.ai,
                    model: e.target.value
                  }
                }))
              }
            >
              {AI_MODEL_OPTIONS[config.ai.provider].map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </label>

          <label>
            Comment Strategy
            <select
              value={config.review.comment_strategy}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  review: {
                    ...prev.review,
                    comment_strategy: e.target.value as EditableConfig['review']['comment_strategy']
                  }
                }))
              }
            >
              <option value="summary">summary</option>
              <option value="inline">inline</option>
              <option value="both">both</option>
            </select>
          </label>

          <label>
            Focus Areas (comma separated)
            <input
              type="text"
              value={focusText}
              onChange={(e) => setFocusText(e.target.value)}
            />
          </label>
        </section>

        <button type="button" disabled={saving || loading} onClick={onSave}>
          {saving ? 'Saving...' : 'Save Config'}
        </button>
      </header>
    </main>
  )
}
