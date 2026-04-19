import { http } from './http'

export async function fetchNotifications(params = {}) {
  const response = await http.get('/notifications/', { params })
  return response.data
}

export async function fetchUnreadNotificationCount(params = {}) {
  const response = await http.get('/notifications/unread-count', { params })
  return response.data
}

export async function markNotificationAsRead(notificationId) {
  const response = await http.post(`/notifications/${notificationId}/read`)
  return response.data
}

export async function createManualNotification(payload) {
  const response = await http.post('/notifications/manual', payload)
  return response.data
}
