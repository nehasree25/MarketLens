import { useCallback, useEffect, useMemo, useState } from 'react'
import { checkStock, getMarketData, getStock, getStockChanges, getStockState, getStockAttention } from '../services/stocks'

const value = (item, format = String) => item === null || item === undefined ? 'Unavailable' : format(item)
const number = (item) => value(item, (current) => Number(current).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
const percent = (item) => value(item, (current) => `${current > 0 ? '+' : ''}${Number(current).toFixed(2)}%`)
const timestamp = (item) => { if (!item) return 'Unavailable'; const date = new Date(item); return Number.isNaN(date.getTime()) ? 'Unavailable' : date.toLocaleString() }
const tone = (level) => level === 'HIGH' ? 'high' : level === 'NOTABLE' ? 'notable' : level === 'MILD' ? 'mild' : 'quiet'

function ResourceUnavailable({ message }) { return <p className="resource-unavailable">{message}</p> }

function UpdateBaselineDialog({ checking, onCancel, onConfirm }) {
  return <div className="dialog-backdrop" role="presentation"><div className="dialog baseline-dialog" role="dialog" aria-modal="true" aria-labelledby="baseline-dialog-title"><span className="message-icon">↻</span><h2 id="baseline-dialog-title">Update baseline?</h2><p>Your current &quot;Since You Last Checked&quot; reference will be replaced with the latest available market data.</p><div className="dialog-actions"><button className="secondary-button" type="button" onClick={onCancel} disabled={checking}>Cancel</button><button className="primary-button" type="button" onClick={onConfirm} disabled={checking}>{checking ? 'Checking...' : 'Update baseline'}<span>→</span></button></div></div></div>
}

export default function StockDetailsPage({ stockId, onBack, onUnauthorized }) {
  const [resources, setResources] = useState({})
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [checkError, setCheckError] = useState(null)
  const [checkSuccess, setCheckSuccess] = useState(null)
  const [confirmUpdate, setConfirmUpdate] = useState(false)

  const loadDetails = useCallback(async () => {
    setLoading(true)
    setErrors({})
    // Request endpoints needed for display
    const requests = [
      ['stock', getStock(stockId)],
      ['market', getMarketData(stockId)],
      ['state', getStockState(stockId)],
      ['changes', getStockChanges(stockId)],
      ['attention', getStockAttention(stockId)],
    ]
    const results = await Promise.all(requests.map(async ([key, request]) => {
      try { return [key, { value: await request }] } catch (error) {
        if (error.status === 401 || error.status === 403) onUnauthorized()
        return [key, { error: error.status === 404 ? 'Resource unavailable' : 'Data unavailable' }]
      }
    }))
    setResources(Object.fromEntries(results.map(([key, result]) => [key, result.value])))
    setErrors(Object.fromEntries(results.filter(([, result]) => result.error).map(([key, result]) => [key, result.error])))
    setLoading(false)
  }, [stockId, onUnauthorized])

  useEffect(() => { const timer = setTimeout(() => loadDetails(), 0); return () => clearTimeout(timer) }, [loadDetails])

  async function handleCheck() {
    setChecking(true)
    setCheckError(null)
    setCheckSuccess(null)
    try {
      const result = await checkStock(stockId)
      setConfirmUpdate(false)
      setCheckSuccess(result.message || 'Baseline updated.')
      await loadDetails()
    } catch (error) {
      if (error.status === 401 || error.status === 403) onUnauthorized()
      else if (error.status === 404 || error.status === 503) setCheckError('Market data is currently unavailable. Please try again when market data is available.')
      else setCheckError('Unable to check this stock. Please try again.')
    } finally { setChecking(false) }
  }

  const stock = resources.stock
  const market = resources.market
  const state = resources.state
  const changes = resources.changes
  const attentionData = resources.attention
  // Use attention data from dedicated attention endpoint
  const attention = attentionData ? {
    attention_score: attentionData.attention_score,
    attention_level: attentionData.attention_level,
    volume_change_percent: attentionData.volume_change_percent,
    important_level_crossed: attentionData.important_level_crossed,
    sustained_movement: attentionData.sustained_movement,
    reason: attentionData.reason,
  } : null
  const noBaseline = changes?.status === 'NO_BASELINE' || state === null
  const noNewData = changes?.status === 'NO_NEW_DATA'
  const identity = useMemo(() => stock || changes || {}, [stock, changes])

  if (loading) return <main className="dashboard-content stock-details-content"><div className="skeleton stock-hero-skeleton" /><div className="stock-details-grid"><div className="skeleton stock-panel-skeleton" /><div className="skeleton stock-panel-skeleton" /></div></main>
  if (!stock && errors.stock === 'Unavailable') return <main className="dashboard-content stock-details-content"><button className="back-link" type="button" onClick={onBack}>← Back</button><div className="watchlist-message"><h2>Stock not found.</h2></div></main>

  return <main className="dashboard-content stock-details-content"><button className="back-link" type="button" onClick={onBack}>← Back</button><section className="stock-identity"><div><span className="eyebrow">Stock details</span><h1>{identity?.symbol || 'Stock'}</h1><p className="stock-subtitle">{stock?.company_name || 'Company information unavailable'}{stock?.exchange ? ` · ${stock.exchange}` : ''}</p></div><span className="stock-active">{stock?.is_active === false ? 'Inactive' : 'Active'}</span></section>{noBaseline ? <div className="baseline-callout"><div><strong>Start tracking this stock</strong><span>Check this stock to establish your reference point. MarketLens will then show you what has meaningfully changed since you last checked.</span></div><button className="check-stock-button" type="button" disabled={checking} onClick={handleCheck}>{checking ? 'Checking...' : 'Check stock'}</button></div> : <div className="baseline-update-row"><span>Update your reference point with the latest available market snapshot.</span><button className="check-stock-button" type="button" disabled={checking} onClick={() => setConfirmUpdate(true)}>{checking ? 'Checking...' : 'Check stock again'}</button></div>}{checkSuccess && <p className="check-success">{checkSuccess}</p>}{checkError && <p className="form-error stock-error">{checkError}</p>}<section className="current-market-panel panel"><div className="panel-heading"><div><span className="eyebrow">Current market</span><h2>Latest available data</h2></div></div><div className="market-values"><div><span>Current price</span><strong>{number(market?.close)}</strong></div><div><span>Open</span><strong>{number(market?.open)}</strong></div><div><span>High</span><strong>{number(market?.high)}</strong></div><div><span>Low</span><strong>{number(market?.low)}</strong></div><div><span>Volume</span><strong>{value(market?.volume, (item) => Number(item).toLocaleString())}</strong></div><div><span>Timestamp</span><strong>{timestamp(market?.timestamp)}</strong></div></div>{errors.market && <ResourceUnavailable message="Market data is currently unavailable." />}</section><div className="stock-details-grid"><section className="panel detail-info-panel"><div className="panel-heading"><div><span className="eyebrow">Since you last checked</span><h2>Change data</h2></div></div>{changes ? <div className="info-grid"><div><span>Reference price</span><strong>{number(changes.reference_price)}</strong></div><div><span>Current price</span><strong>{number(changes.current_price)}</strong></div><div><span>Price change</span><strong>{noNewData ? 'Unavailable' : number(changes.price_change)}</strong></div><div><span>Percentage</span><strong>{noNewData ? 'Unavailable' : percent(changes.price_change_percent)}</strong></div><div><span>Direction</span><strong>{changes.direction || 'Unavailable'}</strong></div><div><span>Reference time</span><strong>{timestamp(changes.reference_timestamp)}</strong></div><div><span>Current time</span><strong>{timestamp(changes.current_timestamp)}</strong></div><div><span>Status</span><strong>{changes.status}</strong></div></div> : <ResourceUnavailable message="Change data unavailable." />}</section><section className="panel attention-panel"><div className="panel-heading"><div><span className="eyebrow">Why it matters</span><h2>Attention</h2></div></div>{attention ? <><div className="attention-hero"><span className={`attention-badge ${tone(attention.attention_level)}`}>{attention.attention_level.replaceAll('_', ' ')}</span></div><p className="attention-reason">{attention.reason}</p><div className="info-grid compact"><div><span>Volume change</span><strong>{percent(attention.volume_change_percent)}</strong></div><div><span>Important level</span><strong>{attention.important_level_crossed ? 'Yes' : 'No'}</strong></div><div><span>Sustained movement</span><strong>{attention.sustained_movement ? 'Yes' : 'No'}</strong></div></div></> : <ResourceUnavailable message="Attention data unavailable." />}</section></div><section className="panel state-panel"><div className="panel-heading"><div><span className="eyebrow">User state</span><h2>Last checked</h2></div></div>{state ? <div className="info-grid"><div><span>Reference price</span><strong>{number(state.reference_price)}</strong></div><div><span>Reference time</span><strong>{timestamp(state.reference_timestamp)}</strong></div><div><span>Last checked at</span><strong>{timestamp(state.last_checked_at)}</strong></div></div> : <ResourceUnavailable message="You have not established a baseline for this stock." />}</section>{confirmUpdate && <UpdateBaselineDialog checking={checking} onCancel={() => setConfirmUpdate(false)} onConfirm={handleCheck} />}</main>
}
