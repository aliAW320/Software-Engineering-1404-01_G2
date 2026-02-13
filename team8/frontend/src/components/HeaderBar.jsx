import { useState } from 'react'
import AuthModal from './auth/AuthModal'
import { useAuth } from '../hooks/useAuth'
import NotificationPanel from './notifications/NotificationPanel'
import { useQuery } from '@tanstack/react-query'
import { fetchUnreadCount } from '../api/queries'

function HeaderBar({ onShowAuth, hideAdminLink = false }) {
  const { user, isAuthenticated, logout } = useAuth()
  const [authOpen, setAuthOpen] = useState(false)
  const [mode, setMode] = useState('login')
  const [notifOpen, setNotifOpen] = useState(false)

  const unreadQuery = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: fetchUnreadCount,
    enabled: isAuthenticated,
    staleTime: 30000,
  })

  const openAuth = (m) => {
    if (onShowAuth) {
      onShowAuth(m)
    } else {
      setMode(m)
      setAuthOpen(true)
    }
  }

  return (
    <>
      <header className="glass" style={{ padding: 16, marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, #4ac29a, #f7c948)', boxShadow: '0 10px 30px rgba(0,0,0,0.35)' }} />
          <div>
            <div style={{ fontWeight: 800, letterSpacing: 0.4 }}>سامانه گردشگری تیم ۸</div>
            <div style={{ color: '#9fb4d3', fontSize: 13 }}>نظرات، رسانه، امتیازدهی</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isAuthenticated && user?.is_admin && !hideAdminLink && (
            <a className="btn btn-ghost" href="/admin">
              بخش ادمین
            </a>
          )}
          {!isAuthenticated ? (
            <>
              <button className="btn btn-ghost" onClick={() => openAuth('login')}>
                ورود
              </button>
              <button className="btn btn-primary" onClick={() => openAuth('register')}>
                ثبت‌نام
              </button>
            </>
          ) : (
            <>
              <button className="btn btn-ghost" onClick={() => setNotifOpen(true)} style={{ position: 'relative' }}>
                🔔
                {unreadQuery.data?.unread > 0 && (
                  <span style={{
                    position: 'absolute',
                    top: -4,
                    right: -4,
                    background: '#f7c948',
                    color: '#0f1b2d',
                    borderRadius: 999,
                    padding: '2px 6px',
                    fontSize: 11,
                    fontWeight: 800,
                  }}>
                    {unreadQuery.data.unread}
                  </span>
                )}
              </button>
              <div className="pill-ghost" onClick={() => setNotifOpen(true)} style={{ cursor: 'pointer' }}>
                {user?.username || [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email}
              </div>
              <button className="btn btn-ghost" onClick={logout}>
                خروج
              </button>
            </>
          )}
        </div>
      </header>

      {!onShowAuth && authOpen && <AuthModal mode={mode} onClose={() => setAuthOpen(false)} />}
      {notifOpen && <NotificationPanel onClose={() => setNotifOpen(false)} />}
    </>
  )
}

export default HeaderBar
