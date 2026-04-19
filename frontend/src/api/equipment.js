import { http } from './http'

export async function fetchEquipmentTypes() {
  const response = await http.get('/equipment-types/')
  return response.data
}

export async function createEquipmentType(payload) {
  const response = await http.post('/equipment-types/', payload)
  return response.data
}

export async function updateEquipmentType(equipmentTypeId, payload) {
  const response = await http.patch(`/equipment-types/${equipmentTypeId}`, payload)
  return response.data
}

export async function deleteEquipmentType(equipmentTypeId) {
  await http.delete(`/equipment-types/${equipmentTypeId}`)
}

export async function fetchParameters() {
  const response = await http.get('/parameters/')
  return response.data
}

export async function createParameter(payload) {
  const response = await http.post('/parameters/', payload)
  return response.data
}

export async function updateParameter(parameterId, payload) {
  const response = await http.patch(`/parameters/${parameterId}`, payload)
  return response.data
}

export async function deleteParameter(parameterId) {
  await http.delete(`/parameters/${parameterId}`)
}

export async function fetchEquipmentList() {
  const [equipmentResponse, statesResponse] = await Promise.all([
    http.get('/equipment/'),
    http.get('/equipment-states/'),
  ])

  const statesByEquipmentId = new Map(
    statesResponse.data.map((item) => [item.equipment.id, item]),
  )

  return equipmentResponse.data.map((item) => {
    const monitoringState = statesByEquipmentId.get(item.id)

    return {
      ...item,
      monitoringStatus: monitoringState?.status ?? 'unknown',
      warningCount: monitoringState?.warning_count ?? 0,
      criticalCount: monitoringState?.critical_count ?? 0,
      lastEvaluatedAt: monitoringState?.last_evaluated_at ?? null,
    }
  })
}

export async function fetchEquipmentDetails(equipmentId) {
  const [equipmentResponse, stateResponse] = await Promise.all([
    http.get(`/equipment/${equipmentId}`),
    http.get(`/equipment-states/${equipmentId}`),
  ])

  return {
    ...equipmentResponse.data,
    monitoringState: stateResponse.data,
  }
}

export async function fetchEquipmentTypeParameterBindings(equipmentTypeId) {
  const response = await http.get('/equipment-type-parameters/', {
    params: {
      equipment_type_id: equipmentTypeId,
    },
  })

  return response.data
}

export async function fetchEquipmentTypeParameters(params = {}) {
  const response = await http.get('/equipment-type-parameters/', { params })
  return response.data
}

export async function createEquipmentTypeParameterBinding(payload) {
  const response = await http.post('/equipment-type-parameters/', payload)
  return response.data
}

export async function deleteEquipmentTypeParameterBinding(bindingId) {
  await http.delete(`/equipment-type-parameters/${bindingId}`)
}
