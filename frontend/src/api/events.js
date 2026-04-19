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

export async function createMaintenanceTaskFromEvent(eventId, payload) {
  const response = await http.post(`/events/${eventId}/maintenance-task`, payload)
  return response.data
}
