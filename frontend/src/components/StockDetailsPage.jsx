import { useCallback, useEffect, useMemo, useState } from 'react'
import { checkStock, getMarketData, getStock, getStockAttention, getStockChanges, getStockState } from '../services/stocks'

function valueOrUnavailable(value, format = String) {
  return value === null || value === undefined ? 'Unavailable' : format(value)
}

function number(value) {
  return valueOrUnavailable(value, (item) => Number(item).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
}

function percent(value) {
  return valueOrUnavailable(value, (item) => `${item > 0 ? '+' : ''}${Number(item).toFixed(2)}%`)
}

function date(value) {
  if (!value) return 'Unavailable'
  const result = new Date(value)
  return Number.isNaN(result.getTime()) ? 'Unavailable' : result.toLocaleString()
}

function ResourceState({ error, children }) {
  return error ? <span className="resource-unavailable">{error}</span> : children
}

function attentionTone(level) {
  return level === 'HIGH' ? 'high' : level === 'NOTABLE' ? 'notable' : level === 'MILD' ? 'mild' : 'quiet'
}

export default function StockDetailsPage({ stockId, onBack, onUnauthorized }) {
  const [stock, setStock] = useState(null)
  const [market, setMarket] = useState(null)
  const [state, setState] = useState(null)
  const [changes, setChanges] = useState(null)
  const [attention, setAttention] = useState(null)
  const [resourceErrors, setResourceErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [checkError, setCheckError] = useState(null)

  const loadDetails = useCallback(async () => {
    setLoading(true)
    setResourceErrors({})
    const requests = [
      ['stock', getStock(stockId)],
      ['market', getMarketData(stockId)],
      ['state', getStockState(stockId)],
      ['changes', getStockChanges(stockId)],
      ['attention', getStockAttention(stockId)],
    ]
    const results = await Promise.all(requests.map(async ([key, request]) => {
      try {
        return [key, { value: await request }]
      } catch (error) {
        if (error.status === 401 || error.status === 403) onUnauthorized()
        return [key, { error: error.status === 404 ? 'Unavailable' : 'Data unavailable' }]
      }
    }))
    const resources = Object.fromEntries(results)
    setStock(resources.stock?.value || null)
    setMarket(resources.market?.value || null)
    setState(resources.state?.value || null)
    setChanges(resources.changes?.value || null)
    setAttention(resources.attention?.value || null)
    setResourceErrors(Object.fromEntries(results.filter(([, result]) => result.error).map(([key, result]) => [key, result.error])))
    setLoading(false)
  }, [stockId, onUnauthorized])

  useEffect(() => {
    const timer = setTimeout(() => { loadDetails() }, 0)
    return () => clearTimeout(timer)
  }, [loadDetails])

  async function handleCheck() {
    setChecking(true)
    setCheckError(null)
    try {
      await checkStock(stockId)
      await loadDetails()
    } catch (error) {
      if (error.status === 401 || error.status === 403) onUnauthorized()
      else setCheckError(error.status === 404 ? 'Market data is currently unavailable.' : 'Unable to check this stock. Please try again.')
    } finally {
      setChecking(false)
    }
  }

  const noBaseline = changes?.status === 'NO_BASELINE' || resourceErrors.state === 'Unavailable'
  const noNewData = changes?.status === 'NO_NEW_DATA'
  const attentionToneClass = attentionTone(attention?.attention_level)
  const checkMessage = noBaseline ? "You haven't checked this stock yet." : null
  const identity = useMemo(() => stock || changes || {}, [stock, changes])

  if (loading) return <main className="dashboard-content stock-details-content"><div className="skeleton stock-hero-skeleton" /><div className="stock-details-grid"><div className="skeleton stock-panel-skeleton" /><div className="skeleton stock-panel-skeleton" /></div></main>
  if (!stock && resourceErrors.stock === 'Unavailable') return <main className="dashboard-content stock-details-content"><button className="back-link" type="button" onClick={onBack}>← Back</button><div className="watchlist-message"><h2>Stock not found.</h2></div></main>

  return <main className="dashboard-content stock-details-content"><button className="back-link" type="button" onClick={onBack}>← Back</button><section className="stock-identity"><div><span className="eyebrow">Stock details</span><h1>{identity.symbol || 'Stock'}</h1><p className="stock-subtitle">{stock?.company_name || 'Company information unavailable'}{stock?.exchange ? ` · ${stock.exchange}` : ''}</p></div><span className="stock-active">{stock?.is_active === false ? 'Inactive' : 'Active'}</span></section>{checkMessage && <div className="baseline-callout"><div><strong>{checkMessage}</strong><span>Check this stock to establish a baseline.</span></div><button className="check-stock-button" type="button" disabled={checking} onClick={handleCheck}>{checking ? 'Checking...' : 'Check stock'}</button></div>}{checkError && <p className="form-error stock-error">{checkError}</p>}<section className="current-market-panel panel"><div className="panel-heading"><div><span className="eyebrow">Current market</span><h2>Latest available data</h2></div></div><div className="market-values"><div><span>Current price</span><strong>{number(market?.close)}</strong></div><div><span>Open</span><strong>{number(market?.open)}</strong></div><div><span>High</span><strong>{number(market?.high)}</strong></div><div><span>Low</span><strong>{number(market?.low)}</strong></div><div><span>Volume</span><strong>{valueOrUnavailable(market?.volume, (item) => Number(item).toLocaleString())}</strong></div><div><span>Timestamp</span><strong>{date(market?.timestamp)}</strong></div></div><ResourceState error={resourceErrors.market && 'Market data is currently unavailable.'}>{null}</ResourceState></section><div className="stock-details-grid"><section className="panel detail-info-panel"><div className="panel-heading"><div><span className="eyebrow">Since you last checked</span><h2>Change data</h2></div></div><div className="info-grid"><div><span>Reference price</span><strong>{number(changes?.reference_price)}</strong></div><div><span>Current price</span><strong>{number(changes?.current_price)}</strong></div><div><span>Price change</span><strong>{noNewData ? 'Unavailable' : number(changes?.price_change)}</strong></div><div><span>Percentage</span><strong>{noNewData ? 'Unavailable' : percent(changes?.price_change_percent)}</strong></div><div><span>Direction</span><strong>{changes?.direction || 'Unavailable'}</strong></div><div><span>Reference time</span><strong>{date(changes?.reference_timestamp)}</strong></div><div><span>Current time</span><strong>{date(changes?.current_timestamp)}</strong></div><div><span>Status</span><strong>{changes?.status || 'Unavailable'}</strong></div></div><ResourceState error={resourceErrors.changes && 'Change data unavailable.'}>{null}</ResourceState></section><section className="panel attention-panel"><div className="panel-heading"><div><span className="eyebrow">Why it matters</span><h2>Attention</h2></div></div>{attention ? <><div className="attention-hero"><strong>{attention.attention_score}</strong><span className={`attention-badge ${attentionToneClass}`}>{attention.attention_level.replaceAll('_', ' ')}</span></div><p className="attention-reason">{attention.reason}</p><div className="info-grid compact"><div><span>Volume change</span><strong>{percent(attention.volume_change_percent)}</strong></div><div><span>Important level</span><strong>{attention.important_level_crossed ? 'Yes' : 'No'}</strong></div><div><span>Sustained movement</span><strong>{attention.sustained_movement ? 'Yes' : 'No'}</strong></div></div></> : <p className="resource-unavailable">Attention data unavailable.</p>}</section></div><section className="panel state-panel"><div className="panel-heading"><div><span className="eyebrow">User state</span><h2>Last checked</h2></div></div>{state ? <div className="info-grid"><div><span>Reference price</span><strong>{number(state.reference_price)}</strong></div><div><span>Reference time</span><strong>{date(state.reference_timestamp)}</strong></div><div><span>Last checked at</span><strong>{date(state.last_checked_at)}</strong></div></div> : <p className="resource-unavailable">You have not established a baseline for this stock.</p>}</section></main>
}
