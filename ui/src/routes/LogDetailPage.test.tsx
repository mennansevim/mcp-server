import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import LogDetailPage from './LogDetailPage'

function jsonResponse(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('LogDetailPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('groups header and step events while appending with cursor', async () => {
    let eventsCallCount = 0

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/logs/config')) {
        return jsonResponse({ poll_interval_seconds: 1, max_events_per_poll: 200 })
      }

      if (url.includes('/api/logs/active/run-1/events')) {
        eventsCallCount += 1
        if (eventsCallCount === 1) {
          return jsonResponse({
            run: {
              run_id: 'run-1',
              status: 'active',
              pr_id: '5',
              title: 'PR #5 webhook test',
              author: 'gocenalper'
            },
            events: [
              { seq: 1, ts: '2026-03-04T11:51:40.427495+00:00', level: 'info', step: 'console_header', message: '📦 Platform: GITHUB', meta: {} },
              { seq: 2, ts: '2026-03-04T11:51:40.427613+00:00', level: 'info', step: 'console_header', message: '🔗 PR #5: PR #5 webhook test', meta: {} },
              { seq: 3, ts: '2026-03-04T11:51:40.427700+00:00', level: 'info', step: 'console_header', message: '--------------------------------------------------------------------------------', meta: {} },
              { seq: 4, ts: '2026-03-04T11:51:40.427701+00:00', level: 'info', step: 'step_1', message: '📥 Step 1/5: Fetching diff from platform...', meta: {} },
              { seq: 5, ts: '2026-03-04T11:51:40.427702+00:00', level: 'info', step: 'step_1', message: '✅ Diff fetched successfully (25876 bytes)', meta: {} }
            ],
            next_cursor: 5
          })
        }

        return jsonResponse({
          run: {
            run_id: 'run-1',
            status: 'active',
            pr_id: '5',
            title: 'PR #5 webhook test',
            author: 'gocenalper'
          },
          events: [
            { seq: 6, ts: '2026-03-04T11:51:41.427613+00:00', level: 'info', step: 'step_2', message: '🔍 Step 2/5: Analyzing diff...', meta: {} },
            { seq: 7, ts: '2026-03-04T11:51:41.427700+00:00', level: 'info', step: 'step_2_file', message: '📄 src/main.ts', meta: {} }
          ],
          next_cursor: 7
        })
      }

      throw new Error(`Unexpected fetch URL: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter initialEntries={['/logs/run-1']}>
        <Routes>
          <Route path="/logs/:runId" element={<LogDetailPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('PR Header')).toBeInTheDocument()
      expect(screen.getByText('Step 1')).toBeInTheDocument()
      expect(screen.getByText('📦 Platform: GITHUB')).toBeInTheDocument()
    })

    await waitFor(
      () => {
        expect(screen.getByText('Step 2')).toBeInTheDocument()
        expect(screen.getByText('📄 src/main.ts')).toBeInTheDocument()
      },
      { timeout: 2500 }
    )

    expect(screen.queryByText('--------------------------------------------------------------------------------')).not.toBeInTheDocument()
    expect(screen.getByTestId('group-card-header')).toBeInTheDocument()
    expect(screen.getByTestId('group-card-step_1')).toBeInTheDocument()
    expect(screen.getByTestId('group-card-step_2')).toBeInTheDocument()
  })
})
