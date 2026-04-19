import { http } from './http'

export async function fetchEvents(params = {}) {
  const response = await http.get('/events/', {
    params: {
      limit: 25,
      ...params,
    },
  })

  return response.data
}
