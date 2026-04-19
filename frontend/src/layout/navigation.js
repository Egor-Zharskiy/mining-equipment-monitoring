import CategoryRoundedIcon from '@mui/icons-material/CategoryRounded'
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded'
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded'
import EventRepeatRoundedIcon from '@mui/icons-material/EventRepeatRounded'
import ManageSearchRoundedIcon from '@mui/icons-material/ManageSearchRounded'
import NotificationsRoundedIcon from '@mui/icons-material/NotificationsRounded'
import PeopleRoundedIcon from '@mui/icons-material/PeopleRounded'
import PrecisionManufacturingRoundedIcon from '@mui/icons-material/PrecisionManufacturingRounded'
import RuleRoundedIcon from '@mui/icons-material/RuleRounded'
import SecurityRoundedIcon from '@mui/icons-material/SecurityRounded'
import AssignmentTurnedInRoundedIcon from '@mui/icons-material/AssignmentTurnedInRounded'
import TaskAltRoundedIcon from '@mui/icons-material/TaskAltRounded'

export const navigationItems = [
  {
    label: 'Панель мониторинга',
    description: 'Оперативный обзор, статус парка и ключевые сигналы.',
    href: '/dashboard',
    icon: DashboardRoundedIcon,
    requiredPermissions: ['analytics.read'],
  },
  {
    label: 'Список оборудования',
    description: 'Каталог контролируемых единиц техники.',
    href: '/equipment',
    icon: PrecisionManufacturingRoundedIcon,
    requiredPermissions: ['equipment.read'],
  },
  {
    label: 'События',
    description: 'Журнал событий мониторинга и разбивка по критичности.',
    href: '/events',
    icon: EventNoteRoundedIcon,
    requiredPermissions: ['events.read'],
  },
  {
    label: 'Задачи ТО',
    description: 'Очередь работ на проверку и корректирующие действия.',
    href: '/maintenance',
    icon: TaskAltRoundedIcon,
    requiredPermissions: ['maintenance.read'],
  },
  {
    label: 'История ТО',
    description: 'Журнал выполненных работ и результатов обслуживания.',
    href: '/maintenance-records',
    icon: AssignmentTurnedInRoundedIcon,
    requiredPermissions: ['maintenance.read'],
  },
  {
    label: 'Планы ТО',
    description: 'Регламенты обслуживания по типам оборудования и единицам техники.',
    href: '/maintenance-plans',
    icon: EventRepeatRoundedIcon,
    requiredPermissions: ['maintenance.read'],
  },
  {
    label: 'Уведомления',
    description: 'Оповещения, напоминания и дальнейшие действия операторов.',
    href: '/notifications',
    icon: NotificationsRoundedIcon,
    requiredPermissions: ['notifications.read'],
  },
  {
    label: 'Пользователи',
    description: 'Управление учетными записями, ролями и активностью пользователей.',
    href: '/admin/users',
    icon: PeopleRoundedIcon,
    requiredPermissions: ['users.read'],
  },
  {
    label: 'Роли и права',
    description: 'Создание ролей и управление наборами прав доступа.',
    href: '/admin/roles',
    icon: SecurityRoundedIcon,
    requiredPermissions: ['roles.read'],
  },
  {
    label: 'Справочники',
    description: 'Типы оборудования, параметры и связи для телеметрии.',
    href: '/admin/catalogs',
    icon: CategoryRoundedIcon,
    requiredPermissions: ['equipment.read'],
  },
  {
    label: 'Пороговые правила',
    description: 'Границы warning и critical для оценки телеметрии.',
    href: '/admin/threshold-rules',
    icon: RuleRoundedIcon,
    requiredPermissions: ['threshold_rules.read'],
  },
  {
    label: 'Журнал аудита',
    description: 'История входов, изменений и действий пользователей.',
    href: '/admin/audit-logs',
    icon: ManageSearchRoundedIcon,
    requiredPermissions: ['audit.read'],
  },
]
