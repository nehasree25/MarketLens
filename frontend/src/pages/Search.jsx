import { useEffect, useRef, useState } from 'react'
import { searchStocks } from '../services/stocks'
import { addStockToWatchlist, getWatchlists } from '../services/watchlists'

function SearchResult({ stock, onOpen, onAdd }) {
  return <article className="discovery-result"><div><strong>{stock.company_name}</strong><span>{stock.symbol} · {stock.exchange}</span></div><div className="discovery-actions"><button className="secondary-button" type="button" onClick={() => onOpen(stock.id)}>View details <span>→</span></button><button className="primary-button" type="button" onClick={() => onAdd(stock)}>Add to watchlist</button></div></article>
}

function AddToWatchlistDialog({ stock, onClose, onUnauthorized }) {
  const [watchlists, setWatchlists] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        setWatchlists(await getWatchlists())
      } catch (requestError) {
        if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
        else setError('Unable to load your watchlists. Please try again.')
      } finally {
        setLoading(false)
      }
    }, 0)
    return () => clearTimeout(timer)
  }, [onUnauthorized])

  async function add() {
    if (!selectedId) return
    setAdding(true)
    setError(null)
    try {
      await addStockToWatchlist(Number(selectedId), stock.id)
      setSuccess('Stock added to your watchlist.')
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else if (requestError.status === 400 || requestError.status === 409) setError('This stock may already be in that watchlist.')
      else setError('Unable to add this stock.')
    } finally {
      setAdding(false)
    }
  }

  return <div className="dialog-backdrop" role="presentation"><div className="dialog discovery-dialog" role="dialog" aria-modal="true" aria-labelledby="add-discovery-title"><div className="dialog-header"><div><span className="eyebrow">Watchlist action</span><h2 id="add-discovery-title">Add to watchlist</h2></div><button className="dialog-close" type="button" onClick={onClose} aria-label="Close dialog">×</button></div><p className="dialog-stock-name">{stock.company_name}<span>{stock.symbol} · {stock.exchange}</span></p>{loading ? <p className="search-state">Loading watchlists...</p> : watchlists.length === 0 ? <div className="search-state"><strong>No watchlists yet.</strong><span>Create a watchlist before adding stocks.</span></div> : <><label className="dialog-label">Choose a watchlist<select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}><option value="">Select a watchlist</option>{watchlists.map((watchlist) => { const alreadyAdded = watchlist.stocks?.some((item) => item.id === stock.id); return <option key={watchlist.id} value={watchlist.id} disabled={alreadyAdded}>{watchlist.name}{alreadyAdded ? ' · Already added' : ''}</option> })}</select></label>{success && <p className="check-success">{success}</p>}{error && <p className="form-error">{error}</p>}<div className="dialog-actions"><button className="secondary-button" type="button" onClick={onClose}>Close</button><button className="primary-button" type="button" disabled={!selectedId || adding || Boolean(success)} onClick={add}>{adding ? 'Adding...' : 'Add stock'}<span>→</span></button></div></>}</div></div>
}

export default function Search({ onNavigate, onUnauthorized }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState(null)
  const [selectedStock, setSelectedStock] = useState(null)
  const [retryKey, setRetryKey] = useState(0)
  const searchVersion = useRef(0)

  function handleQueryChange(value) {
    searchVersion.current += 1
    setQuery(value)
    setResults([])
    setError(null)
    setSearching(Boolean(value.trim()))
  }

  useEffect(() => {
    const trimmed = query.trim()
    if (!trimmed) return undefined
    const version = searchVersion.current
    const timer = setTimeout(async () => {
      try {
        const nextResults = await searchStocks(trimmed)
        if (version === searchVersion.current) setResults(nextResults)
      } catch (requestError) {
        if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
        else if (version === searchVersion.current) setError('Unable to search stocks. Please try again.')
      } finally {
        if (version === searchVersion.current) setSearching(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, onUnauthorized, retryKey])

  return <main className="dashboard-content discovery-content"><div className="discovery-heading"><div><span className="eyebrow">Stock catalogue</span><h1>Search stocks</h1><p className="muted">Find stocks by symbol or company name.</p></div></div><label className="discovery-search"><span aria-hidden="true">⌕</span><span className="sr-only">Search stocks by symbol or company name</span><input type="search" value={query} onChange={(event) => handleQueryChange(event.target.value)} placeholder="Search stocks by symbol or company name..." autoComplete="off" />{query && <button type="button" onClick={() => handleQueryChange('')} aria-label="Clear search">×</button>}</label><section className="discovery-results" aria-live="polite">{searching ? <div className="discovery-state"><span className="skeleton discovery-skeleton" /><span>Searching stocks...</span></div> : error ? <div className="discovery-state"><strong>{error}</strong><button className="secondary-button" type="button" onClick={() => { setError(null); setSearching(true); setRetryKey((key) => key + 1) }}>Retry</button></div> : !query.trim() ? <div className="discovery-state"><strong>Search for a stock</strong><span>Find active stocks by symbol or company name.</span></div> : results.length === 0 ? <div className="discovery-state"><strong>No stocks found</strong><span>Try another symbol or company name.</span></div> : results.map((stock) => <SearchResult key={stock.id} stock={stock} onOpen={(id) => onNavigate(`/stocks/${id}`)} onAdd={setSelectedStock} />)}</section>{selectedStock && <AddToWatchlistDialog stock={selectedStock} onClose={() => setSelectedStock(null)} onUnauthorized={onUnauthorized} />}</main>
}
