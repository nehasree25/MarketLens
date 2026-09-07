import { useEffect, useState } from 'react'
import { searchStocks } from '../services/stocks'
import { addStockToWatchlist } from '../services/watchlists'

export default function AddStockModal({ watchlist, onClose, onUpdated, onUnauthorized }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState(null)
  const [addingId, setAddingId] = useState(null)
  const [addError, setAddError] = useState(null)
  const existingIds = new Set((watchlist.stocks || []).map((stock) => stock.id))

  function handleQueryChange(value) {
    setQuery(value)
    if (!value.trim()) {
      setResults([])
      setSearchError(null)
      setSearching(false)
    }
  }

  useEffect(() => {
    const trimmedQuery = query.trim()
    if (!trimmedQuery) {
      return undefined
    }
    const timer = setTimeout(async () => {
      setSearching(true)
      setSearchError(null)
      try {
        const response = await searchStocks(trimmedQuery)
        setResults(response.data || [])
      } catch (error) {
        if (error.status === 401 || error.status === 403) onUnauthorized()
        else setSearchError('Unable to load stocks. Please try again.')
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, onUnauthorized])

  async function addStock(stock) {
    setAddingId(stock.id)
    setAddError(null)
    try {
      const updated = await addStockToWatchlist(watchlist.id, stock.id)
      onUpdated(updated)
    } catch (error) {
      if (error.status === 401 || error.status === 403) onUnauthorized()
      else if (error.status === 400 || error.status === 409) setAddError('This stock may already be in your watchlist.')
      else setAddError('Unable to add this stock.')
    } finally {
      setAddingId(null)
    }
  }

  return <div className="dialog-backdrop" role="presentation"><div className="dialog add-stock-dialog" role="dialog" aria-modal="true" aria-labelledby="add-stock-title"><div className="dialog-header"><div><span className="eyebrow">Stock catalogue</span><h2 id="add-stock-title">Add stock</h2></div><button className="dialog-close" type="button" onClick={onClose} aria-label="Close dialog">×</button></div><input className="stock-search-input" type="search" value={query} onChange={(event) => handleQueryChange(event.target.value)} placeholder="Search stocks..." autoFocus />{addError && <p className="form-error">{addError}</p>}<div className="search-results">{searching ? <p className="search-state">Searching...</p> : searchError ? <p className="form-error">{searchError}</p> : !query.trim() ? <p className="search-state">Search by symbol or company name.</p> : results.length === 0 ? <p className="search-state"><strong>No stocks found.</strong><span>Try a different symbol or company name.</span></p> : results.map((stock) => { const alreadyAdded = existingIds.has(stock.id); return <div className="search-result" key={stock.id}><div><strong>{stock.symbol}</strong><span>{stock.company_name} · {stock.exchange}</span></div><button className="secondary-button" type="button" disabled={alreadyAdded || addingId === stock.id} onClick={() => addStock(stock)}>{alreadyAdded ? 'Already added' : addingId === stock.id ? 'Adding...' : 'Add'}</button></div> })}</div><div className="dialog-actions"><button className="secondary-button" type="button" onClick={onClose}>Close</button></div></div></div>
}
