import { http } from './http'

function toIsoDateTime(value) {
  return value.toISOString()
}

export async function fetchDashboardOverview() {
  const response = await http.get('/analytics/overview', {
    params: { days: 7 },
  })
  return response.data
}

export async function fetchEquipmentStatusAnalytics() {
  const response = await http.get('/analytics/equipment-status')
  return response.data
}

export async function fetchEventAnalytics(days = 7) {
  const resolvedDays = typeof days === 'number' && Number.isFinite(days) ? days : 7
  const dateTo = new Date()
  const dateFrom = new Date(dateTo)
  dateFrom.setDate(dateFrom.getDate() - (resolvedDays - 1))
  dateFrom.setHours(0, 0, 0, 0)

  const response = await http.get('/analytics/events', {
    params: {
      date_from: toIsoDateTime(dateFrom),
      date_to: toIsoDateTime(dateTo),
    },
  })
  return response.data
}

export async function fetchTelemetryHistory({ equipmentId, parameterId, limit = 50 }) {
  const response = await http.get('/analytics/telemetry-history', {
    params: {
      equipment_id: equipmentId,
      parameter_id: parameterId,
      limit,
    },
  })

  return response.data
}
