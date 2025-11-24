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

export function RegisterPage() {
  const { t } = useTranslation()
  const { register: registerUser, authError, clearError, isInitializing } = useAuth()
  const navigate = useNavigate()
  
  const [form, setForm] = useState({
    email: '',
    display_name: '',
    password: '',
    confirmPassword: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const handleRegister = async (event: FormEvent) => {
    event.preventDefault()
    setValidationError(null)

    if (!form.email || !form.password || !form.display_name) {
      return
    }
    if (form.password !== form.confirmPassword) {
      setValidationError('パスワードが一致しません')
      return
    }

    setIsSubmitting(true)
    try {
      await registerUser(form.email, form.password, form.display_name)
      navigate('/')
    } catch {
      // Error is handled by AuthContext and displayed via authError
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFieldChange = (field: keyof typeof form, value: string) => {
    if (authError) clearError()
    if (validationError) setValidationError(null)
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>{t('auth.register')}</h1>
        </div>
      </header>

      <section className="auth-container">
        <form className="auth-form" onSubmit={handleRegister}>
          <div className="field">
            <label htmlFor="email">{t('auth.email')}</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(e) => handleFieldChange('email', e.target.value)}
              disabled={isSubmitting || isInitializing}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="display_name">{t('auth.displayName')}</label>
            <input
              id="display_name"
              type="text"
              value={form.display_name}
              onChange={(e) => handleFieldChange('display_name', e.target.value)}
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
                autoComplete="new-password"
                value={form.password}
                onChange={(e) => handleFieldChange('password', e.target.value)}
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
          <div className="field">
            <label htmlFor="confirmPassword">{t('auth.confirmPassword')}</label>
            <input
              id="confirmPassword"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              value={form.confirmPassword}
              onChange={(e) => handleFieldChange('confirmPassword', e.target.value)}
              disabled={isSubmitting || isInitializing}
              required
            />
          </div>
          
          {validationError && <p className="error-text">{validationError}</p>}
          {authError && <p className="error-text">{authError}</p>}
          
          <button type="submit" className="button" disabled={isSubmitting || isInitializing}>
            {isSubmitting ? t('auth.signingUp') : t('auth.signUp')}
          </button>
        </form>
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <button type="button" className="button ghost" onClick={() => navigate('/login')}>
            {t('auth.toLogin')}
          </button>
        </div>
      </section>
    </div>
  )
}
