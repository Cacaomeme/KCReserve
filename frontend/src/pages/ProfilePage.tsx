import { useState, useEffect } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProfilePage() {
  const { t } = useTranslation()
  const { user, updateProfile, authError, clearError } = useAuth()
  const navigate = useNavigate()
  
  const [form, setForm] = useState({
    email: '',
    display_name: '',
    receives_notification: false,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      setForm({
        email: user.email,
        display_name: user.display_name || '',
        receives_notification: user.receivesNotification,
      })
    }
  }, [user])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSuccessMessage(null)
    if (authError) clearError()

    setIsSubmitting(true)
    try {
      await updateProfile(form)
      setSuccessMessage(t('profile.updateSuccess'))
    } catch {
      // Error is handled by AuthContext
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>{t('profile.title')}</h1>
          <button onClick={() => navigate('/')} className="button ghost" style={{ marginTop: '1rem' }}>
            &larr; {t('calendar.backToCalendar')}
          </button>
        </div>
      </header>

      <section className="auth-container">
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">{t('auth.email')}</label>
            <input
              id="email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              disabled={isSubmitting}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="display_name">{t('auth.displayName')}</label>
            <input
              id="display_name"
              type="text"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              disabled={isSubmitting}
              required
            />
          </div>

          {user?.isAdmin && (
            <div className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
                <input
                    id="receives_notification"
                    type="checkbox"
                    checked={form.receives_notification}
                    onChange={(e) => setForm({ ...form, receives_notification: e.target.checked })}
                    disabled={isSubmitting}
                    style={{ width: 'auto' }}
                />
                <label htmlFor="receives_notification" style={{ marginBottom: 0 }}>
                    新規予約申請のメール通知を受け取る
                </label>
            </div>
          )}
          
          {authError && <p className="error-text">{authError}</p>}
          {successMessage && <p className="success-text" style={{ color: '#166534' }}>{successMessage}</p>}
          
          <button type="submit" className="button" disabled={isSubmitting}>
            {isSubmitting ? t('profile.updating') : t('profile.update')}
          </button>
        </form>
      </section>
    </div>
  )
}
