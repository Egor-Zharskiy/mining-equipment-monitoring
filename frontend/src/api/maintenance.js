import { http } from './http'

export async function fetchMaintenanceTasks(params = {}) {
  const response = await http.get('/maintenance-tasks/', { params })
  return response.data
}

export async function fetchMaintenanceRecords(params = {}) {
  const response = await http.get('/maintenance-records/', { params })
  return response.data
}

export async function fetchMaintenanceRecord(recordId) {
  const response = await http.get(`/maintenance-records/${recordId}`)
  return response.data
}

export async function fetchMaintenancePlans(params = {}) {
  const response = await http.get('/maintenance-plans/', { params })
  return response.data
}

export async function createMaintenancePlan(payload) {
  const response = await http.post('/maintenance-plans/', payload)
  return response.data
}

export async function updateMaintenancePlan(planId, payload) {
  const response = await http.patch(`/maintenance-plans/${planId}`, payload)
  return response.data
}

export async function deleteMaintenancePlan(planId) {
  await http.delete(`/maintenance-plans/${planId}`)
}

export async function createMaintenanceTask(payload) {
  const response = await http.post('/maintenance-tasks/', payload)
  return response.data
}

export async function updateMaintenanceTask(taskId, payload) {
  const response = await http.patch(`/maintenance-tasks/${taskId}`, payload)
  return response.data
}

export async function completeMaintenanceTask(taskId, payload) {
  const response = await http.post(`/maintenance-tasks/${taskId}/complete`, payload)
  return response.data
}
