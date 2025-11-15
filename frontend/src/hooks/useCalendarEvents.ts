import { useQuery } from '@tanstack/react-query'
import type { CalendarEvent } from '../api/reservations'
import { fetchCalendarEvents } from '../api/reservations'

type UseCalendarEventsOptions = {
  start: string
  end: string
  token?: string | null
  visibility?: 'public' | 'anonymous'
}

export function useCalendarEvents({ start, end, token, visibility }: UseCalendarEventsOptions) {
  return useQuery<CalendarEvent[]>({
    queryKey: ['calendar-events', start, end, visibility, Boolean(token)],
    queryFn: () =>
      fetchCalendarEvents({
        start,
        end,
        visibility,
        token,
      }),
  })
}
