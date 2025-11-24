import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import jaLocale from '@fullcalendar/core/locales/ja'
import { useCalendarEvents } from '../hooks/useCalendarEvents'
import { useAuth } from '../context/AuthContext'

const bufferInDays = 7

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

  const visibilityParam = visibilityFilter === 'all' ? undefined : visibilityFilter

  const { data: events = [], isLoading, isFetching, error } = useCalendarEvents({
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
        allDay: true,
        classNames: ['calendar-event', `status-${event.status}`],
      })),
    [events, t],
  )

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>{t('app.title')}</h1>
          <p className="subtitle">
            {t('app.subtitle')}
          </p>
        </div>
      </header>

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

        <div className="auth-panel">
          {user && (
            <div className="auth-status">
              <p>
                {t('auth.signedInAs', { email: user.email })}
                {user.isAdmin ? ` ${t('auth.admin')}` : ''}
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {user.isAdmin && (
                  <button
                    type="button"
                    onClick={() => navigate('/admin/whitelist')}
                    className="button secondary"
                  >
                    {t('admin.editWhitelist')}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => navigate('/profile')}
                  className="button secondary"
                >
                  {t('auth.editProfile')}
                </button>
                <button type="button" onClick={logout} className="button ghost">
                  {t('auth.signOut')}
                </button>
              </div>
            </div>
          )}
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
          />
        )}

        <footer className="legend">
          <span className="legend-item status-approved">{t('event.status.approved')}</span>
          <span className="legend-item status-pending">{t('event.status.pending')}</span>
          <span className="legend-item status-rejected">{t('event.status.rejected')}</span>
          <span className="legend-item status-cancelled">{t('event.status.cancelled')}</span>
        </footer>
      </section>
    </div>
  )
}
