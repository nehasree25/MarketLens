import { useEffect, useState } from 'react'
import Dashboard from './pages/Dashboard'
import Watchlists from './pages/Watchlists'
import WatchlistDetails from './pages/WatchlistDetails'
import Search from './pages/Search'
import Stocks from './pages/Stocks'
import StockDetailsPage from './components/StockDetailsPage'
import Signup from './pages/Signup'
import LoginScreen from './components/LoginScreen'
import LoadingState from './components/LoadingState'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import AppLayout from './layouts/AppLayout'
import { AuthProvider, useAuth } from './context/AuthContext'
import { getDashboardSummary } from './services/dashboard'
import './App.css'

function usePath() {
  const [path, setPath] = useState(window.location.pathname)
  useEffect(() => {
    const handlePopState = () => setPath(window.location.pathname)
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])
  return [path, (nextPath) => { window.history.pushState({}, '', nextPath); setPath(nextPath) }]
}

function DashboardRoute({ theme, setTheme, navigate, searchQuery }) {
  const { user, logout } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    if (!user) return
    getDashboardSummary()
      .then(setData)
      .catch(async (requestError) => {
        if (requestError.status === 401) await logout()
        else setError('Unable to load your dashboard. Please try again.')
      })
  }, [user, logout, retryKey])

  if (!data && !error) return <LoadingState />
  if (error) return <main className="message-shell"><div className="message-card"><span className="message-icon">!</span><h1>Unable to load dashboard</h1><p>{error}</p><button className="primary-button" type="button" onClick={() => { setError(null); setData(null); setRetryKey((key) => key + 1) }}>Retry <span>↻</span></button></div></main>
  return <AppLayout path="/dashboard" user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={() => { logout(); navigate('/login') }}><Dashboard data={data} searchQuery={searchQuery} /></AppLayout>
}

function ProtectedPage({ title, path, user, theme, setTheme, navigate, logout }) {
  return <ProtectedRoute><AppLayout path={path} user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={() => { logout(); navigate('/login') }}><main className="message-shell page-placeholder"><div className="message-card"><span className="eyebrow">Protected workspace</span><h1>{title}</h1><p>This section is protected and ready for its data workflow.</p></div></main></AppLayout></ProtectedRoute>
}

function WatchlistsRoute({ theme, setTheme, navigate }) {
  const { user, logout } = useAuth()
  const exitToLogin = () => { logout(); navigate('/login') }
  return <AppLayout path="/watchlists" user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={exitToLogin}><Watchlists onNavigate={navigate} onUnauthorized={exitToLogin} /></AppLayout>
}

function WatchlistDetailsRoute({ watchlistId, theme, setTheme, navigate }) {
  const { user, logout } = useAuth()
  const exitToLogin = () => { logout(); navigate('/login') }
  return <AppLayout path={`/watchlists/${watchlistId}`} user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={exitToLogin}><WatchlistDetails watchlistId={watchlistId} onBack={() => navigate('/watchlists')} onUnauthorized={exitToLogin} onOpenStock={(stockId) => navigate(`/stocks/${stockId}`)} /></AppLayout>
}

function StockDetailsRoute({ stockId, theme, setTheme, navigate }) {
  const { user, logout } = useAuth()
  const exitToLogin = () => { logout(); navigate('/login') }
  return <AppLayout path="/stocks" user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={exitToLogin}><StockDetailsPage stockId={stockId} onBack={() => navigate('/dashboard')} onUnauthorized={exitToLogin} /></AppLayout>
}

function SearchRoute({ theme, setTheme, navigate }) {
  const { user, logout } = useAuth()
  const exitToLogin = () => { logout(); navigate('/login') }
  return <AppLayout path="/search" user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={exitToLogin}><Search onNavigate={navigate} onUnauthorized={exitToLogin} /></AppLayout>
}

function StocksRoute({ theme, setTheme, navigate }) {
  const { user, logout } = useAuth()
  const exitToLogin = () => { logout(); navigate('/login') }
  return <AppLayout path="/stocks" user={user} theme={theme} onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')} onNavigate={navigate} onLogout={exitToLogin}><Stocks onNavigate={navigate} onUnauthorized={exitToLogin} /></AppLayout>
}

function AppContent() {
  const { user, loading, login, signup, logout } = useAuth()
  const [path, navigate] = usePath()
  const [theme, setTheme] = useState(() => localStorage.getItem('marketlens_theme') || 'dark')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('marketlens_theme', theme)
  }, [theme])

  if (loading) return <main className="auth-loading"><div className="brand-mark" aria-hidden="true"><span /></div><p>Restoring your workspace…</p></main>
  if (!user && path !== '/login' && path !== '/signup') { navigate('/login'); return null }
  if (user && (path === '/login' || path === '/signup' || path === '/')) { navigate('/dashboard'); return null }
  if (path === '/signup') return <Signup onSignup={signup} onLogin={() => navigate('/login')} />
  if (path === '/login') return <LoginScreen onLogin={login} onSignup={() => navigate('/signup')} />
  if (path === '/dashboard' || path === '/') return <DashboardRoute theme={theme} setTheme={setTheme} navigate={navigate} searchQuery='' />
  if (path === '/watchlists') return <WatchlistsRoute theme={theme} setTheme={setTheme} navigate={navigate} />
  if (/^\/watchlists\/\d+$/.test(path)) return <WatchlistDetailsRoute watchlistId={path.split('/')[2]} theme={theme} setTheme={setTheme} navigate={navigate} />
  if (/^\/stocks\/\d+$/.test(path)) return <StockDetailsRoute stockId={path.split('/')[2]} theme={theme} setTheme={setTheme} navigate={navigate} />
  if (path === '/search') return <SearchRoute theme={theme} setTheme={setTheme} navigate={navigate} />
  if (path === '/stocks') return <StocksRoute theme={theme} setTheme={setTheme} navigate={navigate} />
  if (path.startsWith('/stock/') || path.startsWith('/watchlist/')) return <ProtectedPage title="MarketLens detail" path={path} user={user} theme={theme} setTheme={setTheme} navigate={navigate} logout={logout} />
  navigate(user ? '/dashboard' : '/login')
  return null
}

function App() {
  return <ErrorBoundary><AuthProvider><AppContent /></AuthProvider></ErrorBoundary>
}

export default App
