import { useState } from 'react'

export default function UserMenu({ user, onLogout }) {
  const [open, setOpen] = useState(false)
  const initial = user?.name?.trim()?.charAt(0)?.toUpperCase() || '?'

  return <div className="user-menu"><button className="profile-button" type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open}><span className="avatar">{initial}</span><span className="profile-copy"><strong>{user?.name || 'User'}</strong><small>{user?.email || 'Authenticated'}</small></span><span className="menu-chevron">⌄</span></button>{open && <div className="user-dropdown"><div className="dropdown-identity"><span className="avatar">{initial}</span><div><strong>{user?.name || 'User'}</strong><small>{user?.email || 'Authenticated'}</small></div></div><button type="button" onClick={onLogout}>Sign out <span>↗</span></button></div>}</div>
}
