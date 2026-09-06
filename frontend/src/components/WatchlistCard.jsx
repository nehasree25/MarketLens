function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function WatchlistCard({ watchlist, onOpen, onRename, onDelete }) {
  return <article className="watchlist-card"><div className="watchlist-card-top"><span className="watchlist-symbol">WL</span><span className="watchlist-date">Created {formatDate(watchlist.created_at)}</span></div><h2>{watchlist.name}</h2><p className="watchlist-count">{watchlist.stocks?.length ?? 0} {watchlist.stocks?.length === 1 ? 'stock' : 'stocks'}</p><div className="watchlist-actions"><button className="watchlist-open" type="button" onClick={() => onOpen(watchlist.id)}>Open <span>→</span></button><button type="button" onClick={() => onRename(watchlist)}>Rename</button><button className="danger-action" type="button" onClick={() => onDelete(watchlist)}>Delete</button></div></article>
}
