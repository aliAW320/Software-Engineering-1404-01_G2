import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '../../api/queries'
import { timeAgo } from '../../utils/format'

function NotificationPanel({ onClose }) {
  const queryClient = useQueryClient()
  const panelRef = useRef(null)

  const notifQuery = useQuery({ queryKey: ['notifications'], queryFn: fetchNotifications })
  const unreadQuery = useQuery({ queryKey: ['notifications', 'unread'], queryFn: fetchUnreadCount })

  const markOne = useMutation({
    mutationFn: (id) => markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread'] })
    },
  })

  const markAll = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread'] })
    },
  })

  useEffect(() => {
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        onClose?.()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(5,10,20,0.45)', zIndex: 40, display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
      <div
        ref={panelRef}
        className="glass"
        style={{ width: 'min(640px, 100%)', maxHeight: '80vh', overflow: 'auto', padding: 16, borderRadius: 18 }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ fontWeight: 800, fontSize: 18 }}>اعلان‌ها</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" onClick={() => markAll.mutate()} disabled={markAll.isLoading}>
              خواندن همه
            </button>
            <button className="btn btn-ghost" onClick={onClose}>بستن</button>
          </div>
        </div>

        {notifQuery.isLoading && <div className="empty">در حال بارگذاری...</div>}
        {!notifQuery.isLoading && (!notifQuery.data || notifQuery.data.length === 0) && (
          <div className="empty">اعلانی ندارید.</div>
        )}

        <div className="grid" style={{ gap: 10 }}>
          {(Array.isArray(notifQuery.data) ? notifQuery.data : []).map((n) => (
            <div
              key={n.notification_id}
              className="card"
              style={{
                background: n.is_read ? '#15263f' : 'linear-gradient(135deg, #183457, #1f416b)',
                borderColor: n.is_read ? 'var(--border)' : 'rgba(74,194,154,0.6)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <div style={{ fontWeight: 700 }}>{n.title}</div>
                <div className="pill-ghost">{timeAgo(n.created_at)}</div>
              </div>
              <p style={{ margin: '8px 0', color: '#dbe6f5', lineHeight: 1.6 }}>{n.message}</p>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                {!n.is_read && (
                  <button
                    className="btn btn-primary"
                    onClick={() => markOne.mutate(n.notification_id)}
                    disabled={markOne.isLoading}
                    style={{ padding: '8px 12px' }}
                  >
                    علامت خوانده شد
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default NotificationPanel
