import { http } from './http'

export async function fetchUsers() {
  const response = await http.get('/users/')
  return response.data
}

export async function createUser(payload) {
  const response = await http.post('/users/', payload)
  return response.data
}

export async function updateUser(userId, payload) {
  const response = await http.patch(`/users/${userId}`, payload)
  return response.data
}
