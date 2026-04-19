import { http } from './http'

export async function fetchThresholdRules(params = {}) {
  const response = await http.get('/threshold-rules/', { params })
  return response.data
}

export async function createThresholdRule(payload) {
  const response = await http.post('/threshold-rules/', payload)
  return response.data
}

export async function updateThresholdRule(ruleId, payload) {
  const response = await http.patch(`/threshold-rules/${ruleId}`, payload)
  return response.data
}

export async function deleteThresholdRule(ruleId) {
  await http.delete(`/threshold-rules/${ruleId}`)
}
