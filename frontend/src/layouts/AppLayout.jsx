import Navbar from '../components/Navbar'

export default function AppLayout({ children, path, user, theme, searchQuery, onSearch, onToggleTheme, onNavigate, onLogout }) {
  return <div className="app-shell"><Navbar path={path} user={user} theme={theme} searchQuery={searchQuery} onSearch={onSearch} onToggleTheme={onToggleTheme} onNavigate={onNavigate} onLogout={onLogout} />{children}</div>
}
