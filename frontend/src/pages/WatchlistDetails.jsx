import { useCallback, useEffect, useMemo, useState } from 'react'
import AddStockModal from '../components/AddStockModal'
import RemoveStockDialog from '../components/RemoveStockDialog'
import StockChangeCard from '../components/StockChangeCard'
import { checkStock } from '../services/stocks'
import { getWatchlist, getWatchlistChanges, removeStockFromWatchlist } from '../services/watchlists'

export default function WatchlistDetails({ watchlistId, onBack, onUnauthorized }) {
  const [watchlist, setWatchlist] = useState(null)
  const [changes, setChanges] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modal, setModal] = useState(null)
  const [checkingId, setCheckingId] = useState(null)
  const [removing, setRemoving] = useState(false)
  const [removeError, setRemoveError] = useState(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [watchlistResponse, changesResponse] = await Promise.all([
        getWatchlist(watchlistId),
        getWatchlistChanges(watchlistId),
      ])
      setWatchlist(watchlistResponse)
      setChanges(changesResponse)
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else setError(requestError.status === 404 ? 'Watchlist not found.' : 'Unable to load watchlist changes.')
    } finally {
      setLoading(false)
    }
  }, [watchlistId, onUnauthorized])

  useEffect(() => {
    const timer = setTimeout(() => { loadData() }, 0)
    return () => clearTimeout(timer)
  }, [loadData])

  const stockInfo = useMemo(() => new Map((watchlist?.stocks || []).map((stock) => [stock.id, stock])), [watchlist])

  function openRemove(stock) {
    setRemoveError(null)
    setModal({ type: 'remove', stock })
  }

  async function confirmRemove() {
    setRemoving(true)
    setRemoveError(null)
    try {
      await removeStockFromWatchlist(watchlist.id, modal.stock.id)
      setModal(null)
      await loadData()
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else setRemoveError(requestError.status === 404 ? 'This stock is no longer in the watchlist.' : 'Unable to remove this stock.')
    } finally {
      setRemoving(false)
    }
  }

  async function handleCheck(stockId) {
    setCheckingId(stockId)
    try {
      await checkStock(stockId)
      await loadData()
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else setError(requestError.status === 404 ? 'No market snapshot is available for this stock.' : 'Unable to check this stock. Please try again.')
    } finally {
      setCheckingId(null)
    }
  }

  if (loading) return <main className="dashboard-content detail-content"><div className="skeleton detail-skeleton" /></main>
  if (error) return <main className="dashboard-content detail-content"><button className="back-link" type="button" onClick={onBack}>← Back to watchlists</button><div className="watchlist-message"><h2>{error}</h2><button className="secondary-button" type="button" onClick={loadData}>Retry</button></div></main>

  const hasStocks = changes.stocks.length > 0
  const noSignificantChanges = hasStocks && changes.stocks.every((stock) => stock.attention_level === 'NO_NOTABLE_CHANGE' || stock.status === 'NO_NEW_DATA')

  return <main className="dashboard-content detail-content"><button className="back-link" type="button" onClick={onBack}>← Back to watchlists</button><div className="detail-heading"><div><span className="eyebrow">Watchlist changes</span><h1>{changes.watchlist_name}</h1><p className="muted">Since you last checked</p></div><button className="primary-button" type="button" onClick={() => setModal({ type: 'add' })}>+ Add stock</button></div><section className="change-summary"><div><span>Total stocks</span><strong>{changes.summary.total_stocks}</strong></div><div className="summary-high"><span>High attention</span><strong>{changes.summary.high_attention}</strong></div><div className="summary-notable"><span>Notable</span><strong>{changes.summary.notable}</strong></div><div className="summary-mild"><span>Mild</span><strong>{changes.summary.mild}</strong></div><div className="summary-quiet"><span>No notable change</span><strong>{changes.summary.no_notable_change}</strong></div></section>{!hasStocks ? <div className="watchlist-empty"><h2>No stocks in this watchlist yet.</h2><p>Add stocks to start tracking changes.</p><button className="primary-button" type="button" onClick={() => setModal({ type: 'add' })}>+ Add stock</button></div> : <><div className="changes-heading"><div><span className="eyebrow">Backend-ranked signals</span><h2>Stock changes</h2></div>{noSignificantChanges && <span className="muted">No significant changes since your last check.</span>}</div><div className="changes-grid">{changes.stocks.map((change) => { const info = stockInfo.get(change.stock_id); return <StockChangeCard key={change.stock_id} change={change} companyName={info?.company_name} exchange={info?.exchange} onCheck={handleCheck} checking={checkingId === change.stock_id} onRemove={openRemove} /> })}</div></>}{modal?.type === 'add' ? <AddStockModal watchlist={watchlist} onClose={() => setModal(null)} onUpdated={async (updated) => { setWatchlist(updated); setModal(null); await loadData() }} onUnauthorized={onUnauthorized} /> : null}{modal?.type === 'remove' ? <RemoveStockDialog stock={modal.stock} removing={removing} error={removeError} onClose={() => setModal(null)} onConfirm={confirmRemove} /> : null}</main>
}
