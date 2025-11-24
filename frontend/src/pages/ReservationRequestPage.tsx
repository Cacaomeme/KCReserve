import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../api/client'

export function ReservationRequestPage() {
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState({
    startTime: '',
    endTime: '',
    visibility: 'public',
    purpose: '',
    displayMessage: '',
    description: '',
    attendeeCount: 1,
  })

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await apiClient.post('/api/reservations', {
        startTime: new Date(form.startTime).toISOString(),
        endTime: new Date(form.endTime).toISOString(),
        visibility: form.visibility,
        purpose: form.purpose,
        displayMessage: form.displayMessage,
        description: form.description,
        attendeeCount: form.attendeeCount,
      })
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.message || '予約申請に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>予約申請</h1>
      </header>
      <section className="auth-container">
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="field">
            <label>開始日時</label>
            <input 
              type="datetime-local" 
              value={form.startTime}
              onChange={e => setForm({...form, startTime: e.target.value})}
              required
            />
          </div>
          <div className="field">
            <label>終了日時</label>
            <input 
              type="datetime-local" 
              value={form.endTime}
              onChange={e => setForm({...form, endTime: e.target.value})}
              required
            />
          </div>
          <div className="field">
            <label>公開設定</label>
            <select 
              value={form.visibility}
              onChange={e => setForm({...form, visibility: e.target.value})}
              style={{ width: '100%', padding: '0.5rem' }}
            >
              <option value="public">公開希望</option>
              <option value="anonymous">匿名希望</option>
            </select>
          </div>
          <div className="field">
            <label>使用用途</label>
            <input 
              type="text" 
              value={form.purpose}
              onChange={e => setForm({...form, purpose: e.target.value})}
              required
            />
          </div>
          <div className="field">
            <label>人数</label>
            <input 
              type="number" 
              min="1"
              value={form.attendeeCount}
              onChange={e => setForm({...form, attendeeCount: parseInt(e.target.value)})}
              required
            />
          </div>
          {form.visibility === 'public' && (
            <div className="field">
              <label>カレンダー表示メッセージ</label>
              <input 
                type="text" 
                value={form.displayMessage}
                onChange={e => setForm({...form, displayMessage: e.target.value})}
              />
              <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                ※カレンダー表示メッセージは申請後も編集可能です
              </p>
            </div>
          )}
          <div className="field">
            <label>詳細メッセージ</label>
            <textarea 
              value={form.description}
              onChange={e => setForm({...form, description: e.target.value})}
              rows={4}
              style={{ width: '100%', padding: '0.5rem' }}
            />
            <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
              ※詳細メッセージは申請後も編集可能です
            </p>
          </div>
          
          {error && <p className="error-text">{error}</p>}
          
          <button type="submit" className="button" disabled={isSubmitting}>
            申請する
          </button>
          <button type="button" className="button ghost" onClick={() => navigate('/')}>
            キャンセル
          </button>
        </form>
      </section>
    </div>
  )
}
