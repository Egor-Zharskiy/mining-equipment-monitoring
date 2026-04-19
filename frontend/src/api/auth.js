import { http } from './http'

export async function loginRequest(credentials) {
  const response = await http.post('/auth/login', credentials)
  return response.data
}

export async function getCurrentUser(accessToken) {
  const response = await http.get('/users/me', {
    headers: accessToken
      ? { Authorization: `Bearer ${accessToken}` }
      : undefined,
  })

  return response.data
}
