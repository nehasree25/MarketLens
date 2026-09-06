import { useCallback, useEffect, useState } from 'react'
import WatchlistCard from '../components/WatchlistCard'
import { createWatchlist, deleteWatchlist, getWatchlists, renameWatchlist } from '../services/watchlists'

function friendlyError(error, fallback) {
  if (error.status === 401 || error.status === 403) return 'Your session may have expired. Please sign in again.'
  if (error.status === 400) return 'Please check the watchlist name and try again.'
  return fallback
}

function WatchlistDialog({ mode, initialName, submitting, error, onClose, onSubmit }) {
  const [name, setName] = useState(initialName || '')
  const title = mode === 'create' ? 'Create watchlist' : 'Rename watchlist'
  const action = mode === 'create' ? 'Create' : 'Save'

  function submit(event) {
    event.preventDefault()
    onSubmit(name.trim())
  }

  return <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="dialog" role="dialog" aria-modal="true" aria-labelledby="watchlist-dialog-title"><div className="dialog-header"><div><span className="eyebrow">Watchlist management</span><h2 id="watchlist-dialog-title">{title}</h2></div><button className="dialog-close" type="button" onClick={onClose} aria-label="Close dialog">×</button></div><form onSubmit={submit}><label className="dialog-label">Name<input autoFocus value={name} onChange={(event) => setName(event.target.value)} maxLength={150} /></label>{error && <p className="form-error">{error}</p>}<div className="dialog-actions"><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting || !name.trim()}>{submitting ? 'Saving…' : action}<span>→</span></button></div></form></div></div>
}

function DeleteDialog({ watchlist, submitting, error, onClose, onConfirm }) {
  return <div className="dialog-backdrop" role="presentation"><div className="dialog delete-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title"><span className="message-icon">!</span><h2 id="delete-dialog-title">Delete watchlist?</h2><p>Are you sure you want to delete <strong>{watchlist.name}</strong>?</p>{error && <p className="form-error">{error}</p>}<div className="dialog-actions"><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="danger-button" type="button" onClick={onConfirm} disabled={submitting}>{submitting ? 'Deleting…' : 'Delete'}</button></div></div></div>
}

function EmptyWatchlists({ onCreate }) {
  return <div className="watchlist-empty"><span className="empty-watchlist-icon">+</span><h2>No watchlists yet.</h2><p>Create your first watchlist to start tracking stocks.</p><button className="primary-button" type="button" onClick={onCreate}>Create watchlist <span>→</span></button></div>
}

export default function Watchlists({ onNavigate, onUnauthorized }) {
  const [watchlists, setWatchlists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dialog, setDialog] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [actionError, setActionError] = useState(null)

  const loadWatchlists = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setWatchlists(await getWatchlists())
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else setError('Unable to load your watchlists.')
    } finally {
      setLoading(false)
    }
  }, [onUnauthorized])

  useEffect(() => {
    const timer = setTimeout(() => { loadWatchlists() }, 0)
    return () => clearTimeout(timer)
  }, [loadWatchlists])

  function openDialog(nextDialog) {
    setActionError(null)
    setDialog(nextDialog)
  }

  async function submitName(name) {
    if (!name) {
      setActionError('Please enter a watchlist name.')
      return
    }
    setSubmitting(true)
    setActionError(null)
    try {
      if (dialog.mode === 'create') {
        const created = await createWatchlist({ name })
        setWatchlists((current) => [...current, created])
      } else {
        const updated = await renameWatchlist(dialog.watchlist.id, { name })
        setWatchlists((current) => current.map((item) => item.id === updated.id ? updated : item))
      }
      setDialog(null)
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else setActionError(friendlyError(requestError, 'Unable to save this watchlist.'))
    } finally {
      setSubmitting(false)
    }
  }

  async function confirmDelete() {
    setSubmitting(true)
    setActionError(null)
    try {
      await deleteWatchlist(dialog.watchlist.id)
      setWatchlists((current) => current.filter((item) => item.id !== dialog.watchlist.id))
      setDialog(null)
    } catch (requestError) {
      if (requestError.status === 401 || requestError.status === 403) onUnauthorized()
      else setActionError(friendlyError(requestError, 'Unable to delete this watchlist.'))
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="dashboard-content watchlists-content"><div className="watchlists-heading"><div><span className="eyebrow">Your workspace</span><h1>My watchlists</h1><p className="muted">Keep the stocks you care about organized.</p></div><button className="primary-button create-watchlist-button" type="button" onClick={() => openDialog({ mode: 'create' })}>+ Create watchlist</button></div>{loading ? <div className="watchlist-grid">{[1, 2, 3, 4].map((item) => <div className="skeleton watchlist-skeleton" key={item} />)}</div> : error ? <div className="watchlist-message"><h2>Unable to load your watchlists.</h2><button className="secondary-button" type="button" onClick={loadWatchlists}>Retry</button></div> : watchlists.length === 0 ? <EmptyWatchlists onCreate={() => openDialog({ mode: 'create' })} /> : <div className="watchlist-grid">{watchlists.map((watchlist) => <WatchlistCard key={watchlist.id} watchlist={watchlist} onOpen={(id) => onNavigate(`/watchlists/${id}`)} onRename={(item) => openDialog({ mode: 'rename', watchlist: item, initialName: item.name })} onDelete={(item) => openDialog({ mode: 'delete', watchlist: item })} />)}</div>}{dialog?.mode === 'create' || dialog?.mode === 'rename' ? <WatchlistDialog mode={dialog.mode} initialName={dialog.initialName} submitting={submitting} error={actionError} onClose={() => setDialog(null)} onSubmit={submitName} /> : null}{dialog?.mode === 'delete' ? <DeleteDialog watchlist={dialog.watchlist} submitting={submitting} error={actionError} onClose={() => setDialog(null)} onConfirm={confirmDelete} /> : null}</main>
}
