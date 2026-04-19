import { http } from './http'

export async function createTelemetryReading(payload) {
  const response = await http.post('/telemetry-readings/', payload)
  return response.data
}
