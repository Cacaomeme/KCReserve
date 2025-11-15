import { useMemo, useState } from 'react'
import dayjs from 'dayjs'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import { useCalendarEvents } from './hooks/useCalendarEvents'
import './App.css'

const bufferInDays = 7

function App() {
  const [token, setToken] = useState('')
  const [visibilityFilter, setVisibilityFilter] = useState<'all' | 'public' | 'anonymous'>('all')
  const [range, setRange] = useState(() => ({
    start: dayjs().startOf('month').subtract(bufferInDays, 'day').toISOString(),
    end: dayjs().endOf('month').add(bufferInDays, 'day').toISOString(),
  }))

  const visibilityParam = visibilityFilter === 'all' ? undefined : visibilityFilter

  const { data: events = [], isLoading, isFetching, error } = useCalendarEvents({
    start: range.start,
    end: range.end,
    token: token ? token : undefined,
    visibility: visibilityParam,
  })

  const calendarEvents = useMemo(
    () =>
      events.map((event) => ({
        id: String(event.id),
        title:
          event.title ??
          (event.visibility === 'anonymous' ? '予約済み (匿名)' : '予約済み'),
        start: event.start ?? undefined,
        end: event.end ?? undefined,
        allDay: true,
        classNames: ['calendar-event', `status-${event.status}`],
      })),
    [events],
  )

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>Hut Reservation Calendar</h1>
          <p className="subtitle">
            The calendar shows approved bookings by default. Provide a JWT token
            to view private details or pending requests.
          </p>
        </div>
      </header>

      <section className="controls">
        <div className="field">
          <label htmlFor="visibility">Visibility</label>
          <select
            id="visibility"
            value={visibilityFilter}
            onChange={(event) => setVisibilityFilter(event.target.value as typeof visibilityFilter)}
          >
            <option value="all">All events</option>
            <option value="public">Public only</option>
            <option value="anonymous">Masked only</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="token">JWT (optional)</label>
          <input
            id="token"
            placeholder="Paste bearer token"
            value={token}
            onChange={(event) => setToken(event.target.value)}
          />
        </div>

        {isFetching && <span className="status-pill">Refreshing…</span>}
      </section>

      <section className="calendar-card">
        {error ? (
          <div className="error-banner">
            <strong>Failed to load events.</strong>
            <span>{(error as Error).message}</span>
          </div>
        ) : null}

        {isLoading ? (
          <div className="loading">Loading calendar…</div>
        ) : (
          <FullCalendar
            plugins={[dayGridPlugin]}
            initialView="dayGridMonth"
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
          <span className="legend-item status-approved">Approved</span>
          <span className="legend-item status-pending">Pending</span>
          <span className="legend-item status-rejected">Rejected</span>
          <span className="legend-item status-cancelled">Cancelled</span>
        </footer>
      </section>
    </div>
  )
}

export default App
