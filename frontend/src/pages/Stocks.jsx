import { useEffect, useState } from 'react'
import { getStocks } from '../services/stocks'

export default function Stocks({ onNavigate, onUnauthorized }) {
  const [stocks, setStocks] = useState(null)
  const [error, setError] = useState(null)
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    const loadStocks = async () => {
      setError(null)
      try {
        const data = await getStocks()
        setStocks(data)
      } catch (err) {
        if (err.status === 401 || err.status === 403) {
          onUnauthorized()
        } else {
          setError('Unable to load stocks.')
        }
      }
    }
    loadStocks()
  }, [onUnauthorized, retryKey])

  if (error) {
    return (
      <main className="dashboard-content stocks-content">
        <div className="stocks-heading">
          <div>
            <span className="eyebrow">Available stocks</span>
            <h1>Stocks</h1>
            <p className="muted">Browse the stock catalogue</p>
          </div>
        </div>
        <div className="message-shell">
          <div className="message-card">
            <span className="message-icon">!</span>
            <h2>Unable to load stocks</h2>
            <p>{error}</p>
            <button
              className="primary-button"
              type="button"
              onClick={() => {
                setError(null)
                setStocks(null)
                setRetryKey((key) => key + 1)
              }}
            >
              Retry <span>↻</span>
            </button>
          </div>
        </div>
      </main>
    )
  }

  if (stocks === null) {
    return (
      <main className="dashboard-content stocks-content">
        <div className="stocks-heading">
          <div>
            <span className="eyebrow">Available stocks</span>
            <h1>Stocks</h1>
            <p className="muted">Browse the stock catalogue</p>
          </div>
        </div>
        <div className="stocks-list">
          <div className="skeleton stock-row-skeleton" />
          <div className="skeleton stock-row-skeleton" />
          <div className="skeleton stock-row-skeleton" />
          <div className="skeleton stock-row-skeleton" />
        </div>
      </main>
    )
  }

  if (stocks.length === 0) {
    return (
      <main className="dashboard-content stocks-content">
        <div className="stocks-heading">
          <div>
            <span className="eyebrow">Available stocks</span>
            <h1>Stocks</h1>
            <p className="muted">Browse the stock catalogue</p>
          </div>
        </div>
        <div className="watchlist-empty">
          <h2>No stocks available</h2>
          <p>The stock catalogue is currently empty.</p>
        </div>
      </main>
    )
  }

  return (
    <main className="dashboard-content stocks-content">
      <div className="stocks-heading">
        <div>
          <span className="eyebrow">Available stocks</span>
          <h1>Stocks</h1>
          <p className="muted">Browse the stock catalogue</p>
        </div>
      </div>
      <div className="stocks-list">
        {stocks.map((stock) => (
          <button
            key={stock.id}
            className="stock-row"
            type="button"
            onClick={() => onNavigate(`/stocks/${stock.id}`)}
          >
            <div className="stock-row-content">
              <strong className="stock-company">{stock.company_name}</strong>
              <div className="stock-details">
                <span className="stock-symbol">{stock.symbol}</span>
                <span className="stock-exchange">{stock.exchange || 'N/A'}</span>
              </div>
            </div>
            <span className="stock-arrow">→</span>
          </button>
        ))}
      </div>
    </main>
  )
}
