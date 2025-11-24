import { apiClient } from './client'

export type WhitelistEntry = {
  id: number
  email: string
  display_name: string | null
  is_admin_default: boolean
  created_at: string
}

export type CreateWhitelistPayload = {
  email: string
  display_name?: string
  is_admin_default?: boolean
}

export type UpdateWhitelistPayload = Partial<CreateWhitelistPayload>

export async function fetchWhitelist(): Promise<WhitelistEntry[]> {
  const response = await apiClient.get<{ entries: WhitelistEntry[] }>('/api/admin/whitelist')
  return response.data.entries
}

export async function createWhitelistEntry(payload: CreateWhitelistPayload): Promise<WhitelistEntry> {
  const response = await apiClient.post<{ entry: WhitelistEntry }>('/api/admin/whitelist', payload)
  return response.data.entry
}

export async function updateWhitelistEntry(id: number, payload: UpdateWhitelistPayload): Promise<WhitelistEntry> {
  const response = await apiClient.put<{ entry: WhitelistEntry }>(`/api/admin/whitelist/${id}`, payload)
  return response.data.entry
}

export async function deleteWhitelistEntry(id: number): Promise<void> {
  await apiClient.delete(`/api/admin/whitelist/${id}`)
}
