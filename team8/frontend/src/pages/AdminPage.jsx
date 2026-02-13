import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import HeaderBar from '../components/HeaderBar'
import { useAuth } from '../hooks/useAuth'
import {
  fetchPendingPosts,
  fetchPendingMedia,
  approvePost,
  rejectPost,
  approveMedia,
  rejectMedia,
  fetchReports,
} from '../api/queries'
import { timeAgo } from '../utils/format'

function AdminPage() {
  const { user, isAuthenticated } = useAuth()
  const nav = useNavigate()
  const queryClient = useQueryClient()

  const postsQ = useQuery({ queryKey: ['moderation', 'posts'], queryFn: fetchPendingPosts, enabled: isAuthenticated && user?.is_admin })
  const mediaQ = useQuery({ queryKey: ['moderation', 'media'], queryFn: fetchPendingMedia, enabled: isAuthenticated && user?.is_admin })
  const reportsQ = useQuery({ queryKey: ['reports'], queryFn: fetchReports, enabled: isAuthenticated && user?.is_admin })

  const approvePostMut = useMutation({
    mutationFn: (id) => approvePost(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['moderation', 'posts'] }),
  })
  const rejectPostMut = useMutation({
    mutationFn: ({ id, reason }) => rejectPost(id, reason),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['moderation', 'posts'] }),
  })

  const approveMediaMut = useMutation({
    mutationFn: (id) => approveMedia(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation', 'media'] })
      queryClient.invalidateQueries({ queryKey: ['moderation', 'posts'] })
    },
  })
  const rejectMediaMut = useMutation({
    mutationFn: ({ id, reason }) => rejectMedia(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation', 'media'] })
      queryClient.invalidateQueries({ queryKey: ['moderation', 'posts'] })
    },
  })

  if (!isAuthenticated || !user?.is_admin) {
    nav('/')
    return null
  }

  return (
    <div className="shell">
      <HeaderBar hideAdminLink />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10 }}>
        <Link className="btn btn-ghost" to="/">بازگشت به صفحه اصلی</Link>
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 14 }}>
        <section className="card">
          <SectionTitle title="پست‌های منتظر بررسی" />
          {postsQ.isLoading && <div className="empty">در حال بارگذاری...</div>}
          {!postsQ.isLoading && (!postsQ.data || postsQ.data.length === 0) && <div className="empty">موردی نیست.</div>}
          <div className="grid" style={{ gap: 10 }}>
            {postsQ.data?.map((p) => (
              <div key={p.post_id} className="card" style={{ background: '#1c2f4b' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontWeight: 700 }}>{p.username}</div>
                  <div className="pill-ghost">{timeAgo(p.created_at)}</div>
                </div>
                <p style={{ margin: '8px 0', color: '#dbe6f5', lineHeight: 1.7 }}>{p.content}</p>
                {p.media && <span className="pill-ghost">رسانه پیوست دارد</span>}
                <div className="list-inline" style={{ marginTop: 8 }}>
                  <button className="btn btn-primary" onClick={() => approvePostMut.mutate(p.post_id)} disabled={approvePostMut.isLoading}>
                    تایید
                  </button>
                  <button
                    className="btn btn-ghost"
                    onClick={() => {
                      const reason = window.prompt('دلیل رد؟', 'Rejected by admin')
                      if (reason !== null) rejectPostMut.mutate({ id: p.post_id, reason })
                    }}
                    disabled={rejectPostMut.isLoading}
                  >
                    رد
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <SectionTitle title="رسانه‌های منتظر بررسی" />
          {mediaQ.isLoading && <div className="empty">در حال بارگذاری...</div>}
          {!mediaQ.isLoading && (!mediaQ.data || mediaQ.data.length === 0) && <div className="empty">موردی نیست.</div>}
          <div className="grid" style={{ gap: 10 }}>
            {mediaQ.data?.map((m) => (
              <div key={m.media_id} className="card" style={{ background: '#1c2f4b' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontWeight: 700 }}>{m.username}</div>
                  <div className="pill-ghost">{timeAgo(m.created_at)}</div>
                </div>
                <img src={m.url} alt="media" style={{ width: '100%', maxHeight: 240, objectFit: 'cover', marginTop: 6 }} />
                <div className="list-inline" style={{ marginTop: 8 }}>
                  <button className="btn btn-primary" onClick={() => approveMediaMut.mutate(m.media_id)} disabled={approveMediaMut.isLoading}>
                    تایید
                  </button>
                  <button
                    className="btn btn-ghost"
                    onClick={() => {
                      const reason = window.prompt('دلیل رد؟', 'Rejected by admin')
                      if (reason !== null) rejectMediaMut.mutate({ id: m.media_id, reason })
                    }}
                    disabled={rejectMediaMut.isLoading}
                  >
                    رد
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <SectionTitle title="گزارش‌های کاربران" />
          {reportsQ.isLoading && <div className="empty">در حال بارگذاری...</div>}
          {!reportsQ.isLoading && (!reportsQ.data || reportsQ.data.length === 0) && <div className="empty">گزارشی نیست.</div>}
          <div className="grid" style={{ gap: 10 }}>
            {reportsQ.data?.map((r) => (
              <div key={r.report_id} className="card" style={{ background: '#1c2f4b' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontWeight: 700 }}>گزارش #{r.report_id}</div>
                  <div className="pill-ghost">{timeAgo(r.created_at)}</div>
                </div>
                <div className="pill-ghost" style={{ marginTop: 6 }}>
                  نوع: {r.target_type === 'POST' ? 'پست' : 'رسانه'}
                </div>
                <p style={{ margin: '8px 0', color: '#dbe6f5', lineHeight: 1.7 }}>{r.reason}</p>
                {r.reported_post && <div className="pill-ghost">پست: {r.reported_post}</div>}
                {r.reported_media && <div className="pill-ghost">رسانه: {r.reported_media}</div>}
                <div className="pill-ghost" style={{ marginTop: 6 }}>وضعیت: {r.status || 'OPEN'}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function SectionTitle({ title }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <div style={{ width: 8, height: 8, borderRadius: 999, background: 'linear-gradient(120deg, #4ac29a, #f7c948)' }} />
      <div style={{ fontWeight: 800 }}>{title}</div>
    </div>
  )
}

export default AdminPage
