import { useMemo, useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import jaLocale from '@fullcalendar/core/locales/ja'
import { useCalendarEvents } from '../hooks/useCalendarEvents'
import { useAuth } from '../context/AuthContext'
import { updateReservation, deleteReservation, requestCancellation, getPendingCount } from '../api/reservations'
import { getVideoUrl } from '../api/systemSettings'

const bufferInDays = 7

const STATUS_LABELS: Record<string, string> = {
  approved: '承認済み',
  pending: '申請中',
  rejected: '却下',
  cancelled: 'キャンセル済み',
  cancellation_requested: 'キャンセル申請中',
}

function getEmbedUrl(url: string): string {
  try {
    let videoId = '';
    if (url.includes('youtu.be/')) {
      videoId = url.split('youtu.be/')[1]?.split('?')[0];
    } else if (url.includes('youtube.com/watch')) {
      const urlParams = new URLSearchParams(new URL(url).search);
      videoId = urlParams.get('v') || '';
    } else if (url.includes('youtube.com/embed/')) {
        return url;
    }

    if (videoId) {
      return `https://www.youtube.com/embed/${videoId}`;
    }
    return url;
  } catch (e) {
    return url;
  }
}

/* ---- Confirm Dialog Component ---- */
function ConfirmDialog({ title, message, confirmLabel, confirmVariant, onConfirm, onCancel, children }: {
  title: string
  message?: string
  confirmLabel: string
  confirmVariant?: string
  onConfirm: () => void
  onCancel: () => void
  children?: React.ReactNode
}) {
  return (
    <div className="confirm-dialog-backdrop" onClick={onCancel}>
      <div className="confirm-dialog" onClick={e => e.stopPropagation()}>
        <h3>{title}</h3>
        {message && <p>{message}</p>}
        {children}
        <div className="confirm-actions">
          <button className="button ghost" onClick={onCancel}>キャンセル</button>
          <button className={`button ${confirmVariant || ''}`} onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  )
}

/* ---- Toast Component ---- */
function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3500)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className={`toast ${type}`}>
      <span>{type === 'success' ? '✓' : '✕'}</span>
      <span>{message}</span>
    </div>
  )
}

export function CalendarPage() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const authFingerprint = user ? `${user.id}-${user.isAdmin ? 'admin' : 'member'}` : 'anonymous'
  const userDisplayName = user?.displayName || user?.display_name || user?.email.split('@')[0] || ''
  
  const [visibilityFilter, setVisibilityFilter] = useState<'all' | 'public' | 'anonymous'>('all')
  const [range, setRange] = useState(() => ({
    start: dayjs().startOf('month').subtract(bufferInDays, 'day').toISOString(),
    end: dayjs().endOf('month').add(bufferInDays, 'day').toISOString(),
  }))
  const [pendingCount, setPendingCount] = useState(0)
  const [videoUrl, setVideoUrl] = useState('')

  // UI state
  const [selectedEvent, setSelectedEvent] = useState<any>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editingDescription, setEditingDescription] = useState('')
  const [editingDisplayMessage, setEditingDisplayMessage] = useState('')
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [videoOpen, setVideoOpen] = useState(() => {
    const stored = localStorage.getItem('kcr-video-open')
    return stored !== 'false' // Default open
  })

  // Confirm / Toast state
  const [confirmState, setConfirmState] = useState<{ title: string; message?: string; confirmLabel: string; confirmVariant?: string; onConfirm: () => void; children?: React.ReactNode } | null>(null)
  const [toasts, setToasts] = useState<{ id: number; message: string; type: 'success' | 'error' }[]>([])
  const toastIdRef = useRef(0)

  const userMenuRef = useRef<HTMLDivElement>(null)

  const addToast = (message: string, type: 'success' | 'error') => {
    const id = ++toastIdRef.current
    setToasts(prev => [...prev, { id, message, type }])
  }

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  // Close user menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const refreshPendingCount = () => {
    if (user?.isAdmin) {
      getPendingCount().then(setPendingCount).catch(console.error)
    }
  }

  useEffect(() => {
    getVideoUrl().then(setVideoUrl).catch(console.error)
  }, [])

  useEffect(() => {
    refreshPendingCount()
    const interval = setInterval(refreshPendingCount, 30000)
    return () => clearInterval(interval)
  }, [user])

  const toggleVideo = () => {
    setVideoOpen(prev => {
      const next = !prev
      localStorage.setItem('kcr-video-open', String(next))
      return next
    })
  }

  const visibilityParam = visibilityFilter === 'all' ? undefined : visibilityFilter

  const { data: events = [], isLoading, isFetching, error, refetch } = useCalendarEvents({
    start: range.start,
    end: range.end,
    visibility: visibilityParam,
    authFingerprint,
  })

  const calendarEvents = useMemo(
    () =>
      events.map((event) => ({
        id: String(event.id),
        title:
          event.title ??
          (event.visibility === 'anonymous' ? t('event.reservedAnonymous') : t('event.reserved')),
        start: event.start ?? undefined,
        end: event.end ?? undefined,
        classNames: ['calendar-event', `status-${event.status}`],
        extendedProps: {
            id: event.id,
            description: event.description,
            displayMessage: event.displayMessage,
            attendeeCount: event.attendeeCount,
            userDisplayName: event.userDisplayName,
            rejectionReason: event.rejectionReason,
            approvalMessage: event.approvalMessage,
            status: event.status,
            visibility: event.visibility,
            isOwner: event.isOwner
        }
      })),
    [events, t],
  )

  const handleEdit = () => {
    setEditingDescription(selectedEvent.extendedProps.description || '')
    setEditingDisplayMessage(selectedEvent.extendedProps.displayMessage || '')
    setIsEditing(true)
  }

  const handleSave = async () => {
    try {
        await updateReservation(selectedEvent.extendedProps.id, {
            description: editingDescription,
            displayMessage: editingDisplayMessage
        })
        setIsEditing(false)
        setSelectedEvent({
            ...selectedEvent,
            extendedProps: {
                ...selectedEvent.extendedProps,
                description: editingDescription,
                displayMessage: editingDisplayMessage
            }
        })
        refetch()
        refreshPendingCount()
        addToast('予約を更新しました', 'success')
    } catch (e) {
        addToast('更新に失敗しました', 'error')
    }
  }

  const handleDelete = () => {
    setConfirmState({
      title: '予約を削除しますか？',
      message: 'この操作は取り消せません。',
      confirmLabel: '削除',
      confirmVariant: 'danger',
      onConfirm: async () => {
        setConfirmState(null)
        try {
          await deleteReservation(selectedEvent.extendedProps.id)
          setSelectedEvent(null)
          refetch()
          refreshPendingCount()
          addToast('予約を削除しました', 'success')
        } catch (e: any) {
          const message = e.response?.data?.message || e.message || '削除に失敗しました'
          addToast(`エラー: ${message}`, 'error')
        }
      }
    })
  }

  const handleRequestCancellation = () => {
    setConfirmState({
      title: 'キャンセルを申請しますか？',
      confirmLabel: 'キャンセル申請',
      confirmVariant: 'warning',
      children: (
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            キャンセル理由
          </label>
          <textarea
            id="cancellation-reason-input"
            rows={3}
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontSize: '0.9rem' }}
            placeholder="キャンセルの理由を入力してください"
          />
        </div>
      ),
      onConfirm: async () => {
        const textarea = document.getElementById('cancellation-reason-input') as HTMLTextAreaElement
        const reason = textarea?.value || ''
        setConfirmState(null)
        try {
          await requestCancellation(selectedEvent.extendedProps.id, reason)
          setSelectedEvent(null)
          refetch()
          refreshPendingCount()
          addToast('キャンセル申請を送信しました', 'success')
        } catch (e: any) {
          const message = e.response?.data?.message || e.message || '申請に失敗しました'
          addToast(`エラー: ${message}`, 'error')
        }
      }
    })
  }

  const closeMobileMenu = () => setMobileMenuOpen(false)

  return (
    <div className="page">
      {/* ---- Navbar ---- */}
      <nav className="navbar">
        <div className="navbar-inner">
          <span className="navbar-brand">
            <span className="navbar-brand-icon">🏔</span>
            KC Reserve
          </span>

          <div className="navbar-actions">
            {/* Desktop actions */}
            <div className="desktop-only">
              <button className="button large" onClick={() => navigate('/reservations/new')}>
                ＋ 予約申請
              </button>
              {user?.isAdmin && (
                <button className="button secondary large" onClick={() => navigate('/admin/reservations')} style={{ position: 'relative' }}>
                  管理者: 申請一覧
                  {pendingCount > 0 && <span className="badge">{pendingCount}</span>}
                </button>
              )}

              {/* User dropdown */}
              {user && (
                <div className="user-menu" ref={userMenuRef}>
                  <button
                    className={`user-menu-trigger ${userMenuOpen ? 'open' : ''}`}
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                  >
                    <span className="avatar">{(userDisplayName || user.email)[0].toUpperCase()}</span>
                    <span className="user-name">{userDisplayName}</span>
                    <span className="chevron">▼</span>
                  </button>

                  {userMenuOpen && (
                    <div className="user-menu-dropdown">
                      <div className="menu-header">
                        {user.email}
                        {user.isAdmin && <span style={{ marginLeft: '0.25rem', fontSize: '0.75rem', background: 'var(--color-primary-light)', color: 'var(--color-primary)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>管理者</span>}
                      </div>
                      <button className="menu-item" onClick={() => { navigate('/profile'); setUserMenuOpen(false) }}>
                        👤 {t('auth.editProfile')}
                      </button>
                      {user.isAdmin && (
                        <button className="menu-item" onClick={() => { navigate('/admin/whitelist'); setUserMenuOpen(false) }}>
                          📋 {t('admin.editWhitelist')}
                        </button>
                      )}
                      <div className="menu-divider" />
                      <button className="menu-item danger" onClick={() => { logout(); setUserMenuOpen(false) }}>
                        🚪 {t('auth.signOut')}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Mobile hamburger */}
            <button className="navbar-hamburger" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="mobile-menu">
          {user && (
            <div className="mobile-user-info">
              {user.email}
              {user.isAdmin && <span style={{ marginLeft: '0.25rem', fontSize: '0.75rem', background: 'var(--color-primary-light)', color: 'var(--color-primary)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>管理者</span>}
            </div>
          )}
          <button className="mobile-menu-item" onClick={() => { navigate('/reservations/new'); closeMobileMenu() }}>
            ＋ 予約申請
          </button>
          {user?.isAdmin && (
            <button className="mobile-menu-item" onClick={() => { navigate('/admin/reservations'); closeMobileMenu() }}>
              📋 管理者: 申請一覧 {pendingCount > 0 && <span className="badge" style={{ position: 'static', marginLeft: '0.25rem' }}>{pendingCount}</span>}
            </button>
          )}
          <button className="mobile-menu-item" onClick={() => { navigate('/profile'); closeMobileMenu() }}>
            👤 {t('auth.editProfile')}
          </button>
          {user?.isAdmin && (
            <button className="mobile-menu-item" onClick={() => { navigate('/admin/whitelist'); closeMobileMenu() }}>
              📋 {t('admin.editWhitelist')}
            </button>
          )}
          <div className="mobile-menu-divider" />
          <button className="mobile-menu-item danger" onClick={() => { logout(); closeMobileMenu() }}>
            🚪 {t('auth.signOut')}
          </button>
        </div>
      )}

      {/* ---- Page Body ---- */}
      <div className="page-body">
        {/* Video Section (collapsible) */}
        <section className="video-section">
          <button className="video-toggle" onClick={toggleVideo}>
            <span>📹 山小屋の利用方法</span>
            <span className={`toggle-icon ${videoOpen ? 'open' : ''}`}>▼</span>
          </button>
          <div className={`video-body ${videoOpen ? 'expanded' : 'collapsed'}`}>
            <div className="video-container">
              {videoUrl && (
                <iframe 
                    src={getEmbedUrl(videoUrl)} 
                    title="YouTube video player" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowFullScreen
                ></iframe>
              )}
            </div>
          </div>
        </section>

        {/* Filter & Status */}
        <section className="controls">
          <div className="field">
            <label htmlFor="visibility">{t('filters.label')}</label>
            <select
              id="visibility"
              value={visibilityFilter}
              onChange={(event) => setVisibilityFilter(event.target.value as typeof visibilityFilter)}
            >
              <option value="all">{t('filters.all')}</option>
              <option value="public">{t('filters.public')}</option>
              <option value="anonymous">{t('filters.anonymous')}</option>
            </select>
          </div>

          {isFetching && <span className="status-pill">🔄 {t('app.refreshing')}</span>}
        </section>

        {/* Calendar */}
        <section className="calendar-card" style={{ position: 'relative' }}>
          {error ? (
            <div className="error-banner">
              <strong>{t('app.error')}</strong>
              <span>{(error as Error).message}</span>
            </div>
          ) : null}

          {isLoading && (
            <div className="loading-overlay">
              <div className="spinner" />
              <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>読み込み中...</span>
            </div>
          )}

          <FullCalendar
              plugins={[dayGridPlugin]}
              initialView="dayGridMonth"
              locale={jaLocale}
              height="auto"
              events={calendarEvents}
              displayEventTime={false}
              datesSet={(info) => {
                const paddedStart = dayjs(info.startStr).subtract(bufferInDays, 'day').toISOString()
                const paddedEnd = dayjs(info.endStr).add(bufferInDays, 'day').toISOString()
                setRange((current) =>
                  current.start === paddedStart && current.end === paddedEnd
                    ? current
                    : { start: paddedStart, end: paddedEnd },
                )
              }}
              headerToolbar={{ start: 'title', center: '', end: 'today prev,next' }}
              eventClick={(info) => {
                setSelectedEvent({
                  title: info.event.title,
                  start: info.event.start,
                  end: info.event.end,
                  extendedProps: info.event.extendedProps
                })
                setIsEditing(false)
              }}
            />

          <footer className="legend">
            <span className="legend-item status-approved">{t('event.status.approved')}</span>
            <span className="legend-item status-pending">{t('event.status.pending')}</span>
            <span className="legend-item status-rejected">{t('event.status.rejected')}</span>
            <span className="legend-item status-cancelled">{t('event.status.cancelled')}</span>
          </footer>
        </section>
      </div>

      {/* ---- Reservation Detail Modal ---- */}
      {selectedEvent && (
        <div className="modal-backdrop" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>予約詳細</h2>
                <span className={`status-badge ${selectedEvent.extendedProps.status}`}>
                  {STATUS_LABELS[selectedEvent.extendedProps.status] || selectedEvent.extendedProps.status}
                </span>
              </div>
              <button className="modal-close" onClick={() => setSelectedEvent(null)}>✕</button>
            </div>

            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">タイトル</span>
                <span className="detail-value">{selectedEvent.title}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">日時</span>
                <span className="detail-value">
                  {dayjs(selectedEvent.start).format('YYYY/MM/DD HH:mm')} 〜 {dayjs(selectedEvent.end).format('MM/DD HH:mm')}
                </span>
              </div>
              {selectedEvent.extendedProps.userDisplayName && (
                <div className="detail-row">
                  <span className="detail-label">予約者</span>
                  <span className="detail-value">{selectedEvent.extendedProps.userDisplayName}</span>
                </div>
              )}
              {selectedEvent.extendedProps.attendeeCount && (
                <div className="detail-row">
                  <span className="detail-label">人数</span>
                  <span className="detail-value">{selectedEvent.extendedProps.attendeeCount}人</span>
                </div>
              )}

              {/* Description / Display Message */}
              {isEditing ? (
                <div style={{ marginTop: '1rem' }}>
                  <div className="field" style={{ marginBottom: '0.75rem' }}>
                    <label>詳細メッセージ</label>
                    <textarea 
                      value={editingDescription}
                      onChange={e => setEditingDescription(e.target.value)}
                      rows={4}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontSize: '0.9rem' }}
                    />
                  </div>
                  <div className="field" style={{ marginBottom: '0.75rem' }}>
                    <label>カレンダー表示メッセージ</label>
                    <input 
                      type="text"
                      value={editingDisplayMessage}
                      onChange={e => setEditingDisplayMessage(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontSize: '0.9rem', minWidth: 'unset' }}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="button small" onClick={handleSave}>保存</button>
                    <button className="button ghost small" onClick={() => setIsEditing(false)}>やめる</button>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ marginTop: '0.75rem' }}>
                    <span className="detail-label">詳細メッセージ</span>
                    <div className="message-box">
                      {selectedEvent.extendedProps.description || '(なし)'}
                    </div>
                  </div>
                  <div style={{ marginTop: '0.5rem' }}>
                    <span className="detail-label">カレンダー表示メッセージ</span>
                    <div className="message-box">
                      {selectedEvent.extendedProps.displayMessage || '(なし)'}
                    </div>
                  </div>
                  {selectedEvent.extendedProps.isOwner && (
                    <button className="button secondary small" style={{ marginTop: '0.5rem' }} onClick={handleEdit}>✏️ 編集</button>
                  )}
                </>
              )}

              {/* Rejection / Approval messages */}
              {selectedEvent.extendedProps.rejectionReason && (
                <div style={{ marginTop: '0.75rem' }}>
                  <span className="detail-label">却下理由</span>
                  <div className="message-box rejection">
                    {selectedEvent.extendedProps.rejectionReason}
                  </div>
                </div>
              )}
              {selectedEvent.extendedProps.approvalMessage && (
                <div style={{ marginTop: '0.75rem' }}>
                  <span className="detail-label">管理者からのメッセージ</span>
                  <div className="message-box approval">
                    {selectedEvent.extendedProps.approvalMessage}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {user?.isAdmin && (
                  <button className="button danger small" onClick={handleDelete}>🗑 削除</button>
                )}
                {selectedEvent.extendedProps.isOwner && selectedEvent.extendedProps.status === 'approved' && (
                  <button className="button warning small" onClick={handleRequestCancellation}>キャンセル申請</button>
                )}
              </div>
              <button className="button ghost small" onClick={() => setSelectedEvent(null)}>閉じる</button>
            </div>
          </div>
        </div>
      )}

      {/* ---- Confirm Dialog ---- */}
      {confirmState && (
        <ConfirmDialog
          title={confirmState.title}
          message={confirmState.message}
          confirmLabel={confirmState.confirmLabel}
          confirmVariant={confirmState.confirmVariant}
          onConfirm={confirmState.onConfirm}
          onCancel={() => setConfirmState(null)}
        >
          {confirmState.children}
        </ConfirmDialog>
      )}

      {/* ---- Toast Notifications ---- */}
      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map(toast => (
            <Toast key={toast.id} message={toast.message} type={toast.type} onClose={() => removeToast(toast.id)} />
          ))}
        </div>
      )}
    </div>
  )
}
