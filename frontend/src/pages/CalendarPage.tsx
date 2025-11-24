import { useMemo, useState, useEffect } from 'react'
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

export function CalendarPage() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const authFingerprint = user ? `${user.id}-${user.isAdmin ? 'admin' : 'member'}` : 'anonymous'
  
  const [visibilityFilter, setVisibilityFilter] = useState<'all' | 'public' | 'anonymous'>('all')
  const [range, setRange] = useState(() => ({
    start: dayjs().startOf('month').subtract(bufferInDays, 'day').toISOString(),
    end: dayjs().endOf('month').add(bufferInDays, 'day').toISOString(),
  }))
  const [pendingCount, setPendingCount] = useState(0)
  const [videoUrl, setVideoUrl] = useState('')

  useEffect(() => {
    getVideoUrl().then(setVideoUrl).catch(console.error)
  }, [])

  useEffect(() => {
    if (user?.isAdmin) {
      getPendingCount().then(setPendingCount).catch(console.error)
    }
  }, [user])

  const visibilityParam = visibilityFilter === 'all' ? undefined : visibilityFilter

  const { data: events = [], isLoading, isFetching, error, refetch } = useCalendarEvents({
    start: range.start,
    end: range.end,
    visibility: visibilityParam,
    authFingerprint,
  })

  const [selectedEvent, setSelectedEvent] = useState<any>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editingDescription, setEditingDescription] = useState('')
  const [editingDisplayMessage, setEditingDisplayMessage] = useState('')

  const calendarEvents = useMemo(
    () =>
      events.map((event) => ({
        id: String(event.id),
        title:
          event.title ??
          (event.visibility === 'anonymous' ? t('event.reservedAnonymous') : t('event.reserved')),
        start: event.start ?? undefined,
        end: event.end ?? undefined,
        // allDay: true, // Remove this to show time
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
    } catch (e) {
        alert('更新に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('本当にこの予約を削除しますか？')) {
      return
    }
    try {
      await deleteReservation(selectedEvent.extendedProps.id)
      setSelectedEvent(null)
      refetch()
    } catch (e: any) {
      const message = e.response?.data?.message || e.message || '削除に失敗しました'
      alert(`エラー: ${message}`)
    }
  }

  const handleRequestCancellation = async () => {
    const reason = window.prompt('キャンセル申請の理由を入力してください')
    if (reason === null) return // Cancelled prompt

    if (!window.confirm('この予約のキャンセルを申請しますか？')) {
      return
    }
    try {
      await requestCancellation(selectedEvent.extendedProps.id, reason)
      setSelectedEvent(null)
      refetch()
      alert('キャンセル申請を行いました')
    } catch (e: any) {
      const message = e.response?.data?.message || e.message || '申請に失敗しました'
      alert(`エラー: ${message}`)
    }
  }

  return (
    <div className="page">
      <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>{t('app.title')}</h1>
          <p className="subtitle">
            {/* {t('app.subtitle')} */}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
                <button className="button large" onClick={() => navigate('/reservations/new')}>予約申請</button>
                {user?.isAdmin && (
                    <button className="button secondary large" onClick={() => navigate('/admin/reservations')} style={{ position: 'relative' }}>
                    申請一覧
                    {pendingCount > 0 && (
                        <span style={{
                        position: 'absolute',
                        top: '-8px',
                        right: '-8px',
                        backgroundColor: '#ef4444',
                        color: 'white',
                        borderRadius: '50%',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        fontWeight: 'bold'
                        }}>
                        {pendingCount}
                        </span>
                    )}
                    </button>
                )}
            </div>

            {user && (
                <div className="auth-panel" style={{ minWidth: 'auto', padding: '0.75rem', marginBottom: 0 }}>
                    <div className="auth-status">
                        <p style={{ margin: 0, fontSize: '0.85rem' }}>
                            {t('auth.signedInAs', { email: user.email })}
                            {user.isAdmin ? ` ${t('auth.admin')}` : ''}
                        </p>
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                            {user.isAdmin && (
                                <button
                                    type="button"
                                    onClick={() => navigate('/admin/whitelist')}
                                    className="button secondary"
                                    style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                                >
                                    {t('admin.editWhitelist')}
                                </button>
                            )}
                            <button
                                type="button"
                                onClick={() => navigate('/profile')}
                                className="button secondary"
                                style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                            >
                                {t('auth.editProfile')}
                            </button>
                            <button 
                                type="button" 
                                onClick={logout} 
                                className="button ghost"
                                style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                            >
                                {t('auth.signOut')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
      </header>

      <section className="video-section">
        <h2 style={{ marginTop: 0, fontSize: '1.25rem', color: '#475569' }}>山小屋の利用方法</h2>
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
      </section>

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

        {isFetching && <span className="status-pill">{t('app.refreshing')}</span>}
      </section>

      <section className="calendar-card">
        {error ? (
          <div className="error-banner">
            <strong>{t('app.error')}</strong>
            <span>{(error as Error).message}</span>
          </div>
        ) : null}

        {isLoading ? (
          <div className="loading">{t('app.loading')}</div>
        ) : (
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
        )}

        <footer className="legend">
          <span className="legend-item status-approved">{t('event.status.approved')}</span>
          <span className="legend-item status-pending">{t('event.status.pending')}</span>
          <span className="legend-item status-rejected">{t('event.status.rejected')}</span>
          <span className="legend-item status-cancelled">{t('event.status.cancelled')}</span>
        </footer>
      </section>

      {selectedEvent && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }} onClick={() => setSelectedEvent(null)}>
          <div style={{
            backgroundColor: 'white', padding: '2rem', borderRadius: '8px', maxWidth: '500px', width: '90%',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }} onClick={e => e.stopPropagation()}>
            <h2 style={{ marginTop: 0 }}>予約詳細</h2>
            <p><strong>タイトル:</strong> {selectedEvent.title}</p>
            <p><strong>ステータス:</strong> {t(`event.status.${selectedEvent.extendedProps.status}`)}</p>
            <p><strong>日時:</strong> {dayjs(selectedEvent.start).format('YYYY/MM/DD HH:mm')} - {dayjs(selectedEvent.end).format('YYYY/MM/DD HH:mm')}</p>
            
            {selectedEvent.extendedProps.userDisplayName && (
                <p><strong>予約者:</strong> {selectedEvent.extendedProps.userDisplayName}</p>
            )}
            {selectedEvent.extendedProps.attendeeCount && (
                <p><strong>人数:</strong> {selectedEvent.extendedProps.attendeeCount}人</p>
            )}
            
            <div style={{marginTop: '1rem'}}>
                <strong>詳細メッセージ:</strong>
                {isEditing ? (
                    <div style={{ marginTop: '0.5rem' }}>
                        <textarea 
                            value={editingDescription}
                            onChange={e => setEditingDescription(e.target.value)}
                            rows={4}
                            style={{ width: '100%', padding: '0.5rem' }}
                        />
                        <div style={{ marginTop: '1rem' }}>
                            <strong>カレンダー表示メッセージ:</strong>
                            <input 
                                type="text"
                                value={editingDisplayMessage}
                                onChange={e => setEditingDisplayMessage(e.target.value)}
                                style={{ width: '100%', padding: '0.5rem' }}
                            />
                        </div>
                        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                            <button className="button" onClick={handleSave}>保存</button>
                            <button className="button ghost" onClick={() => setIsEditing(false)}>キャンセル</button>
                        </div>
                    </div>
                ) : (
                    <div>
                        <p style={{whiteSpace: 'pre-wrap', margin: '0.5rem 0'}}>{selectedEvent.extendedProps.description || '(なし)'}</p>
                        
                        <div style={{marginTop: '1rem'}}>
                            <strong>カレンダー表示メッセージ:</strong>
                            <p style={{margin: '0.5rem 0'}}>{selectedEvent.extendedProps.displayMessage || '(なし)'}</p>
                        </div>

                        {selectedEvent.extendedProps.isOwner && (
                            <button className="button secondary" style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem' }} onClick={handleEdit}>編集</button>
                        )}
                    </div>
                )}
            </div>

            {selectedEvent.extendedProps.rejectionReason && (
                <div style={{marginTop: '1rem', color: 'red'}}>
                    <strong>却下理由:</strong>
                    <p>{selectedEvent.extendedProps.rejectionReason}</p>
                </div>
            )}
            {selectedEvent.extendedProps.approvalMessage && (
                <div style={{marginTop: '1rem', color: 'green'}}>
                    <strong>管理者からのメッセージ:</strong>
                    <p>{selectedEvent.extendedProps.approvalMessage}</p>
                </div>
            )}

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {user?.isAdmin && (
                    <button className="button" style={{ backgroundColor: '#ef4444' }} onClick={handleDelete}>削除</button>
                )}
                {selectedEvent.extendedProps.isOwner && selectedEvent.extendedProps.status === 'approved' && (
                    <button className="button" style={{ backgroundColor: '#f59e0b' }} onClick={handleRequestCancellation}>キャンセル申請</button>
                )}
              </div>
              <button className="button" onClick={() => setSelectedEvent(null)} style={{ marginLeft: 'auto' }}>閉じる</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
