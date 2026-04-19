import { http } from './http'

export async function fetchPermissions() {
  const response = await http.get('/permissions/')
  return response.data
}
