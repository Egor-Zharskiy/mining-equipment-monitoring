import ManageSearchRoundedIcon from '@mui/icons-material/ManageSearchRounded'
import {
  Alert,
  Box,
  Button,
  MenuItem,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchAuditLogs } from '../api/audit'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { formatDateTime, formatNumber } from '../utils/format'

const resourceTypeOptions = [
  'auth',
  'equipment',
  'equipment_types',
  'equipment_type_parameters',
  'maintenance_tasks',
  'notifications',
  'parameters',
  'roles',
  'telemetry_readings',
  'threshold_rules',
  'users',
]

const actionLabels = {
  create: 'Создание',
  delete: 'Удаление',
  login: 'Вход',
  mark_read: 'Прочтение',
  update: 'Обновление',
}

const resourceLabels = {
  auth: 'Аутентификация',
  equipment: 'Оборудование',
  equipment_types: 'Типы оборудования',
  equipment_type_parameters: 'Параметры типов',
  maintenance_tasks: 'Задачи ТО',
  notifications: 'Уведомления',
  parameters: 'Параметры',
  roles: 'Роли',
  telemetry_readings: 'Телеметрия',
  threshold_rules: 'Пороговые правила',
  users: 'Пользователи',
}

function formatActor(actor) {
  if (!actor) {
    return 'Система'
  }

  return `${actor.first_name} ${actor.last_name}`
}

function formatDetails(details) {
  if (!details) {
    return 'Нет деталей'
  }

  return JSON.stringify(details, null, 2)
}

export function AuditLogsPage() {
  const [actionFilter, setActionFilter] = useState('')
  const [resourceTypeFilter, setResourceTypeFilter] = useState('')
  const [limit, setLimit] = useState('100')

  const auditLogsQuery = useQuery({
    queryKey: ['audit-logs', actionFilter, resourceTypeFilter, limit],
    queryFn: () =>
      fetchAuditLogs({
        ...(actionFilter ? { action: actionFilter } : {}),
        ...(resourceTypeFilter ? { resource_type: resourceTypeFilter } : {}),
        limit,
      }),
  })

  const logs = auditLogsQuery.data ?? []
  const actionOptions = Array.from(new Set(logs.map((item) => item.action))).sort()
  const successCount = logs.filter((item) => item.status_code >= 200 && item.status_code < 300).length
  const writeCount = logs.filter((item) => ['create', 'update', 'delete'].includes(item.action)).length
  const isInitialLoading = auditLogsQuery.isLoading && logs.length === 0

  function resetFilters() {
    setActionFilter('')
    setResourceTypeFilter('')
    setLimit('100')
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Администрирование"
        title="Журнал аудита"
        description="История значимых действий пользователей: входы, изменения справочников, телеметрия, уведомления и задачи ТО."
        actions={
          <Button onClick={resetFilters} startIcon={<ManageSearchRoundedIcon />} variant="outlined">
            Сбросить фильтры
          </Button>
        }
      />

      {auditLogsQuery.isError ? (
        <Alert severity="warning">
          Не удалось загрузить журнал аудита. Проверьте право `audit.read` и доступность API.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Записей в выборке" value={formatNumber(logs.length)} />
        <StatCard accent="success.main" label="Успешные действия" value={formatNumber(successCount)} />
        <StatCard accent="warning.main" label="Изменения данных" value={formatNumber(writeCount)} />
      </Box>

      <SectionCard
        title="События аудита"
        subtitle="Фильтры помогают быстро показать, кто создавал телеметрию, менял справочники или работал с уведомлениями."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Действие"
              onChange={(event) => setActionFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={actionFilter}
            >
              <MenuItem value="">Все действия</MenuItem>
              {[...new Set([...Object.keys(actionLabels), ...actionOptions])].sort().map((action) => (
                <MenuItem key={action} value={action}>
                  {actionLabels[action] ?? action}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Ресурс"
              onChange={(event) => setResourceTypeFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={resourceTypeFilter}
            >
              <MenuItem value="">Все ресурсы</MenuItem>
              {resourceTypeOptions.map((resourceType) => (
                <MenuItem key={resourceType} value={resourceType}>
                  {resourceLabels[resourceType] ?? resourceType}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Лимит"
              onChange={(event) => setLimit(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 140 }}
              value={limit}
            >
              <MenuItem value="50">50</MenuItem>
              <MenuItem value="100">100</MenuItem>
              <MenuItem value="200">200</MenuItem>
              <MenuItem value="500">500</MenuItem>
            </TextField>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} height={76} variant="rounded" />
            ))}
          </Box>
        ) : logs.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 1040 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Время</TableCell>
                  <TableCell>Пользователь</TableCell>
                  <TableCell>Действие</TableCell>
                  <TableCell>Ресурс</TableCell>
                  <TableCell>HTTP</TableCell>
                  <TableCell>Детали</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{formatDateTime(log.created_at)}</TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{formatActor(log.actor_user)}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {log.actor_user?.id ?? 'system'}
                      </Typography>
                    </TableCell>
                    <TableCell>{actionLabels[log.action] ?? log.action}</TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 700 }}>
                        {resourceLabels[log.resource_type] ?? log.resource_type}
                      </Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {log.resource_id ?? 'без объекта'}
                      </Typography>
                    </TableCell>
                    <TableCell>{log.status_code}</TableCell>
                    <TableCell>
                      <Box
                        component="pre"
                        sx={{
                          bgcolor: 'background.default',
                          borderRadius: 2,
                          fontFamily: 'monospace',
                          fontSize: 12,
                          m: 0,
                          maxHeight: 120,
                          maxWidth: 360,
                          overflow: 'auto',
                          p: 1.5,
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {formatDetails(log.details)}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="Записи аудита не найдены"
            description="По текущим фильтрам журнал пуст. Сбросьте фильтры или выполните действие в системе."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>
    </Box>
  )
}
