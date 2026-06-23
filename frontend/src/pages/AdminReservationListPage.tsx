import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { useNavigate } from 'react-router-dom'
import { getVideoUrl, updateVideoUrl } from '../api/systemSettings'

type Reservation = {
  id: number
  userId: number
  user?: { displayName?: string; email: string }
  statusUpdatedBy?: { displayName?: string; email: string } | null
  status: string
  visibility: string
  purpose: string
  displayMessage?: string
  description?: string
  cancellationReason?: string
  rejectionReason?: string
  attendeeCount: number
  notifyApplicant: boolean
  startTime: string
  endTime: string
  createdAt: string
  updatedAt: string
}

export function AdminReservationListPage() {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [loading, setLoading] = useState(true)
  const [rejectionReason, setRejectionReason] = useState<{[key: number]: string}>({})
  const [approvalMessage, setApprovalMessage] = useState<{[key: number]: string}>({})
  const [videoUrl, setVideoUrl] = useState('')
  const [newVideoUrl, setNewVideoUrl] = useState('')
  const [exportStatus, setExportStatus] = useState('')
  const [exportStartFrom, setExportStartFrom] = useState('')
  const [exportStartTo, setExportStartTo] = useState('')
  const [exportStatusFilter, setExportStatusFilter] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchReservations()
    fetchVideoUrl()
  }, [])

  const fetchVideoUrl = async () => {
    try {
      const url = await getVideoUrl()
      setVideoUrl(url)
      setNewVideoUrl(url)
    } catch (error) {
      console.error('Failed to fetch video URL', error)
    }
  }

  const handleUpdateVideoUrl = async () => {
    try {
      await updateVideoUrl(newVideoUrl)
      setVideoUrl(newVideoUrl)
      alert('動画URLを更新しました')
    } catch (error) {
      alert('動画URLの更新に失敗しました')
    }
  }

  const handleExportCsv = async () => {
    try {
      setExportStatus('ダウンロード中...')
      const params = new URLSearchParams()
      if (exportStatusFilter) params.append('status', exportStatusFilter)
      if (exportStartFrom) params.append('startFrom', new Date(exportStartFrom).toISOString())
      if (exportStartTo) params.append('startTo', new Date(exportStartTo).toISOString())

      const res = await apiClient.get(`/api/admin/reservations/export?${params.toString()}`, {
        responseType: 'blob',
      })

      // Extract filename from Content-Disposition header or use default
      const disposition = res.headers['content-disposition']
      let filename = 'reservations.csv'
      if (disposition) {
        const match = disposition.match(/filename="?(.+?)"?$/)
        if (match) filename = match[1]
      }

      // Trigger download
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setExportStatus('ダウンロード完了')
      setTimeout(() => setExportStatus(''), 3000)
    } catch (error) {
      console.error('Export failed', error)
      setExportStatus('エクスポートに失敗しました')
      setTimeout(() => setExportStatus(''), 3000)
    }
  }

  const fetchReservations = async () => {
    try {
      const res = await apiClient.get('/api/reservations')
      setReservations(res.data.reservations)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (id: number, status: 'approved' | 'rejected' | 'cancelled') => {
    let actionName = ''
    if (status === 'approved') actionName = '承認'
    else if (status === 'rejected') actionName = '却下'
    else if (status === 'cancelled') actionName = 'キャンセル承認'

    if (!window.confirm(`本当にこの予約を${actionName}しますか？`)) {
      return
    }
    try {
      const payload: any = { status }
      if (status === 'rejected') {
        payload.rejectionReason = rejectionReason[id] || ''
      } else if (status === 'approved' || status === 'cancelled') {
        payload.approvalMessage = approvalMessage[id] || ''
      }
      await apiClient.patch(`/api/admin/reservations/${id}/status`, payload)
      fetchReservations()
    } catch (error) {
      alert('更新に失敗しました')
    }
  }

  if (loading) return <div className="page"><div className="page-body"><div className="loading"><div className="spinner" /><p>読み込み中...</p></div></div></div>

  const pendingReservations = reservations.filter(r => r.status === 'pending')
  const cancellationRequests = reservations.filter(r => r.status === 'cancellation_requested')
  const otherReservations = reservations
    .filter(r => r.status !== 'pending' && r.status !== 'cancellation_requested')
    .sort((a, b) => {
      const aTime = new Date(a.updatedAt || a.createdAt).getTime()
      const bTime = new Date(b.updatedAt || b.createdAt).getTime()
      return bTime - aTime
    })
  const getAdminName = (reservation: Reservation) =>
    reservation.statusUpdatedBy?.displayName || reservation.statusUpdatedBy?.email || '未記録'

  return (
    <div className="page">
      <div className="page-body">
      <header className="page-header">
        <h1>予約申請一覧</h1>
        <button className="button ghost" onClick={() => navigate('/')}>戻る</button>
      </header>

      <section style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
        <h2 style={{ marginTop: 0 }}>システム設定</h2>
        <div className="field">
            <label htmlFor="videoUrl">トップページ動画URL (YouTube)</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                    id="videoUrl"
                    type="text" 
                    value={newVideoUrl} 
                    onChange={(e) => setNewVideoUrl(e.target.value)}
                    style={{ flex: 1, padding: '0.5rem' }}
                    placeholder="https://youtu.be/..."
                />
                <button className="button" onClick={handleUpdateVideoUrl}>更新</button>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
                現在の設定: {videoUrl}
            </p>
        </div>
      </section>

      <section style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#f0fdf4', borderRadius: '8px' }}>
        <h2 style={{ marginTop: 0 }}>📊 予約データ エクスポート</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="field" style={{ minWidth: '150px' }}>
            <label htmlFor="exportStatus">ステータス</label>
            <select
              id="exportStatus"
              value={exportStatusFilter}
              onChange={(e) => setExportStatusFilter(e.target.value)}
              style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc', width: '100%' }}
            >
              <option value="">すべて</option>
              <option value="pending">申請中</option>
              <option value="approved">承認済み</option>
              <option value="rejected">却下</option>
              <option value="cancelled">キャンセル済み</option>
              <option value="cancellation_requested">キャンセル申請中</option>
            </select>
          </div>
          <div className="field" style={{ minWidth: '160px' }}>
            <label htmlFor="exportStartFrom">いつから (From)</label>
            <input
              id="exportStartFrom"
              type="date"
              value={exportStartFrom}
              onChange={(e) => setExportStartFrom(e.target.value)}
              style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc', width: '100%' }}
            />
          </div>
          <div className="field" style={{ minWidth: '160px' }}>
            <label htmlFor="exportStartTo">いつまで (To)</label>
            <input
              id="exportStartTo"
              type="date"
              value={exportStartTo}
              onChange={(e) => setExportStartTo(e.target.value)}
              style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc', width: '100%' }}
            />
          </div>
          <button
            className="button"
            onClick={handleExportCsv}
            style={{ height: 'fit-content', whiteSpace: 'nowrap' }}
          >
            📥 CSVダウンロード
          </button>
          {exportStatus && (
            <span style={{ fontSize: '0.85rem', color: exportStatus.includes('失敗') ? '#dc2626' : '#16a34a' }}>
              {exportStatus}
            </span>
          )}
        </div>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
          日付を指定しない場合は全期間を出力します。ダウンロードしたCSVはExcelやGoogleスプレッドシートで開けます
        </p>
      </section>
      
      <section>
        <h2>キャンセル申請</h2>
        {cancellationRequests.length === 0 ? <p>キャンセル申請はありません</p> : (
          <div className="reservation-list" style={{ display: 'grid', gap: '1rem' }}>
            {cancellationRequests.map(r => (
              <div key={r.id} className="card" style={{ padding: '1rem', border: '1px solid #fca5a5', borderRadius: '8px', backgroundColor: '#fff1f2' }}>
                <h3>{r.purpose} (キャンセル申請)</h3>
                <p><strong>申請者:</strong> {r.user?.displayName || '未設定'} ({r.user?.email || 'Unknown'})</p>
                <p><strong>利用日時:</strong> {new Date(r.startTime).toLocaleString()} - {new Date(r.endTime).toLocaleString()}</p>
                <p><strong>詳細:</strong> {r.description}</p>
                <p><strong>申請者メール通知:</strong> {r.notifyApplicant ? '希望あり' : '希望なし'}</p>
                {r.cancellationReason && <p style={{ color: '#b91c1c' }}><strong>キャンセル理由:</strong> {r.cancellationReason}</p>}
                
                <div className="actions" style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
                        <input 
                            type="text" 
                            placeholder="メッセージ (承認/却下共通)" 
                            value={approvalMessage[r.id] || ''}
                            onChange={e => setApprovalMessage({...approvalMessage, [r.id]: e.target.value})}
                            style={{ padding: '0.5rem', width: '100%' }}
                        />
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button className="button" onClick={() => handleStatusUpdate(r.id, 'cancelled')}>キャンセルを承認</button>
                            <button className="button ghost" onClick={() => handleStatusUpdate(r.id, 'approved')}>キャンセルを却下（元に戻す）</button>
                        </div>
                    </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: '2rem' }}>
        <h2>新規予約申請</h2>
        {pendingReservations.length === 0 ? <p>申請中の予約はありません</p> : (
          <div className="reservation-list" style={{ display: 'grid', gap: '1rem' }}>
            {pendingReservations.map(r => (
              <div key={r.id} className="card" style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
                <h3>{r.purpose}</h3>
                <p><strong>申請者:</strong> {r.user?.displayName || '未設定'} ({r.user?.email || 'Unknown'})</p>
                <p><strong>申請日時:</strong> {new Date(r.createdAt).toLocaleString()}</p>
                <p><strong>利用日時:</strong> {new Date(r.startTime).toLocaleString()} - {new Date(r.endTime).toLocaleString()}</p>
                <p><strong>人数:</strong> {r.attendeeCount}人</p>
                <p><strong>詳細:</strong> {r.description}</p>
                <p><strong>公開設定:</strong> {r.visibility === 'public' ? '公開' : '匿名'}</p>
                <p><strong>申請者メール通知:</strong> {r.notifyApplicant ? '希望あり' : '希望なし'}</p>
                {r.visibility === 'public' && <p><strong>表示メッセージ:</strong> {r.displayMessage}</p>}
                
                <div className="actions" style={{ marginTop: '1rem', display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <input 
                      type="text" 
                      placeholder="承認メッセージ" 
                      value={approvalMessage[r.id] || ''}
                      onChange={e => setApprovalMessage({...approvalMessage, [r.id]: e.target.value})}
                      style={{ padding: '0.5rem' }}
                    />
                    <button className="button" onClick={() => handleStatusUpdate(r.id, 'approved')}>承認</button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <input 
                      type="text" 
                      placeholder="却下理由" 
                      value={rejectionReason[r.id] || ''}
                      onChange={e => setRejectionReason({...rejectionReason, [r.id]: e.target.value})}
                      style={{ padding: '0.5rem' }}
                    />
                    <button className="button danger" style={{ backgroundColor: '#ef4444', color: 'white' }} onClick={() => handleStatusUpdate(r.id, 'rejected')}>却下</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: '2rem' }}>
        <h2>過去の予約・処理済み</h2>
        <div className="reservation-list" style={{ display: 'grid', gap: '1rem' }}>
            {otherReservations.map(r => (
              <div key={r.id} className="card" style={{ padding: '1rem', border: '1px solid #eee', borderRadius: '8px', opacity: 0.7 }}>
                <h3>{r.purpose} - {r.status}</h3>
                <p><strong>申請者:</strong> {r.user?.displayName || '未設定'} ({r.user?.email})</p>
                <p><strong>利用日時:</strong> {new Date(r.startTime).toLocaleString()}</p>
                <p><strong>担当した管理者:</strong> {getAdminName(r)}</p>
                {r.status === 'rejected' && <p style={{ color: 'red' }}>理由: {r.rejectionReason}</p>}
              </div>
            ))}
        </div>
      </section>
      </div>
    </div>
  )
}
