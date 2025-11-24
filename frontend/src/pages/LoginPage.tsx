import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const EyeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
)

const EyeOffIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
    <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
    <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
    <line x1="2" x2="22" y1="2" y2="22" />
  </svg>
)

export function LoginPage() {
  const { t } = useTranslation()
  const { login, authError, clearError, isInitializing } = useAuth()
  const navigate = useNavigate()
  
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault()
    if (!credentials.email || !credentials.password) {
      return
    }
    setIsSubmitting(true)
    try {
      await login(credentials.email, credentials.password)
      navigate('/')
    } catch {
      // Error is handled by AuthContext and displayed via authError
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFieldChange = (field: 'email' | 'password', value: string) => {
    if (authError) {
      clearError()
    }
    setCredentials((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>{t('auth.signIn')}</h1>
        </div>
      </header>

      <section className="auth-container">
        <form className="auth-form" onSubmit={handleLogin}>
          <div className="field">
            <label htmlFor="email">{t('auth.email')}</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={credentials.email}
              onChange={(event) => handleFieldChange('email', event.target.value)}
              disabled={isSubmitting || isInitializing}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">{t('auth.password')}</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={credentials.password}
                onChange={(event) => handleFieldChange('password', event.target.value)}
                disabled={isSubmitting || isInitializing}
                required
                style={{ width: '100%', paddingRight: '2.5rem', boxSizing: 'border-box' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.5rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  color: '#64748b',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                tabIndex={-1}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
          </div>
          {authError ? <p className="error-text">{authError}</p> : null}
          <button type="submit" className="button" disabled={isSubmitting || isInitializing}>
            {isSubmitting ? t('auth.signingIn') : t('auth.signIn')}
          </button>
        </form>
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '0.5rem' }}>
            {t('auth.noAccount')}
          </p>
          <button type="button" className="button ghost" onClick={() => navigate('/register')}>
            {t('auth.signUp')}
          </button>
        </div>
      </section>
    </div>
  )
}
