import { apiClient } from './client'

export type CalendarEvent = {
  id: number
  start: string | null
  end: string | null
  visibility: 'public' | 'anonymous'
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  title: string | null
}

export type CalendarQuery = {
  start: string
  end: string
  visibility?: 'public' | 'anonymous'
}

export async function fetchCalendarEvents(query: CalendarQuery) {
  const response = await apiClient.get<{ events: CalendarEvent[] }>('/api/reservations/calendar', {
    params: query,
  })

  return response.data.events
}
