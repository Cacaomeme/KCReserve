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
  token?: string | null
}

export async function fetchCalendarEvents(query: CalendarQuery) {
  const { token, ...params } = query

  const response = await apiClient.get<{ events: CalendarEvent[] }>('/api/reservations/calendar', {
    params,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })

  return response.data.events
}
