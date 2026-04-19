import AddTaskRoundedIcon from '@mui/icons-material/AddTaskRounded'
import FilterListRoundedIcon from '@mui/icons-material/FilterListRounded'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Skeleton,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { fetchEquipmentList } from '../api/equipment'
import { createMaintenanceTaskFromEvent, fetchEvents } from '../api/events'
import { fetchUsers } from '../api/users'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatEventType, formatNumber } from '../utils/format'

const emptyEventTaskForm = {
  title: '',
  description: '',
  priority: 'high',
  dueAt: '',
  assignedToUserId: '',
}

function toDateTimeLocalValue(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  const timezoneOffset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16)
}

function toApiDateTime(value) {
  return value ? new Date(value).toISOString() : null
}

export function EventsPage() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canCreateMaintenanceTask = hasPermission('maintenance.manage')
  const canReadUsers = hasPermission('users.read')
  const searchQuery = searchParams.get('q') ?? ''
  const [severityFilter, setSeverityFilter] = useState('')
  const [eventTypeFilter, setEventTypeFilter] = useState('')
  const [equipmentIdFilter, setEquipmentIdFilter] = useState('')
  const [searchFilter, setSearchFilter] = useState(searchQuery)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [taskForm, setTaskForm] = useState(emptyEventTaskForm)
  const [feedback, setFeedback] = useState({ open: false, message: '', severity: 'success' })
  const focusEventId = searchParams.get('focus')

  useEffect(() => {
    setSearchFilter(searchQuery)
  }, [searchQuery])

  const eventsQuery = useQuery({
    queryKey: ['events', 'list', severityFilter, eventTypeFilter, equipmentIdFilter],
    queryFn: () =>
      fetchEvents({
        limit: 40,
        ...(severityFilter ? { severity: severityFilter } : {}),
        ...(eventTypeFilter ? { event_type: eventTypeFilter } : {}),
        ...(equipmentIdFilter ? { equipment_id: equipmentIdFilter } : {}),
      }),
  })
  const equipmentQuery = useQuery({
    queryKey: ['equipment', 'filter-options'],
    queryFn: fetchEquipmentList,
  })
  const usersQuery = useQuery({
    queryKey: ['users', 'event-task-assignees'],
    queryFn: fetchUsers,
    enabled: canCreateMaintenanceTask && canReadUsers,
  })
  const createTaskFromEventMutation = useMutation({
    mutationFn: ({ eventId, payload }) => createMaintenanceTaskFromEvent(eventId, payload),
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      setSelectedEvent(null)
      setTaskForm(emptyEventTaskForm)
      setFeedback({
        open: true,
        message: `Задача ТО создана: ${task.title}.`,
        severity: 'success',
      })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message || 'Не удалось создать задачу ТО из события.',
        severity: 'error',
      })
    },
  })

  const baseEvents = eventsQuery.data ?? []
  const equipmentOptions = equipmentQuery.data ?? []
  const userOptions = usersQuery.data ?? []
  const normalizedSearch = searchFilter.trim().toLowerCase()
  const events = baseEvents.filter((item) => {
    if (!normalizedSearch) {
      return true
    }

    const haystack = [
      item.title,
      item.message,
      item.event_type,
      item.equipment.name,
      item.equipment.code,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(normalizedSearch)
  })
  const isInitialLoading = eventsQuery.isLoading && baseEvents.length === 0
  const criticalCount = events.filter((item) => item.severity === 'critical').length
  const warningCount = events.filter((item) => item.severity === 'warning').length
  const eventTypeOptions = Array.from(new Set(baseEvents.map((item) => item.event_type))).sort()

  function resetFilters() {
    setSeverityFilter('')
    setEventTypeFilter('')
    setEquipmentIdFilter('')
    setSearchFilter('')
  }

  function openTaskDialog(event) {
    const dueAt = new Date()
    dueAt.setDate(dueAt.getDate() + 1)
    setSelectedEvent(event)
    setTaskForm({
      title: `Проверить событие: ${event.title}`.slice(0, 150),
      description: `${event.message}\n\nИсточник: событие ${event.id}`.slice(0, 500),
      priority: event.severity === 'critical' ? 'high' : 'medium',
      dueAt: toDateTimeLocalValue(dueAt.toISOString()),
      assignedToUserId: '',
    })
  }

  function closeTaskDialog() {
    if (createTaskFromEventMutation.isPending) {
      return
    }
    setSelectedEvent(null)
    setTaskForm(emptyEventTaskForm)
  }

  function submitTaskFromEvent(event) {
    event.preventDefault()
    createTaskFromEventMutation.mutate({
      eventId: selectedEvent.id,
      payload: {
        title: taskForm.title.trim(),
        description: taskForm.description.trim() || null,
        priority: taskForm.priority,
        due_at: toApiDateTime(taskForm.dueAt),
        assigned_to_user_id: taskForm.assignedToUserId || null,
      },
    })
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Журнал мониторинга"
        title="События"
        description="Краткий обзор пересечений порогов, смены состояний и восстановлений."
        actions={
          <Button onClick={resetFilters} startIcon={<FilterListRoundedIcon />} variant="outlined">
            Сбросить фильтры
          </Button>
        }
      />

      {eventsQuery.isError ? (
        <Alert severity="warning">
          Не удалось получить события из API. Проверьте доступность backend или права пользователя.
        </Alert>
      ) : null}
      {equipmentQuery.isError ? (
        <Alert severity="info">
          Не удалось загрузить список оборудования для фильтра. Лента событий продолжает работать без этого справочника.
        </Alert>
      ) : null}
      {canCreateMaintenanceTask && !canReadUsers ? (
        <Alert severity="info">
          Создание задач из событий доступно, но выбор исполнителя скрыт без `users.read`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Видимых событий" value={formatNumber(events.length)} />
        <StatCard accent="warning.main" label="Предупреждения" value={formatNumber(warningCount)} />
        <StatCard accent="error.main" label="Критические события" value={formatNumber(criticalCount)} />
      </Box>

      <SectionCard
        title="Лента событий"
        subtitle="Журнал событий с фильтрами по критичности, типу и оборудованию."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Поиск"
              onChange={(event) => setSearchFilter(event.target.value)}
              placeholder="Название, текст, оборудование"
              size="small"
              sx={{ minWidth: 260 }}
              value={searchFilter}
            />
            <TextField
              label="Критичность"
              onChange={(event) => setSeverityFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={severityFilter}
            >
              <MenuItem value="">Все</MenuItem>
              <MenuItem value="info">Инфо</MenuItem>
              <MenuItem value="warning">Предупреждение</MenuItem>
              <MenuItem value="critical">Критично</MenuItem>
            </TextField>
            <TextField
              label="Тип события"
              onChange={(event) => setEventTypeFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={eventTypeFilter}
            >
              <MenuItem value="">Все типы</MenuItem>
              {eventTypeOptions.map((eventType) => (
                <MenuItem key={eventType} value={eventType}>
                  {formatEventType(eventType)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Оборудование"
              onChange={(event) => setEquipmentIdFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 260 }}
              value={equipmentIdFilter}
            >
              <MenuItem value="">Все единицы</MenuItem>
              {equipmentOptions.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} height={68} variant="rounded" />
            ))}
          </Box>
        ) : events.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: canCreateMaintenanceTask ? 1120 : 920 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Событие</TableCell>
                  <TableCell>Оборудование</TableCell>
                  <TableCell>Тип</TableCell>
                  <TableCell>Критичность</TableCell>
                  <TableCell>Создано</TableCell>
                  {canCreateMaintenanceTask ? <TableCell align="right">Действия</TableCell> : null}
                </TableRow>
              </TableHead>
              <TableBody>
                {events.map((event) => (
                  <TableRow key={event.id} selected={event.id === focusEventId}>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{event.title}</Typography>
                      <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                        {event.message}
                      </Typography>
                    </TableCell>
                    <TableCell>{event.equipment.name}</TableCell>
                    <TableCell>{formatEventType(event.event_type)}</TableCell>
                    <TableCell>
                      <StatusChip value={event.severity} />
                    </TableCell>
                    <TableCell>{formatDateTime(event.created_at)}</TableCell>
                    {canCreateMaintenanceTask ? (
                      <TableCell align="right">
                        <Button
                          onClick={() => openTaskDialog(event)}
                          size="small"
                          startIcon={<AddTaskRoundedIcon />}
                          variant="outlined"
                        >
                          Задача ТО
                        </Button>
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="События не найдены"
            description="По текущим фильтрам событий нет. Измените фильтры или сбросьте их."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <Dialog fullWidth maxWidth="sm" onClose={closeTaskDialog} open={Boolean(selectedEvent)}>
        <Box component="form" onSubmit={submitTaskFromEvent}>
          <DialogTitle>Создать задачу ТО из события</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            {selectedEvent ? (
              <Alert severity={selectedEvent.severity === 'critical' ? 'error' : 'warning'}>
                {selectedEvent.equipment.name}: {formatEventType(selectedEvent.event_type)}
              </Alert>
            ) : null}
            <TextField
              label="Название задачи"
              onChange={(event) => setTaskForm((current) => ({ ...current, title: event.target.value }))}
              required
              value={taskForm.title}
            />
            <TextField
              label="Описание"
              multiline
              minRows={4}
              onChange={(event) => setTaskForm((current) => ({ ...current, description: event.target.value }))}
              value={taskForm.description}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Приоритет"
                onChange={(event) => setTaskForm((current) => ({ ...current, priority: event.target.value }))}
                select
                sx={{ flex: 1 }}
                value={taskForm.priority}
              >
                <MenuItem value="low">Низкий</MenuItem>
                <MenuItem value="medium">Средний</MenuItem>
                <MenuItem value="high">Высокий</MenuItem>
              </TextField>
              <TextField
                InputLabelProps={{ shrink: true }}
                label="Срок"
                onChange={(event) => setTaskForm((current) => ({ ...current, dueAt: event.target.value }))}
                sx={{ flex: 1 }}
                type="datetime-local"
                value={taskForm.dueAt}
              />
            </Stack>
            {canReadUsers ? (
              <TextField
                label="Исполнитель"
                onChange={(event) =>
                  setTaskForm((current) => ({ ...current, assignedToUserId: event.target.value }))
                }
                select
                value={taskForm.assignedToUserId}
              >
                <MenuItem value="">Не назначать</MenuItem>
                {userOptions.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.first_name} {item.last_name} ({item.email})
                  </MenuItem>
                ))}
              </TextField>
            ) : null}
          </DialogContent>
          <DialogActions>
            <Button disabled={createTaskFromEventMutation.isPending} onClick={closeTaskDialog}>
              Отмена
            </Button>
            <Button disabled={createTaskFromEventMutation.isPending} type="submit" variant="contained">
              Создать задачу
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Snackbar
        autoHideDuration={5000}
        onClose={() => setFeedback((current) => ({ ...current, open: false }))}
        open={feedback.open}
      >
        <Alert
          onClose={() => setFeedback((current) => ({ ...current, open: false }))}
          severity={feedback.severity}
          sx={{ width: '100%' }}
        >
          {feedback.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
