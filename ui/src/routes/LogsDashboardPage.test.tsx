import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LogsDashboardPage from './LogsDashboardPage'

function jsonResponse(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('LogsDashboardPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders active run row and pulsing green indicator', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/logs/config')) {
        return jsonResponse({ poll_interval_seconds: 3, max_events_per_poll: 200 })
      }
      if (url.endsWith('/api/logs/runs')) {
        return jsonResponse({
          count: 3,
          runs: [
            {
              run_id: 'run-1',
              platform: 'github',
              pr_id: '142',
              title: 'feat: auth middleware',
              author: 'mehmet',
              source_branch: 'feature/auth',
              target_branch: 'main',
              status: 'active',
              updated_at: '2026-03-04T11:51:40.427466+00:00'
            },
            {
              run_id: 'run-2',
              platform: 'github',
              pr_id: '143',
              title: 'feat: cache',
              author: 'ali',
              source_branch: 'feature/cache',
              target_branch: 'main',
              status: 'error',
              updated_at: '2026-03-04T11:51:39.427466+00:00'
            },
            {
              run_id: 'run-3',
              platform: 'github',
              pr_id: '144',
              title: 'feat: metrics',
              author: 'ayse',
              source_branch: 'feature/metrics',
              target_branch: 'main',
              status: 'completed',
              updated_at: '2026-03-04T11:51:38.427466+00:00'
            }
          ]
        })
      }
      throw new Error(`Unexpected fetch URL: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <LogsDashboardPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('PR #142')).toBeInTheDocument()
    })

    expect(screen.getByText('feat: auth middleware')).toBeInTheDocument()
    expect(screen.getByText('mehmet')).toBeInTheDocument()
    expect(screen.getByTestId('status-dot-run-1')).toHaveClass('dot-active')
    expect(screen.getByTestId('status-dot-run-2')).toHaveClass('dot-error')
    expect(screen.getByTestId('status-dot-run-3')).toHaveClass('dot-completed')
  })
})
