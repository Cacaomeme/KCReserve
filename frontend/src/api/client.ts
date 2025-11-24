import axios, { AxiosHeaders } from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { clearAccessToken, getAccessToken, setAccessToken } from './session'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000',
  withCredentials: true,
})

type AuthResponse = {
  accessToken: string
}

let refreshPromise: Promise<string | null> | null = null

const REFRESH_ENDPOINT = '/api/auth/refresh'

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = apiClient
      .post<AuthResponse>(REFRESH_ENDPOINT, undefined, { skipAuthRefresh: true })
      .then((response) => {
        const token = response.data.accessToken
        setAccessToken(token)
        return token
      })
      .catch((error) => {
        clearAccessToken()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

apiClient.interceptors.request.use((config) => {
  const headers = AxiosHeaders.from(config.headers)
  if (!headers.has('Authorization')) {
    const token = getAccessToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }
  config.headers = headers
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const response = error.response
    const config = error.config as InternalAxiosRequestConfig

    if (!response || !config || config.skipAuthRefresh || config._retry) {
      return Promise.reject(error)
    }

    if (response.status === 401) {
      config._retry = true
      try {
        const newToken = await refreshAccessToken()
        if (newToken) {
          const headers = AxiosHeaders.from(config.headers)
          headers.set('Authorization', `Bearer ${newToken}`)
          config.headers = headers
          return apiClient(config)
        }
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)
