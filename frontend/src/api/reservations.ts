import { apiClient } from './client'

export type CalendarEvent = {
  id: number
  start: string | null
  end: string | null
  visibility: 'public' | 'anonymous'
  status: 'pending' | 'approved' | 'rejected' | 'cancelled' | 'cancellation_requested'
  title: string | null
  description?: string
  attendeeCount?: number
  userDisplayName?: string
  rejectionReason?: string
  approvalMessage?: string
  isOwner?: boolean
  displayMessage?: string
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

export async function updateReservationDescription(id: number, description: string) {
  const response = await apiClient.patch<{ reservation: any }>(`/api/reservations/${id}`, {
    description,
  })
  return response.data.reservation
}

export async function updateReservation(id: number, updates: { description?: string; displayMessage?: string }) {
  const response = await apiClient.patch<{ reservation: any }>(`/api/reservations/${id}`, updates)
  return response.data.reservation
}

export async function requestCancellation(id: number, reason: string) {
  const response = await apiClient.patch<{ reservation: any }>(`/api/reservations/${id}`, {
    status: 'cancellation_requested',
    cancellationReason: reason,
  })
  return response.data.reservation
}

export async function getPendingCount() {
  const response = await apiClient.get<{ count: number }>('/api/admin/reservations/pending-count')
  return response.data.count
}

export async function deleteReservation(id: number) {
  await apiClient.delete(`/api/admin/reservations/${id}`)
}
