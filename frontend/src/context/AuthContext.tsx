import { AxiosError } from 'axios'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { PropsWithChildren } from 'react'
import type { AuthUser } from '../api/auth'
import { login as loginRequest, logout as logoutRequest, register as registerRequest, refreshSession, updateProfile as updateProfileRequest } from '../api/auth'
import type { UpdateProfilePayload } from '../api/auth'

export type AuthContextValue = {
  user: AuthUser | null
  isInitializing: boolean
  authError: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, display_name: string) => Promise<void>
  updateProfile: (payload: UpdateProfilePayload) => Promise<void>
  logout: () => Promise<void>
  clearError: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const [authError, setAuthError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    console.log('[AuthContext] Initialization started')
    ;(async () => {
      try {
        const data = await refreshSession()
        if (!active) return
        console.log('[AuthContext] Session refreshed', data.user)
        setUser(data.user)
      } catch (error) {
        console.log('[AuthContext] Session refresh failed', error)
        // Cookie が無い/無効な場合はそのまま匿名状態で開始する
      } finally {
        if (active) {
          console.log('[AuthContext] Initialization complete')
          setIsInitializing(false)
        }
      }
    })()

    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    try {
      const data = await loginRequest(email, password)
      setUser(data.user)
      setAuthError(null)
    } catch (error) {
      let message = 'ログインに失敗しました'
      if (error instanceof AxiosError) {
        const apiMessage = (error.response?.data as { message?: string } | undefined)?.message
        if (apiMessage) {
          message = apiMessage
        }
      } else if (error instanceof Error) {
        message = error.message
      }
      setAuthError(message)
      throw error
    }
  }, [])

  const register = useCallback(async (email: string, password: string, display_name: string) => {
    try {
      const data = await registerRequest(email, password, display_name)
      setUser(data.user)
      setAuthError(null)
    } catch (error) {
      let message = '登録に失敗しました'
      if (error instanceof AxiosError) {
        const apiMessage = (error.response?.data as { message?: string } | undefined)?.message
        if (apiMessage) {
          message = apiMessage
        }
      } else if (error instanceof Error) {
        message = error.message
      }
      setAuthError(message)
      throw error
    }
  }, [])

  const updateProfile = useCallback(async (payload: UpdateProfilePayload) => {
    try {
      const data = await updateProfileRequest(payload)
      setUser(data.user)
      setAuthError(null)
    } catch (error) {
      let message = 'プロフィールの更新に失敗しました'
      if (error instanceof AxiosError) {
        const apiMessage = (error.response?.data as { message?: string } | undefined)?.message
        if (apiMessage) {
          message = apiMessage
        }
      } else if (error instanceof Error) {
        message = error.message
      }
      setAuthError(message)
      throw error
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
      setAuthError(null)
    }
  }, [])

  const clearError = useCallback(() => setAuthError(null), [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, isInitializing, authError, login, register, updateProfile, logout, clearError }),
    [user, isInitializing, authError, login, register, updateProfile, logout, clearError],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
