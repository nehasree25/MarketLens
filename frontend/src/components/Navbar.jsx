import { useState } from 'react'
import ThemeToggle from './ThemeToggle'
import UserMenu from './UserMenu'

const links = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Watchlists', path: '/watchlists' },
  { label: 'Stocks', path: '/stocks' },
]

export default function Navbar({ path, user, theme, onToggleTheme, onNavigate, onLogout }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = (nextPath) => { setMobileOpen(false); onNavigate(nextPath) }
  return <header className="topbar"><div className="brand-lockup"><div className="brand-mark" aria-hidden="true"><span /></div><div><strong>MarketLens</strong><small>See what changed. Know what matters.</small></div></div><nav className="primary-nav" aria-label="Primary navigation">{links.map((link) => <button className={`nav-link ${path === link.path ? 'active' : ''}`} type="button" key={link.path} onClick={() => navigate(link.path)}>{link.label}</button>)}</nav><div className="nav-actions"><ThemeToggle theme={theme} onToggle={onToggleTheme} /><UserMenu user={user} onLogout={onLogout} /><button className="menu-toggle" type="button" onClick={() => setMobileOpen((value) => !value)} aria-label="Toggle navigation menu" aria-expanded={mobileOpen}>{mobileOpen ? '×' : '☰'}</button></div>{mobileOpen && <nav className="mobile-nav" aria-label="Mobile navigation">{links.map((link) => <button className={`mobile-nav-link ${path === link.path ? 'active' : ''}`} type="button" key={link.path} onClick={() => navigate(link.path)}>{link.label}<span>→</span></button>)}<div className="mobile-nav-divider" /><div className="mobile-nav-option"><span>Theme</span><ThemeToggle theme={theme} onToggle={onToggleTheme} /></div><button className="mobile-logout" type="button" onClick={onLogout}>Sign out <span>↗</span></button></nav>}</header>
}
