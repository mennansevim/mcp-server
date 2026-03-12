import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import App from '../App'

function jsonResponse(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('ConfigPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads and updates editable config fields', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/api/config') && (!init || !init.method || init.method === 'GET')) {
        return jsonResponse({
          ui: { logs: { poll_interval_seconds: 3, max_events_per_poll: 200 } },
          review: { comment_strategy: 'summary', focus: ['security', 'bugs'] },
          ai: { provider: 'openai', model: 'gpt-4o-mini' }
        })
      }

      if (url.endsWith('/api/config') && init?.method === 'PUT') {
        const body = JSON.parse(String(init.body))
        return jsonResponse(body)
      }

      throw new Error(`Unexpected fetch URL: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter initialEntries={['/config']}>
        <Routes>
          <Route path="*" element={<App />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Config' })).toBeInTheDocument()
    })

    const intervalInput = screen.getByLabelText('Poll Interval (sec)') as HTMLInputElement
    const maxEventsInput = screen.getByLabelText('Max Events Per Poll') as HTMLInputElement
    const providerSelect = screen.getByLabelText('LLM Provider') as HTMLSelectElement
    const modelSelect = screen.getByLabelText('LLM Model') as HTMLSelectElement
    const strategySelect = screen.getByLabelText('Comment Strategy') as HTMLSelectElement
    const focusInput = screen.getByLabelText('Focus Areas (comma separated)') as HTMLInputElement

    expect(intervalInput.value).toBe('3')
    expect(maxEventsInput.value).toBe('200')
    expect(providerSelect.value).toBe('openai')
    expect(modelSelect.value).toBe('gpt-4o-mini')
    expect(strategySelect.value).toBe('summary')
    expect(focusInput.value).toBe('security, bugs')

    await userEvent.clear(intervalInput)
    await userEvent.type(intervalInput, '5')
    await userEvent.selectOptions(providerSelect, 'groq')
    await userEvent.selectOptions(modelSelect, 'llama-3.1-70b-versatile')
    await userEvent.selectOptions(strategySelect, 'both')
    await userEvent.clear(focusInput)
    await userEvent.type(focusInput, 'security, performance')

    await userEvent.click(screen.getByRole('button', { name: 'Save Config' }))

    await waitFor(() => {
      expect(screen.getByText('Saved')).toBeInTheDocument()
    })

    const putCall = fetchMock.mock.calls.find((call) => {
      const url = String(call[0])
      const init = call[1] as RequestInit | undefined
      return url.endsWith('/api/config') && init?.method === 'PUT'
    })

    expect(putCall).toBeTruthy()
    const sentBody = JSON.parse(String((putCall?.[1] as RequestInit).body))
    expect(sentBody.ui.logs.poll_interval_seconds).toBe(5)
    expect(sentBody.ai.provider).toBe('groq')
    expect(sentBody.ai.model).toBe('llama-3.1-70b-versatile')
    expect(sentBody.review.comment_strategy).toBe('both')
    expect(sentBody.review.focus).toEqual(['security', 'performance'])
  })
})
