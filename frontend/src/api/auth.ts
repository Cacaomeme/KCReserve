import { apiClient } from './client'
import { clearAccessToken, setAccessToken } from './session'

export type AuthUser = {
  id: number
  email: string
  isAdmin: boolean
  isActive: boolean
  createdAt: string | null
  updatedAt: string | null
}

export type AuthPayload = {
  user: AuthUser
  accessToken: string
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
