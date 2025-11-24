import { useQuery } from '@tanstack/react-query'
import type { CalendarEvent } from '../api/reservations'
import { fetchCalendarEvents } from '../api/reservations'

type UseCalendarEventsOptions = {
  start: string
  end: string
  visibility?: 'public' | 'anonymous'
  authFingerprint?: string
}

export function useCalendarEvents({ start, end, visibility, authFingerprint }: UseCalendarEventsOptions) {
  const authKey = authFingerprint ?? 'anonymous'
  return useQuery<CalendarEvent[]>({
    queryKey: ['calendar-events', start, end, visibility, authKey],
    queryFn: () =>
      fetchCalendarEvents({
        start,
        end,
        visibility,
      }),
  })
}
