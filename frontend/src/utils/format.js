export function formatDateTime(value) {
  if (!value) {
    return 'Нет данных'
  }

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatShortDate(value) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
  }).format(new Date(value))
}

export function formatNumber(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return 'Нет данных'
  }

  return new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 1,
    ...options,
  }).format(Number(value))
}

export function getUserInitials(user) {
  if (!user) {
    return 'НД'
  }

  return `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase()
}

const eventTypeLabels = {
  parameter_warning: 'Предупреждение по параметру',
  parameter_critical: 'Критическое отклонение параметра',
  equipment_warning: 'Предупреждение по оборудованию',
  equipment_critical: 'Критическое состояние оборудования',
  equipment_recovered: 'Восстановление оборудования',
  maintenance_due: 'Срок ТО наступил',
  maintenance_needed: 'Требуется ТО',
  event_warning: 'Предупреждение',
  event_critical: 'Критическое событие',
  event_recovery: 'Восстановление',
}

const statusLabels = {
  critical: 'Критично',
  warning: 'Предупреждение',
  normal: 'Норма',
  info: 'Инфо',
  recovery: 'Восстановление',
  overdue: 'Просрочено',
  due_today: 'На сегодня',
  planned: 'Запланировано',
  unread: 'Непрочитано',
  internal: 'Внутренние',
  email: 'Email',
}

const specificationLabels = {
  engine_power_kw: 'Мощность двигателя, кВт',
  bucket_capacity_m3: 'Объем ковша, м3',
  weight_tons: 'Масса, т',
  payload_tons: 'Грузоподъемность, т',
  tire_size: 'Размер шин',
  drill_depth_m: 'Глубина бурения, м',
  compressor_bar: 'Давление компрессора, бар',
  mast_height_m: 'Высота мачты, м',
  cycle_target_min: 'Целевой цикл, мин',
}

export function formatEventType(value) {
  return eventTypeLabels[value] ?? value
}

export function formatStatusLabel(value) {
  return statusLabels[value] ?? value
}

export function formatSpecificationLabel(value) {
  return specificationLabels[value] ?? value
}

export function formatNotificationType(value) {
  return eventTypeLabels[value] ?? value
}
