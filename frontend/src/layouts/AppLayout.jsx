import Navbar from '../components/Navbar'

export default function AppLayout({ children, path, user, theme, onToggleTheme, onNavigate, onLogout }) {
  return <div className="app-shell"><Navbar path={path} user={user} theme={theme} onToggleTheme={onToggleTheme} onNavigate={onNavigate} onLogout={onLogout} />{children}</div>
}
