import { apiClient } from './client'
import { clearAccessToken, setAccessToken } from './session'

export type AuthUser = {
  id: number
  email: string
  display_name?: string | null
  isAdmin: boolean
  isActive: boolean
  createdAt: string | null
  updatedAt: string | null
}

export type AuthPayload = {
  user: AuthUser
  accessToken: string
}

export type UpdateProfilePayload = {
  email?: string
  display_name?: string
}

export async function login(email: string, password: string) {
  const response = await apiClient.post<AuthPayload>(
    '/api/auth/login',
    { email, password },
    { skipAuthRefresh: true },
  )
  setAccessToken(response.data.accessToken)
  return response.data
}

export async function register(email: string, password: string, display_name: string) {
  const response = await apiClient.post<AuthPayload>(
    '/api/auth/register',
    { email, password, display_name },
    { skipAuthRefresh: true },
  )
  setAccessToken(response.data.accessToken)
  return response.data
}

export async function updateProfile(payload: UpdateProfilePayload) {
  const response = await apiClient.put<{ user: AuthUser }>('/api/auth/me', payload)
  return response.data
}

export async function refreshSession() {
  const response = await apiClient.post<AuthPayload>('/api/auth/refresh', undefined, {
    skipAuthRefresh: true,
  })
  setAccessToken(response.data.accessToken)
  return response.data
}

export async function logout() {
  await apiClient.post('/api/auth/logout', undefined, { skipAuthRefresh: true })
  clearAccessToken()
}

export async function fetchCurrentUser() {
  const response = await apiClient.get<{ user: AuthUser; claims: { isAdmin: boolean } }>(
    '/api/auth/me',
  )
  return response.data
}
