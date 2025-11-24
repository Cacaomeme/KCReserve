import { AxiosError } from 'axios'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { PropsWithChildren } from 'react'
import type { AuthUser } from '../api/auth'
import { login as loginRequest, logout as logoutRequest, refreshSession } from '../api/auth'

export type AuthContextValue = {
  user: AuthUser | null
  isInitializing: boolean
  authError: string | null
  login: (email: string, password: string) => Promise<void>
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
    ;(async () => {
      try {
        const data = await refreshSession()
        if (!active) return
        setUser(data.user)
      } catch {
        // Cookie が無い/無効な場合はそのまま匿名状態で開始する
      } finally {
        if (active) {
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
    () => ({ user, isInitializing, authError, login, logout, clearError }),
    [user, isInitializing, authError, login, logout, clearError],
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
