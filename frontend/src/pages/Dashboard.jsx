const categories = [
  ['high_attention', 'High attention', 'high'],
  ['notable', 'Notable', 'notable'],
  ['mild', 'Mild', 'mild'],
  ['no_notable_change', 'No notable change', 'quiet'],
]

const display = (value, format = String) => value === null || value === undefined ? 'Unavailable' : format(value)
const price = (value) => display(value, (item) => Number(item).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))
const percent = (value) => display(value, (item) => `${item > 0 ? '+' : ''}${Number(item).toFixed(2)}%`)

function Badge({ level }) {
  const tone = level === 'HIGH' ? 'high' : level === 'NOTABLE' ? 'notable' : level === 'MILD' ? 'mild' : 'quiet'
  return <span className={`attention-badge ${tone}`}>{level?.replaceAll('_', ' ') || 'Unavailable'}</span>
}

function Summary({ data }) {
  return <section className="panel summary-panel"><div className="panel-heading"><div><span className="eyebrow">Portfolio signal</span><h2>Your watchlist</h2></div><span className="panel-icon">◌</span></div><div className="total-number">{data.total_stocks}</div><p className="muted">Total tracked stocks</p><div className="stat-list">{categories.map(([key, label, tone]) => <div className="stat-row" key={key}><span className={`status-dot ${tone}`} /><span>{label}</span><strong>{data[key]}</strong></div>)}</div></section>
}

function Distribution({ data }) {
  const total = categories.reduce((sum, [key]) => sum + (data[key] || 0), 0)
  let cursor = 0
  const gradient = total ? categories.map(([key, , tone]) => { const start = cursor / total * 100; cursor += data[key] || 0; return `var(--${tone}) ${start}% ${cursor / total * 100}%` }).join(', ') : 'var(--surface-3) 0 100%'
  return <section className="panel distribution-panel"><div className="panel-heading"><div><span className="eyebrow">Signal mix</span><h2>Attention distribution</h2></div><span className="panel-icon">◔</span></div><div className="donut-layout"><div className="donut" style={{ background: `conic-gradient(${gradient})` }}><div className="donut-hole"><strong>{total}</strong><span>stocks</span></div></div><div className="legend">{categories.map(([key, label, tone]) => <div className="legend-row" key={key}><span className={`legend-swatch ${tone}`} /><span>{label}</span><strong>{data[key]}</strong></div>)}</div></div></section>
}

function Movers({ stocks }) {
  const movers = stocks.filter((stock) => stock.price_change_percent !== null && stock.price_change_percent !== undefined).slice(0, 4)
  return <section className="panel movers-panel"><div className="panel-heading"><div><span className="eyebrow">Important changes</span><h2>Top movers</h2></div><span className="panel-icon">↗</span></div>{movers.length ? <div className="mover-list">{movers.map((stock) => <div className="mover-row" key={stock.stock_id}><div><strong>{stock.symbol}</strong><span>{stock.status.replaceAll('_', ' ')}</span></div><strong className={stock.price_change_percent >= 0 ? 'positive' : 'negative'}>{percent(stock.price_change_percent)}</strong></div>)}</div> : <p className="empty-copy">No market movements available.</p>}</section>
}

function StockTable({ stocks }) {
  return <section className="panel stocks-panel"><div className="panel-heading table-heading"><div><span className="eyebrow">Backend-ranked signals</span><h2>Since you last checked</h2></div><span className="live-indicator"><i /> Live summary</span></div>{stocks.length ? <div className="table-scroll"><table><thead><tr><th>Stock</th><th>Current price</th><th>Change</th><th>Attention</th><th>Status</th></tr></thead><tbody>{stocks.map((stock) => <tr key={stock.stock_id}><td><div className="stock-name"><strong>{stock.symbol}</strong><span>{stock.watchlists?.map((item) => item.watchlist_name).join(' · ') || 'Watchlist'}</span></div></td><td className="numeric">{price(stock.current_price)}</td><td className={`${stock.price_change_percent >= 0 ? 'positive' : 'negative'} numeric`}>{percent(stock.price_change_percent)}</td><td><Badge level={stock.attention_level} /></td><td><span className={`status-pill ${stock.status.toLowerCase()}`}>{stock.status.replaceAll('_', ' ')}</span></td></tr>)}</tbody></table></div> : <div className="empty-table"><strong>No stocks in your watchlists yet.</strong><span>Create a watchlist and add stocks to start tracking changes.</span></div>}</section>
}

export default function Dashboard({ data, searchQuery }) {
  const stocks = data?.stocks?.filter((stock) => stock.symbol.toLowerCase().includes(searchQuery.toLowerCase())) || []
  return <><main className="dashboard-content"><div className="welcome-row"><div><span className="eyebrow">Dashboard / Overview</span><h1>Good to see you.</h1><p className="muted">A focused read on the signals that changed since your last check.</p></div><span className="api-chip"><i /> Dashboard API connected</span></div>{data.total_stocks === 0 ? <div className="empty-hero"><h2>No stocks in your watchlists yet.</h2><p>Create a watchlist and add stocks to start tracking changes.</p></div> : <><div className="dashboard-grid"><Summary data={data} /><Distribution data={data} /><Movers stocks={data.stocks} /></div><StockTable stocks={stocks} /></>}</main><footer>MarketLens <span>·</span> Read-only dashboard intelligence</footer></>
}
