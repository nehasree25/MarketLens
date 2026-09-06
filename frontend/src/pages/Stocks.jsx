import { useEffect, useState } from 'react'
import { getStocks } from '../services/stocks'

export default function Stocks({ onNavigate, onUnauthorized }) {
  const [response, setResponse] = useState(null)
  const [stocks, setStocks] = useState([])
  const [pagination, setPagination] = useState(null)
  const [error, setError] = useState(null)
  const [retryKey, setRetryKey] = useState(0)
  const [currentPage, setCurrentPage] = useState(0)
  const pageSize = 5

  useEffect(() => {
    const loadStocks = async () => {
      setError(null)
      try {
        const data = await getStocks(currentPage * pageSize, pageSize)
        setResponse(data)
        setStocks(data.data || [])
        setPagination(data.pagination || null)
      } catch (err) {
        if (err.status === 401 || err.status === 403) {
          onUnauthorized()
        } else {
          setError('Unable to load stocks.')
        }
      }
    }
    loadStocks()
  }, [onUnauthorized, retryKey, currentPage])

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
                setResponse(null)
                setStocks([])
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

  if (response === null) {
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
      {pagination && (
        <div className="pagination-controls">
          <button
            type="button"
            className="pagination-button"
            onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
            disabled={currentPage === 0}
          >
            ← Previous
          </button>
          <span className="pagination-info">
            Page {currentPage + 1} of {Math.ceil(pagination.total / pageSize)} ({pagination.total} stocks)
          </span>
          <button
            type="button"
            className="pagination-button"
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={!pagination.has_more}
          >
            Next →
          </button>
        </div>
      )}
    </main>
  )
}

