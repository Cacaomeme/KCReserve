import { apiClient } from './client'

export async function getVideoUrl(): Promise<string> {
  const response = await apiClient.get('/api/system-settings/video-url')
  return response.data.video_url
}

export async function updateVideoUrl(videoUrl: string): Promise<void> {
  await apiClient.put('/api/system-settings/video-url', { video_url: videoUrl })
}
