import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded'
import NorthEastRoundedIcon from '@mui/icons-material/NorthEastRounded'
import {
  Alert,
  Box,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { Link as RouterLink } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { fetchDashboardOverview, fetchEquipmentStatusAnalytics, fetchEventAnalytics } from '../api/dashboard'
import { fetchEvents } from '../api/events'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber, formatShortDate, formatStatusLabel } from '../utils/format'

const statusColors = {
  normal: '#2d8d67',
  warning: '#c68d2f',
  critical: '#b24b47',
}

const emptyOverview = {
  equipment: { total_count: 0, buckets: { warning: 0, critical: 0 } },
  events: { total_count: 0, buckets: { warning: 0 } },
  maintenance: { total_count: 0, buckets: { overdue: 0 } },
  notifications: { total_count: 0, buckets: { unread: 0 } },
}

const emptyEquipmentStatus = {
  by_status: {},
  by_type: [],
}

const emptyEventAnalytics = {
  period: null,
  by_severity: {},
  timeline: [],
}

function toDateKey(value) {
  return new Date(value).toISOString().slice(0, 10)
}

function buildSevenDayTimeline(points = [], period) {
  const pointMap = new Map(points.map((point) => [toDateKey(point.date), point.count]))
  const endDate = period?.date_to ? new Date(period.date_to) : new Date()
  const normalizedEndDate = new Date(endDate)
  normalizedEndDate.setHours(0, 0, 0, 0)

  return Array.from({ length: 7 }, (_, index) => {
    const currentDate = new Date(normalizedEndDate)
    currentDate.setDate(normalizedEndDate.getDate() - (6 - index))
    const key = toDateKey(currentDate)

    return {
      date: key,
      count: pointMap.get(key) ?? 0,
    }
  })
}

export function DashboardPage() {
  const { hasPermission } = useAuth()
  const canReadEquipment = hasPermission('equipment.read')
  const canReadEvents = hasPermission('events.read')
  const canReadMaintenance = hasPermission('maintenance.read')
  const canReadNotifications = hasPermission('notifications.read')

  const overviewQuery = useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: fetchDashboardOverview,
  })
  const statusQuery = useQuery({
    queryKey: ['dashboard', 'status'],
    queryFn: fetchEquipmentStatusAnalytics,
  })
  const eventsAnalyticsQuery = useQuery({
    queryKey: ['dashboard', 'events-analytics'],
    queryFn: () => fetchEventAnalytics(),
  })
  const recentEventsQuery = useQuery({
    queryKey: ['dashboard', 'recent-events'],
    queryFn: () => fetchEvents({ limit: 5 }),
    enabled: canReadEvents,
  })

  const overview = overviewQuery.data ?? emptyOverview
  const equipmentStatus = statusQuery.data ?? emptyEquipmentStatus
  const eventAnalytics = eventsAnalyticsQuery.data ?? emptyEventAnalytics
  const recentEvents = canReadEvents ? (recentEventsQuery.data ?? []) : []
  const hasDashboardError =
    overviewQuery.isError ||
    statusQuery.isError ||
    eventsAnalyticsQuery.isError ||
    (canReadEvents && recentEventsQuery.isError)
  const isInitialLoading =
    (overviewQuery.isLoading ||
      statusQuery.isLoading ||
      eventsAnalyticsQuery.isLoading) &&
    (!overviewQuery.data ||
      !statusQuery.data ||
      !eventsAnalyticsQuery.data)

  const workflowItems = [
    canReadEvents
      ? {
          title: '1. Проверить свежие события',
          description: 'Открыть журнал и быстро найти критичные или предупреждающие сигналы.',
          href: '/events',
        }
      : null,
    canReadEquipment
      ? {
          title: '2. Перейти к оборудованию',
          description: 'Из событий или напрямую открыть карточку единицы и посмотреть текущие параметры.',
          href: '/equipment',
        }
      : null,
    canReadMaintenance
      ? {
          title: '3. Открыть задачи ТО',
          description: 'Проверить очередь работ, назначение и статус выполнения.',
          href: '/maintenance',
        }
      : null,
    canReadNotifications
      ? {
          title: '4. Закрыть цикл уведомлениями',
          description: 'Проверить непрочитанные оповещения и зафиксировать действия пользователя.',
          href: '/notifications',
        }
      : null,
  ].filter(Boolean)

  const statusChartData = Object.entries(equipmentStatus.by_status).map(([key, value]) => ({
    color: statusColors[key] ?? '#8b9496',
    name: formatStatusLabel(key),
    value,
  }))

  const severityChartData = Object.entries(eventAnalytics.by_severity).map(([key, value]) => ({
    name: formatStatusLabel(key),
    value,
  }))
  const eventsTimelineData = buildSevenDayTimeline(eventAnalytics.timeline, eventAnalytics.period)

  if (isInitialLoading) {
    return (
      <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
        <PageHeader
          eyebrow="Мониторинг"
          title="Операционная панель"
          description="Загрузка аналитики, статусов оборудования и последних сигналов."
        />
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: {
              xs: '1fr',
              md: 'repeat(2, minmax(0, 1fr))',
              xl: 'repeat(4, minmax(0, 1fr))',
            },
          }}
        >
          {Array.from({ length: 4 }).map((_, index) => (
            <StatCard
              key={index}
              label={<Skeleton width={120} />}
              value={<Skeleton width={100} />}
              hint={<Skeleton width={180} />}
            />
          ))}
        </Box>
        <Box
          sx={{
            display: 'grid',
            gap: 3,
            gridTemplateColumns: { xs: '1fr', xl: '1.4fr 0.8fr' },
          }}
        >
          <SectionCard title="Динамика событий">
            <Skeleton height={300} variant="rounded" />
          </SectionCard>
          <SectionCard title="Распределение состояний парка">
            <Skeleton height={300} variant="rounded" />
          </SectionCard>
        </Box>
        <Box
          sx={{
            display: 'grid',
            gap: 3,
            gridTemplateColumns: { xs: '1fr', xl: '0.9fr 1.1fr' },
          }}
        >
          <SectionCard title="Критичность событий">
            <Skeleton height={260} variant="rounded" />
          </SectionCard>
          <SectionCard title="Последние сигналы">
            <Skeleton height={260} variant="rounded" />
          </SectionCard>
        </Box>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Мониторинг"
        title="Операционная панель"
        description="Быстро читаемая панель для контроля состояния парка, объема сигналов и ближайшей нагрузки по ТО."
        actions={
          canReadEquipment ? (
            <Button
              component={RouterLink}
              endIcon={<ArrowForwardRoundedIcon />}
              to="/equipment"
              variant="contained"
            >
              Открыть оборудование
            </Button>
          ) : null
        }
      />

      {hasDashboardError ? (
        <Alert severity="warning">
          Часть аналитических данных временно недоступна. Обновите страницу или проверьте права доступа пользователя.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            md: 'repeat(2, minmax(0, 1fr))',
            xl: 'repeat(4, minmax(0, 1fr))',
          },
        }}
      >
        <StatCard
          accent="primary.main"
          hint={`${overview.equipment.buckets.warning} предупреждений, ${overview.equipment.buckets.critical} критических`}
          label="Контролируемое оборудование"
          value={formatNumber(overview.equipment.total_count)}
        />
        <StatCard
          accent="error.main"
          hint={`${overview.events.buckets.warning} предупреждающих сигналов за 7 дней`}
          label="Зарегистрированные события"
          value={formatNumber(overview.events.total_count)}
        />
        <StatCard
          accent="secondary.main"
          hint={`${overview.maintenance.buckets.overdue} просроченных задач`}
          label="Очередь ТО"
          value={formatNumber(overview.maintenance.total_count)}
        />
        <StatCard
          accent="warning.main"
          hint={`${overview.notifications.buckets.unread} непрочитанных уведомлений`}
          label="Исходящие уведомления"
          value={formatNumber(overview.notifications.total_count)}
        />
      </Box>

      <Box
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', xl: '1.4fr 0.8fr' },
        }}
      >
        <SectionCard
          title="Динамика событий"
          subtitle="Семидневный ритм событий на основе аналитических данных."
        >
          {eventsTimelineData.length ? (
            <Box sx={{ height: 300, minWidth: 0, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={eventsTimelineData}>
                  <defs>
                    <linearGradient id="eventsGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#1d7565" stopOpacity={0.44} />
                      <stop offset="100%" stopColor="#1d7565" stopOpacity={0.04} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#d7dfdc" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tickFormatter={formatShortDate} tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(value) => [value, 'События']}
                    labelFormatter={(label) => formatDateTime(label)}
                  />
                  <Area
                    dataKey="count"
                    fill="url(#eventsGradient)"
                    stroke="#1d7565"
                    strokeWidth={3}
                    type="monotone"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          ) : (
            <EmptyState
              title="Динамика пока недоступна"
              description="За выбранный период нет событий, из которых можно построить временной ряд."
            />
          )}
        </SectionCard>

        <SectionCard
          title="Распределение состояний парка"
          subtitle="Текущее распределение состояний оборудования."
        >
          <Box sx={{ height: 300, minWidth: 0, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusChartData}
                  cx="50%"
                  cy="50%"
                  dataKey="value"
                  innerRadius={72}
                  outerRadius={104}
                  paddingAngle={4}
                >
                  {statusChartData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value, 'Ед.']} />
              </PieChart>
            </ResponsiveContainer>
          </Box>
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {statusChartData.map((item) => (
              <Box
                key={item.name}
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <Box sx={{ alignItems: 'center', display: 'flex', gap: 1 }}>
                  <Box
                    sx={{
                      backgroundColor: item.color,
                      borderRadius: '50%',
                      height: 10,
                      width: 10,
                    }}
                  />
                  <Typography>{item.name}</Typography>
                </Box>
                <Typography sx={{ fontWeight: 800 }}>{formatNumber(item.value)}</Typography>
              </Box>
            ))}
          </Box>
        </SectionCard>
      </Box>

      <SectionCard
        title="Рабочий маршрут"
        subtitle="Быстрый переход по ключевым разделам системы без лишних переходов по меню."
      >
        {workflowItems.length ? (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' },
            }}
          >
            {workflowItems.map((item) => (
              <Box
                key={item.href}
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 4,
                  display: 'grid',
                  gap: 1.25,
                  p: 2.5,
                }}
              >
                <Typography sx={{ fontWeight: 800 }}>{item.title}</Typography>
                <Typography color="text.secondary">{item.description}</Typography>
                <Box>
                  <Button component={RouterLink} endIcon={<NorthEastRoundedIcon />} to={item.href}>
                    Открыть модуль
                  </Button>
                </Box>
              </Box>
            ))}
          </Box>
        ) : (
          <EmptyState
            title="Доступные шаги не найдены"
            description="У текущего пользователя нет доступа к разделам этого маршрута. Используйте другую роль или откройте доступный модуль."
          />
        )}
      </SectionCard>

      <Box
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', xl: '0.9fr 1.1fr' },
        }}
      >
        <SectionCard
          title="Критичность событий"
          subtitle="Разбивка объема событий по уровням критичности."
        >
          <Box sx={{ height: 260, minWidth: 0, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityChartData} layout="vertical">
                <CartesianGrid stroke="#d7dfdc" strokeDasharray="3 3" horizontal={false} />
                <XAxis allowDecimals={false} type="number" tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" tickLine={false} axisLine={false} width={90} />
                <Tooltip formatter={(value) => [value, 'События']} />
                <Bar dataKey="value" radius={[0, 12, 12, 0]} fill="#cb7a33" />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </SectionCard>

        <SectionCard
          title="Последние сигналы"
          subtitle="Актуальные инциденты мониторинга для оперативного просмотра."
          action={
            canReadEvents ? (
              <Button component={RouterLink} endIcon={<NorthEastRoundedIcon />} to="/events">
                Открыть журнал
              </Button>
            ) : null
          }
        >
          {!canReadEvents ? (
            <EmptyState
              title="Журнал событий скрыт"
              description="У текущего пользователя нет доступа `events.read`, поэтому блок последних сигналов не отображает данные."
            />
          ) : recentEventsQuery.isPending && !recentEventsQuery.data ? (
            <Skeleton height={260} variant="rounded" />
          ) : recentEvents.length ? (
            <List disablePadding>
              {recentEvents.map((event, index) => (
                <Box key={event.id}>
                  <ListItem disableGutters sx={{ alignItems: 'flex-start', px: 0 }}>
                    <ListItemText
                      primaryTypographyProps={{ component: 'div' }}
                      secondaryTypographyProps={{ component: 'div' }}
                      primary={
                        <Box
                          sx={{
                            alignItems: 'center',
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: 1,
                            mb: 0.5,
                          }}
                        >
                          <Typography sx={{ fontWeight: 800 }}>{event.title}</Typography>
                          <StatusChip value={event.severity} />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography color="text.secondary" sx={{ mb: 0.75 }}>
                            {event.message}
                          </Typography>
                          <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                            {event.equipment.name} • {formatDateTime(event.created_at)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < recentEvents.length - 1 ? <Divider /> : null}
                </Box>
              ))}
            </List>
          ) : (
            <EmptyState
              title="Событий пока нет"
              description="Когда в системе появятся инциденты мониторинга, последние записи будут показаны здесь."
            />
          )}
        </SectionCard>
      </Box>

      <SectionCard
        title="Разбивка по типам оборудования"
        subtitle="Где по парку концентрируются предупреждения и критические отклонения."
      >
        <Box sx={{ display: 'grid', gap: 2 }}>
          {equipmentStatus.by_type.map((item) => (
            <Box
              key={item.equipment_type_id}
              sx={{
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 4,
                p: 2.5,
              }}
            >
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 1.5,
                  justifyContent: 'space-between',
                  mb: 1.5,
                }}
              >
                <Typography sx={{ fontWeight: 800 }}>{item.equipment_type_name}</Typography>
                <Typography color="text.secondary">
                  {formatNumber(item.total_count)} ед. под мониторингом
                </Typography>
              </Box>
              <Box
                sx={{
                  display: 'grid',
                  gap: 1,
                  gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
                }}
              >
                {Object.entries(item.by_status).map(([key, value]) => (
                  <Box
                    key={key}
                    sx={{
                      backgroundColor: 'background.default',
                      borderRadius: 3,
                      p: 1.5,
                    }}
                  >
                    <Typography color="text.secondary" sx={{ fontSize: 13, mb: 0.5 }}>
                      {formatStatusLabel(key)}
                    </Typography>
                    <Typography sx={{ fontSize: 24, fontWeight: 800 }}>
                      {formatNumber(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          ))}
        </Box>
      </SectionCard>
    </Box>
  )
}
