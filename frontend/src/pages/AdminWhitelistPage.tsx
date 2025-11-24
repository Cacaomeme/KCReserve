import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useWhitelist } from '../hooks/useWhitelist'
import { useAuth } from '../context/AuthContext'

export function AdminWhitelistPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { entries, isLoading, error, addEntry, updateEntry, deleteEntry, isAdding } = useWhitelist()

  const [form, setForm] = useState({
    email: '',
    display_name: '',
    is_admin_default: false,
  })

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({
    display_name: '',
    is_admin_default: false,
  })

  // 簡易的なアドミンチェック（本来はルートガードで行うべきだが、要件に従いページ内で処理）
  if (user && !user.isAdmin) {
    return <div className="page"><p className="error-text">Access Denied</p></div>
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.email) return
    try {
      await addEntry(form)
      setForm({ email: '', display_name: '', is_admin_default: false })
    } catch (err) {
      alert('Failed to add entry')
    }
  }

  const startEditing = (entry: any) => {
    setEditingId(entry.id)
    setEditForm({
      display_name: entry.display_name || '',
      is_admin_default: entry.is_admin_default,
    })
  }

  const cancelEditing = () => {
    setEditingId(null)
  }

  const saveEditing = async (id: number) => {
    try {
      await updateEntry({ id, payload: editForm })
      setEditingId(null)
    } catch (err) {
      alert('Failed to update entry')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm(t('admin.whitelist.confirmDelete'))) return
    try {
      await deleteEntry(id)
    } catch (err) {
      alert('Failed to delete entry')
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">KC Reserve</p>
          <h1>{t('admin.whitelist.title')}</h1>
          <button onClick={() => navigate('/')} className="button ghost" style={{ marginTop: '1rem' }}>
            &larr; {t('calendar.backToCalendar')}
          </button>
        </div>
      </header>

      <section className="admin-section">
        <h2>{t('admin.whitelist.addTitle')}</h2>
        <form className="whitelist-form" onSubmit={handleSubmit}>
          <div className="field-group">
            <div className="field">
              <label htmlFor="email">{t('auth.email')}</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
                placeholder="user@example.com"
              />
            </div>
            <div className="field">
              <label htmlFor="name">{t('admin.whitelist.name')}</label>
              <input
                id="name"
                type="text"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                placeholder="Taro Yamada"
              />
            </div>
            <div className="field checkbox-field">
              <label>
                <input
                  type="checkbox"
                  checked={form.is_admin_default}
                  onChange={(e) => setForm({ ...form, is_admin_default: e.target.checked })}
                />
                {t('admin.whitelist.isAdmin')}
              </label>
            </div>
          </div>
          <button type="submit" className="button" disabled={isAdding}>
            {isAdding ? t('admin.whitelist.adding') : t('admin.whitelist.add')}
          </button>
        </form>
      </section>

      <section className="admin-section">
        <h2>{t('admin.whitelist.listTitle')}</h2>
        {isLoading ? (
          <p>{t('app.loading')}</p>
        ) : error ? (
          <p className="error-text">{t('app.error')}</p>
        ) : (
          <div className="table-container">
            <table className="whitelist-table">
              <thead>
                <tr>
                  <th>{t('auth.email')}</th>
                  <th>{t('admin.whitelist.name')}</th>
                  <th>{t('admin.whitelist.role')}</th>
                  <th>{t('admin.whitelist.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.email}</td>
                    <td>
                      {editingId === entry.id ? (
                        <input
                          type="text"
                          value={editForm.display_name}
                          onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                        />
                      ) : (
                        entry.display_name || '-'
                      )}
                    </td>
                    <td>
                      {editingId === entry.id ? (
                        <label>
                          <input
                            type="checkbox"
                            checked={editForm.is_admin_default}
                            onChange={(e) => setEditForm({ ...editForm, is_admin_default: e.target.checked })}
                          />
                          {t('admin.whitelist.isAdmin')}
                        </label>
                      ) : entry.is_admin_default ? (
                        <span className="badge admin">{t('auth.admin')}</span>
                      ) : (
                        <span className="badge member">{t('admin.whitelist.member')}</span>
                      )}
                    </td>
                    <td>
                      {editingId === entry.id ? (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button onClick={() => saveEditing(entry.id)} className="button small">
                            Save
                          </button>
                          <button onClick={cancelEditing} className="button ghost small">
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button onClick={() => startEditing(entry)} className="button ghost small">
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(entry.id)}
                            className="button danger small"
                          >
                            {t('admin.whitelist.delete')}
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {entries.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center' }}>
                      {t('admin.whitelist.noEntries')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
