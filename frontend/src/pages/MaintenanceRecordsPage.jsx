import AssignmentTurnedInRoundedIcon from '@mui/icons-material/AssignmentTurnedInRounded'
import FilterListRoundedIcon from '@mui/icons-material/FilterListRounded'
import {
  Alert,
  Box,
  Button,
  MenuItem,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link as RouterLink, useSearchParams } from 'react-router-dom'
import { fetchEquipmentList } from '../api/equipment'
import { fetchMaintenanceRecords } from '../api/maintenance'
import { fetchUsers } from '../api/users'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

function toApiDateTime(value) {
  return value ? new Date(value).toISOString() : null
}

function formatUser(user) {
  if (!user) {
    return 'Не указан'
  }

  return `${user.first_name} ${user.last_name}`
}

function formatEquipment(equipment) {
  if (!equipment) {
    return 'Оборудование не указано'
  }

  return `${equipment.name} (${equipment.code})`
}

function getRecordSearchHaystack(record) {
  return [
    record.summary,
    record.details,
    record.task?.title,
    record.task?.description,
    record.equipment?.name,
    record.equipment?.code,
    record.performed_by_user?.first_name,
    record.performed_by_user?.last_name,
    record.performed_by_user?.email,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function getPerformerOptions(records, users) {
  const options = new Map()

  users.forEach((item) => {
    options.set(item.id, item)
  })
  records.forEach((record) => {
    if (record.performed_by_user) {
      options.set(record.performed_by_user.id, record.performed_by_user)
    }
  })

  return Array.from(options.values()).sort((left, right) =>
    formatUser(left).localeCompare(formatUser(right), 'ru'),
  )
}

export function MaintenanceRecordsPage() {
  const [searchParams] = useSearchParams()
  const { hasPermission } = useAuth()
  const canReadUsers = hasPermission('users.read')
  const [equipmentFilter, setEquipmentFilter] = useState(searchParams.get('equipment_id') ?? '')
  const [performerFilter, setPerformerFilter] = useState(searchParams.get('performed_by_user_id') ?? '')
  const [dateFromFilter, setDateFromFilter] = useState('')
  const [dateToFilter, setDateToFilter] = useState('')
  const [searchFilter, setSearchFilter] = useState(searchParams.get('q') ?? '')

  const recordsQuery = useQuery({
    queryKey: [
      'maintenance',
      'records',
      equipmentFilter,
      performerFilter,
      dateFromFilter,
      dateToFilter,
    ],
    queryFn: () =>
      fetchMaintenanceRecords({
        ...(equipmentFilter ? { equipment_id: equipmentFilter } : {}),
        ...(performerFilter ? { performed_by_user_id: performerFilter } : {}),
        ...(dateFromFilter ? { date_from: toApiDateTime(dateFromFilter) } : {}),
        ...(dateToFilter ? { date_to: toApiDateTime(dateToFilter) } : {}),
      }),
  })
  const equipmentQuery = useQuery({
    queryKey: ['equipment', 'maintenance-record-filters'],
    queryFn: fetchEquipmentList,
  })
  const usersQuery = useQuery({
    queryKey: ['users', 'maintenance-record-filters'],
    queryFn: fetchUsers,
    enabled: canReadUsers,
  })

  const records = recordsQuery.data ?? []
  const normalizedSearch = searchFilter.trim().toLowerCase()
  const filteredRecords = normalizedSearch
    ? records.filter((record) => getRecordSearchHaystack(record).includes(normalizedSearch))
    : records
  const equipmentOptions = equipmentQuery.data ?? []
  const performerOptions = getPerformerOptions(records, usersQuery.data ?? [])
  const isInitialLoading = recordsQuery.isLoading && records.length === 0
  const uniqueEquipmentCount = new Set(filteredRecords.map((record) => record.equipment?.id).filter(Boolean)).size
  const uniquePerformerCount = new Set(
    filteredRecords.map((record) => record.performed_by_user?.id).filter(Boolean),
  ).size
  const withDetailsCount = filteredRecords.filter((record) => Boolean(record.details)).length

  function resetFilters() {
    setEquipmentFilter('')
    setPerformerFilter('')
    setDateFromFilter('')
    setDateToFilter('')
    setSearchFilter('')
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Техническое обслуживание"
        title="История выполненного ТО"
        description="Журнал закрытых работ: кто выполнил задачу, когда она была проведена, по какому оборудованию и с каким результатом."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button onClick={resetFilters} startIcon={<FilterListRoundedIcon />} variant="outlined">
              Сбросить фильтры
            </Button>
            <Button
              component={RouterLink}
              startIcon={<AssignmentTurnedInRoundedIcon />}
              to="/maintenance"
              variant="contained"
            >
              К задачам ТО
            </Button>
          </Stack>
        }
      />

      {recordsQuery.isError ? (
        <Alert severity="warning">
          Не удалось загрузить историю ТО. Проверьте право `maintenance.read` и доступность API.
        </Alert>
      ) : null}
      {equipmentQuery.isError ? (
        <Alert severity="info">
          Справочник оборудования сейчас недоступен. Журнал можно смотреть, но фильтр по оборудованию ограничен.
        </Alert>
      ) : null}
      {canReadUsers && usersQuery.isError ? (
        <Alert severity="info">
          Список пользователей недоступен. Фильтр по исполнителю строится только по загруженным записям ТО.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(4, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Записей в выборке" value={formatNumber(filteredRecords.length)} />
        <StatCard accent="primary.main" label="Единиц оборудования" value={formatNumber(uniqueEquipmentCount)} />
        <StatCard accent="success.main" label="Исполнителей" value={formatNumber(uniquePerformerCount)} />
        <StatCard accent="warning.main" label="С деталями работ" value={formatNumber(withDetailsCount)} />
      </Box>

      <SectionCard
        title="Выполненные работы"
        subtitle="Запись появляется автоматически после завершения задачи ТО. Ручное создание здесь не нужно: так история остается связанной с исходной задачей."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Поиск"
              onChange={(event) => setSearchFilter(event.target.value)}
              placeholder="Итог, оборудование, исполнитель"
              size="small"
              sx={{ minWidth: 260 }}
              value={searchFilter}
            />
            <TextField
              label="Оборудование"
              onChange={(event) => setEquipmentFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 260 }}
              value={equipmentFilter}
            >
              <MenuItem value="">Все оборудование</MenuItem>
              {equipmentOptions.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {formatEquipment(item)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Исполнитель"
              onChange={(event) => setPerformerFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 220 }}
              value={performerFilter}
            >
              <MenuItem value="">Все исполнители</MenuItem>
              {performerOptions.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {formatUser(item)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              InputLabelProps={{ shrink: true }}
              label="С даты"
              onChange={(event) => setDateFromFilter(event.target.value)}
              size="small"
              type="datetime-local"
              value={dateFromFilter}
            />
            <TextField
              InputLabelProps={{ shrink: true }}
              label="По дату"
              onChange={(event) => setDateToFilter(event.target.value)}
              size="small"
              type="datetime-local"
              value={dateToFilter}
            />
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} height={82} variant="rounded" />
            ))}
          </Box>
        ) : filteredRecords.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 1120 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Выполнено</TableCell>
                  <TableCell>Оборудование</TableCell>
                  <TableCell>Задача</TableCell>
                  <TableCell>Исполнитель</TableCell>
                  <TableCell>Итог</TableCell>
                  <TableCell>Детали</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredRecords.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{formatDateTime(record.performed_at)}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        Создано: {formatDateTime(record.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{record.equipment.name}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {record.equipment.code}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack spacing={0.75}>
                        <Typography sx={{ fontWeight: 800 }}>{record.task.title}</Typography>
                        <Stack direction="row" spacing={0.75} sx={{ flexWrap: 'wrap' }}>
                          <StatusChip value={record.task.status} />
                          <StatusChip value={record.task.priority} />
                        </Stack>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{formatUser(record.performed_by_user)}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {record.performed_by_user.email}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ maxWidth: 300 }}>
                      <Typography sx={{ fontWeight: 700 }}>{record.summary}</Typography>
                    </TableCell>
                    <TableCell sx={{ maxWidth: 360 }}>
                      <Typography color={record.details ? 'text.primary' : 'text.secondary'}>
                        {record.details || 'Детали не указаны.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="Записи ТО не найдены"
            description="Завершите задачу ТО на странице задач или сбросьте фильтры, если журнал пуст только в текущей выборке."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>
    </Box>
  )
}
