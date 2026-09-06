import { useEffect, useState } from 'react'
import { getWatchlist } from '../services/watchlists'

export default function WatchlistDetails({ watchlistId, onBack, onUnauthorized }) {
  const [watchlist, setWatchlist] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getWatchlist(watchlistId)
      .then(setWatchlist)
      .catch((requestError) => {
        if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
        else setError(requestError.status === 404 ? 'Watchlist not found.' : 'Unable to load this watchlist.')
      })
      .finally(() => setLoading(false))
  }, [watchlistId, onUnauthorized])

  if (loading) return <main className="dashboard-content detail-content"><div className="skeleton detail-skeleton" /></main>
  if (error) return <main className="dashboard-content detail-content"><button className="back-link" type="button" onClick={onBack}>← Back to watchlists</button><div className="watchlist-message"><h2>{error}</h2></div></main>

  return <main className="dashboard-content detail-content"><button className="back-link" type="button" onClick={onBack}>← Back to watchlists</button><div className="detail-heading"><div><span className="eyebrow">Watchlist detail</span><h1>{watchlist.name}</h1><p className="muted">Created {new Date(watchlist.created_at).toLocaleDateString()}</p></div><span className="detail-count">{watchlist.stocks?.length ?? 0} stocks</span></div><section className="panel detail-panel"><div className="panel-heading"><div><span className="eyebrow">Tracked collection</span><h2>Stocks in this watchlist</h2></div></div>{watchlist.stocks?.length ? <div className="detail-stock-list">{watchlist.stocks.map((stock) => <div className="detail-stock-row" key={stock.id}><div><strong>{stock.symbol}</strong><span>{stock.company_name}</span></div><span>{stock.exchange}</span></div>)}</div> : <div className="empty-table"><strong>No stocks in this watchlist yet.</strong><span>Stocks can be added in a later workflow.</span></div>}</section></main>
}
