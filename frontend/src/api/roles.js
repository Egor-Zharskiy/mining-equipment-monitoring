import { http } from './http'

export async function fetchRoles() {
  const response = await http.get('/roles/')
  return response.data
}

export async function createRole(payload) {
  const response = await http.post('/roles/', payload)
  return response.data
}
