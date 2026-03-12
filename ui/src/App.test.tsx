import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

vi.mock('./routes/LogsDashboardPage', () => ({
  default: () => <h1>Active PR Runs</h1>
}))

vi.mock('./routes/LogDetailPage', () => ({
  default: () => <h1>Run Detail</h1>
}))

describe('App routes', () => {
  it('shows Active PR Runs title', () => {
    render(
      <MemoryRouter initialEntries={['/logs']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByText('Active PR Runs')).toBeInTheDocument()
  })
})
