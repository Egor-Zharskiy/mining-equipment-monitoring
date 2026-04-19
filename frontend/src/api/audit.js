import { http } from './http'

export async function fetchAuditLogs(params = {}) {
  const response = await http.get('/audit-logs/', { params })
  return response.data
}
