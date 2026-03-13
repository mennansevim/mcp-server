import { NavLink } from 'react-router-dom'

interface AppShellProps {
  children: React.ReactNode
}

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <nav className="topnav">
        <div className="topnav-brand">MCP Code Review</div>
        <div className="topnav-links">
          <NavLink to="/logs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            PR Runs
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Analytics
          </NavLink>
          <NavLink to="/config" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Settings
          </NavLink>
        </div>
      </nav>
      <main className="page">{children}</main>
    </div>
  )
}
