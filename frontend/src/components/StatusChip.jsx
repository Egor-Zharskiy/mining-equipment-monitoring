import { Chip } from '@mui/material'

const statusConfig = {
  critical: { label: 'Критично', color: 'error' },
  warning: { label: 'Предупреждение', color: 'warning' },
  normal: { label: 'Норма', color: 'success' },
  info: { label: 'Инфо', color: 'info' },
  planned: { label: 'Запланировано', color: 'default' },
  open: { label: 'Открыта', color: 'default' },
  in_progress: { label: 'В работе', color: 'secondary' },
  done: { label: 'Выполнено', color: 'success' },
  completed: { label: 'Завершено', color: 'success' },
  cancelled: { label: 'Отменено', color: 'default' },
  read: { label: 'Прочитано', color: 'success' },
  unread: { label: 'Непрочитано', color: 'warning' },
  high: { label: 'Высокий', color: 'error' },
  medium: { label: 'Средний', color: 'warning' },
  low: { label: 'Низкий', color: 'success' },
  internal: { label: 'Внутренний', color: 'primary' },
  email: { label: 'Email', color: 'secondary' },
  active: { label: 'Активен', color: 'success' },
  inactive: { label: 'Неактивен', color: 'default' },
  unknown: { label: 'Неизвестно', color: 'default' },
}

function humanize(value) {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function StatusChip({ value, size = 'small' }) {
  const normalized = String(value ?? 'unknown').toLowerCase()
  const config = statusConfig[normalized]

  return (
    <Chip
      color={config?.color ?? 'default'}
      label={config?.label ?? humanize(normalized)}
      size={size}
      variant={config?.color === 'default' ? 'outlined' : 'filled'}
    />
  )
}
