function display(value, format = String) {
  return value === null || value === undefined ? 'Unavailable' : format(value)
}

function formatPrice(value) {
  return display(value, (item) => Number(item).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
}

function formatNumber(value) {
  return display(value, (item) => `${item > 0 ? '+' : ''}${Number(item).toFixed(2)}`)
}

function formatPercent(value) {
  return display(value, (item) => `${item > 0 ? '+' : ''}${Number(item).toFixed(2)}%`)
}

function levelTone(level) {
  return level === 'HIGH' ? 'high' : level === 'NOTABLE' ? 'notable' : level === 'MILD' ? 'mild' : 'quiet'
}

export default function StockChangeCard({ change, companyName, exchange, onCheck, checking, onRemove, onOpen }) {
  const tone = levelTone(change.attention_level)
  const noChange = change.status === 'NO_NEW_DATA' || change.status === 'NO_MARKET_DATA'
  return <article className="change-card"><div className="change-card-header"><div><button className="stock-symbol-link" type="button" onClick={() => onOpen(change.stock_id)}>{change.symbol}</button><span>{companyName || exchange || 'Stock'}</span></div><div className="attention-score"><strong>{change.attention_score}</strong><span className={`attention-badge ${tone}`}>{change.attention_level.replaceAll('_', ' ')}</span></div></div><div className="change-price"><strong>{formatPrice(change.current_price)}</strong><div className="change-metrics"><span className={change.direction === 'DOWN' ? 'negative' : change.direction === 'UP' ? 'positive' : ''}>{noChange || change.price_change === null || change.price_change === undefined ? 'No new data' : formatNumber(change.price_change)}</span><span className={change.direction === 'DOWN' ? 'negative' : change.direction === 'UP' ? 'positive' : ''}>{noChange || change.price_change_percent === null || change.price_change_percent === undefined ? 'No new data' : formatPercent(change.price_change_percent)}</span><span className={`direction ${change.direction?.toLowerCase() || 'unchanged'}`}>{change.direction || 'UNCHANGED'}</span></div></div><p className="change-reason">{change.reason}</p><div className="change-factors"><span>Volume <strong>{formatPercent(change.volume_change_percent)}</strong></span><span>Level crossed <strong>{change.important_level_crossed ? 'Yes' : 'No'}</strong></span><span>Sustained <strong>{change.sustained_movement ? 'Yes' : 'No'}</strong></span></div><div className="change-card-footer"><span className={`status-pill ${change.status.toLowerCase()}`}>{change.status.replaceAll('_', ' ')}</span><div className="change-actions">{change.status === 'NO_BASELINE' && <button className="check-stock-button" type="button" disabled={checking} onClick={() => onCheck(change.stock_id)}>{checking ? 'Checking...' : 'Check stock'}</button>}<button className="remove-stock-button" type="button" onClick={() => onRemove({ id: change.stock_id, symbol: change.symbol })}>Remove</button></div></div></article>
}
