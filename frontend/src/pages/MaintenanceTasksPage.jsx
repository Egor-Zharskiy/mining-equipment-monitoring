import AddTaskRoundedIcon from '@mui/icons-material/AddTaskRounded'
import AssignmentTurnedInRoundedIcon from '@mui/icons-material/AssignmentTurnedInRounded'
import CancelRoundedIcon from '@mui/icons-material/CancelRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import FilterListRoundedIcon from '@mui/icons-material/FilterListRounded'
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Skeleton,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { demoMaintenanceTasks } from '../api/demoData'
import { fetchEquipmentList } from '../api/equipment'
import {
  completeMaintenanceTask,
  createMaintenanceTask,
  fetchMaintenanceTasks,
  updateMaintenanceTask,
} from '../api/maintenance'
import { fetchUsers } from '../api/users'
import { useAuth } from '../auth/useAuth'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { DataFallbackNotice } from '../components/DataFallbackNotice'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

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

function getAssigneeLabel(user) {
  return user ? `${user.first_name} ${user.last_name}` : 'Не назначено'
}

function getStatusOptions(taskStatus) {
  if (taskStatus === 'open') {
    return [
      { value: 'open', label: 'Открыта' },
      { value: 'in_progress', label: 'В работе' },
      { value: 'cancelled', label: 'Отменено' },
    ]
  }

  if (taskStatus === 'in_progress') {
    return [
      { value: 'in_progress', label: 'В работе' },
      { value: 'cancelled', label: 'Отменено' },
    ]
  }

  if (taskStatus === 'done') {
    return [{ value: 'done', label: 'Выполнено' }]
  }

  if (taskStatus === 'cancelled') {
    return [{ value: 'cancelled', label: 'Отменено' }]
  }

  return [{ value: taskStatus, label: 'Неизвестно' }]
}

function buildTaskPayload(formState) {
  const payload = {
    equipment_id: formState.equipmentId,
    title: formState.title.trim() || null,
    description: formState.description.trim() || null,
    priority: formState.priority,
    due_at: toApiDateTime(formState.dueAt),
  }

  if (formState.assignedToUserId) {
    payload.assigned_to_user_id = formState.assignedToUserId
  }

  return payload
}

const emptyCreateForm = {
  equipmentId: '',
  title: '',
  description: '',
  priority: 'medium',
  dueAt: '',
  assignedToUserId: '',
}

export function MaintenanceTasksPage() {
  const [searchParams] = useSearchParams()
  const searchQuery = searchParams.get('q') ?? ''
  const queryClient = useQueryClient()
  const { hasPermission, user } = useAuth()
  const canManageMaintenance = hasPermission('maintenance.manage')
  const canReadUsers = hasPermission('users.read')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [assignedFilter, setAssignedFilter] = useState('')
  const [searchFilter, setSearchFilter] = useState(searchQuery)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState(null)
  const [createForm, setCreateForm] = useState(emptyCreateForm)
  const [editForm, setEditForm] = useState(emptyCreateForm)
  const [completeForm, setCompleteForm] = useState({
    summary: '',
    details: '',
    performedAt: toDateTimeLocalValue(new Date().toISOString()),
  })
  const [feedback, setFeedback] = useState({ open: false, message: '', severity: 'success' })
  const [cancelTask, setCancelTask] = useState(null)
  const focusTaskId = searchParams.get('focus')

  useEffect(() => {
    setSearchFilter(searchQuery)
  }, [searchQuery])

  const tasksQuery = useQuery({
    queryKey: ['maintenance', 'tasks', statusFilter, priorityFilter, assignedFilter],
    queryFn: () =>
      fetchMaintenanceTasks({
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(priorityFilter ? { priority: priorityFilter } : {}),
        ...(assignedFilter ? { assigned_to_user_id: assignedFilter } : {}),
      }),
  })
  const equipmentQuery = useQuery({
    queryKey: ['equipment', 'task-form-options'],
    queryFn: fetchEquipmentList,
    enabled: canManageMaintenance,
  })
  const usersQuery = useQuery({
    queryKey: ['users', 'task-form-options'],
    queryFn: fetchUsers,
    enabled: canReadUsers,
  })

  const usingFallback = tasksQuery.isError
  const baseTasks = usingFallback ? demoMaintenanceTasks : (tasksQuery.data ?? [])
  const equipmentOptions = equipmentQuery.data ?? []
  const userOptions =
    usersQuery.data?.length
      ? usersQuery.data
      : user
        ? [
            {
              id: user.id,
              first_name: user.first_name,
              last_name: user.last_name,
            },
          ]
        : []
  const normalizedSearch = searchFilter.trim().toLowerCase()
  const tasks = baseTasks.filter((item) => {
    if (!normalizedSearch) {
      return true
    }

    const haystack = [
      item.title,
      item.description,
      item.equipment.name,
      item.equipment.code,
      item.assigned_to_user?.first_name,
      item.assigned_to_user?.last_name,
      item.created_by_user?.first_name,
      item.created_by_user?.last_name,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(normalizedSearch)
  })
  const isInitialLoading = !usingFallback && tasksQuery.isLoading && baseTasks.length === 0
  const openCount = tasks.filter((item) => item.status === 'open').length
  const inProgressCount = tasks.filter((item) => item.status === 'in_progress').length
  const completedCount = tasks.filter((item) => item.status === 'done').length
  const cancelledCount = tasks.filter((item) => item.status === 'cancelled').length

  function showFeedback(message, severity = 'success') {
    setFeedback({
      open: true,
      message,
      severity,
    })
  }

  function invalidateMaintenanceQueries() {
    queryClient.invalidateQueries({ queryKey: ['maintenance'] })
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  const createTaskMutation = useMutation({
    mutationFn: createMaintenanceTask,
    onSuccess: () => {
      invalidateMaintenanceQueries()
      setCreateDialogOpen(false)
      setCreateForm(emptyCreateForm)
      showFeedback('Задача ТО создана.')
    },
    onError: (error) => {
      showFeedback(error.message, 'error')
    },
  })

  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, payload }) => updateMaintenanceTask(taskId, payload),
    onSuccess: () => {
      invalidateMaintenanceQueries()
      setEditDialogOpen(false)
      setSelectedTask(null)
      showFeedback('Задача обновлена.')
    },
    onError: (error) => {
      showFeedback(error.message, 'error')
    },
  })

  const completeTaskMutation = useMutation({
    mutationFn: ({ taskId, payload }) => completeMaintenanceTask(taskId, payload),
    onSuccess: () => {
      invalidateMaintenanceQueries()
      setCompleteDialogOpen(false)
      setSelectedTask(null)
      showFeedback('Задача успешно завершена.')
    },
    onError: (error) => {
      showFeedback(error.message, 'error')
    },
  })

  function resetFilters() {
    setStatusFilter('')
    setPriorityFilter('')
    setAssignedFilter('')
    setSearchFilter('')
  }

  function openCreateDialog() {
    setCreateForm({
      ...emptyCreateForm,
      assignedToUserId: user?.id ?? '',
    })
    setCreateDialogOpen(true)
  }

  function openEditDialog(task) {
    setSelectedTask(task)
    setEditForm({
      equipmentId: task.equipment.id,
      title: task.title,
      description: task.description ?? '',
      priority: task.priority,
      dueAt: toDateTimeLocalValue(task.due_at),
      assignedToUserId: task.assigned_to_user?.id ?? '',
      status: task.status,
    })
    setEditDialogOpen(true)
  }

  function openCompleteDialog(task) {
    setSelectedTask(task)
    setCompleteForm({
      summary: `${task.title} выполнена`,
      details: task.description ?? '',
      performedAt: toDateTimeLocalValue(new Date().toISOString()),
    })
    setCompleteDialogOpen(true)
  }

  function handleCreateSubmit(event) {
    event.preventDefault()
    createTaskMutation.mutate(buildTaskPayload(createForm))
  }

  function handleEditSubmit(event) {
    event.preventDefault()

    const payload = {
      title: editForm.title.trim() || null,
      description: editForm.description.trim() || null,
      priority: editForm.priority,
      due_at: toApiDateTime(editForm.dueAt),
      status: editForm.status,
      assigned_to_user_id: editForm.assignedToUserId || null,
    }

    updateTaskMutation.mutate({
      taskId: selectedTask.id,
      payload,
    })
  }

  function handleCompleteSubmit(event) {
    event.preventDefault()
    completeTaskMutation.mutate({
      taskId: selectedTask.id,
      payload: {
        summary: completeForm.summary.trim(),
        details: completeForm.details.trim() || null,
        performed_at: toApiDateTime(completeForm.performedAt),
        performed_by_user_id: user?.id ?? null,
      },
    })
  }

  function handleQuickStatusChange(task, status) {
    updateTaskMutation.mutate({
      taskId: task.id,
      payload: { status },
    })
  }

  const mutationsPending =
    createTaskMutation.isPending ||
    updateTaskMutation.isPending ||
    completeTaskMutation.isPending

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Техническое обслуживание"
        title="Задачи ТО"
        description="Очередь работ по техническому обслуживанию с фильтрами, статусами и рабочими действиями."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button onClick={resetFilters} startIcon={<FilterListRoundedIcon />} variant="outlined">
              Сбросить фильтры
            </Button>
            {canManageMaintenance ? (
              <Button
                onClick={openCreateDialog}
                startIcon={<AddTaskRoundedIcon />}
                variant="contained"
              >
                Создать задачу
              </Button>
            ) : null}
          </Stack>
        }
      />

      {usingFallback ? <DataFallbackNotice /> : null}
      {!usingFallback && tasksQuery.isError ? (
        <Alert severity="warning">
          Не удалось загрузить задачи ТО из API. Показан резервный набор данных.
        </Alert>
      ) : null}
      {canReadUsers && usersQuery.isError ? (
        <Alert severity="info">
          Список пользователей недоступен. Для назначения и фильтрации используется сокращенный набор исполнителей.
        </Alert>
      ) : null}
      {canManageMaintenance && equipmentQuery.isError ? (
        <Alert severity="info">
          Список оборудования для формы создания сейчас недоступен. Открытые задачи можно просматривать, но создание новых может быть ограничено.
        </Alert>
      ) : null}
      {!canManageMaintenance ? (
        <Alert severity="info">
          У текущего пользователя есть доступ к просмотру задач, но действия создания, редактирования и завершения скрыты без `maintenance.manage`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(5, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Видимых задач" value={formatNumber(tasks.length)} />
        <StatCard accent="warning.main" label="Открытые" value={formatNumber(openCount)} />
        <StatCard accent="secondary.main" label="В работе" value={formatNumber(inProgressCount)} />
        <StatCard accent="success.main" label="Выполнено" value={formatNumber(completedCount)} />
        <StatCard accent="text.secondary" label="Отменено" value={formatNumber(cancelledCount)} />
      </Box>

      <SectionCard
        title="Очередь работ"
        subtitle="Фильтры, создание, обновление и завершение задач без перегрузки экрана тяжелой CRUD-формой."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Поиск"
              onChange={(event) => setSearchFilter(event.target.value)}
              placeholder="Название, описание, оборудование"
              size="small"
              sx={{ minWidth: 260 }}
              value={searchFilter}
            />
            <TextField
              label="Статус"
              onChange={(event) => setStatusFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={statusFilter}
            >
              <MenuItem value="">Все статусы</MenuItem>
              <MenuItem value="open">Открыта</MenuItem>
              <MenuItem value="in_progress">В работе</MenuItem>
              <MenuItem value="done">Выполнено</MenuItem>
              <MenuItem value="cancelled">Отменено</MenuItem>
            </TextField>
            <TextField
              label="Приоритет"
              onChange={(event) => setPriorityFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={priorityFilter}
            >
              <MenuItem value="">Все приоритеты</MenuItem>
              <MenuItem value="low">Низкий</MenuItem>
              <MenuItem value="medium">Средний</MenuItem>
              <MenuItem value="high">Высокий</MenuItem>
            </TextField>
            <TextField
              label="Исполнитель"
              onChange={(event) => setAssignedFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={assignedFilter}
            >
              <MenuItem value="">Все исполнители</MenuItem>
              {userOptions.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.first_name} {item.last_name}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} height={220} variant="rounded" />
            ))}
          </Box>
        ) : tasks.length ? (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', xl: 'repeat(2, minmax(0, 1fr))' },
            }}
          >
            {tasks.map((task) => (
              <Paper
                key={task.id}
                sx={{
                  border: '1px solid',
                  borderColor: task.id === focusTaskId ? 'primary.main' : 'divider',
                  boxShadow: task.id === focusTaskId ? 3 : 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2,
                  p: 2.5,
                }}
              >
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={1.25}
                  sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}
                >
                  <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                    <StatusChip value={task.status} />
                    <StatusChip value={task.priority} />
                  </Stack>
                  <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                    Создано: {formatDateTime(task.created_at)}
                  </Typography>
                </Stack>

                <Box>
                  <Typography sx={{ fontSize: 20, fontWeight: 800, mb: 1 }}>
                    {task.title}
                  </Typography>
                  <Typography color="text.secondary">
                    {task.description || 'Описание не указано.'}
                  </Typography>
                </Box>

                <Box sx={{ display: 'grid', gap: 1 }}>
                  <Typography><strong>Оборудование:</strong> {task.equipment.name}</Typography>
                  <Typography><strong>Код:</strong> {task.equipment.code}</Typography>
                  <Typography><strong>Срок:</strong> {formatDateTime(task.due_at)}</Typography>
                  <Typography><strong>Исполнитель:</strong> {getAssigneeLabel(task.assigned_to_user)}</Typography>
                  <Typography><strong>Создал:</strong> {getAssigneeLabel(task.created_by_user)}</Typography>
                  {task.completed_at ? (
                    <Typography><strong>Завершено:</strong> {formatDateTime(task.completed_at)}</Typography>
                  ) : null}
                </Box>

                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25} sx={{ mt: 'auto' }}>
                  {canManageMaintenance && (task.status === 'open' || task.status === 'in_progress') && (
                    <Button
                      onClick={() => openEditDialog(task)}
                      startIcon={<EditRoundedIcon />}
                      variant="outlined"
                    >
                      Редактировать
                    </Button>
                  )}
                  {canManageMaintenance && task.status === 'open' && (
                    <Button
                      onClick={() => handleQuickStatusChange(task, 'in_progress')}
                      startIcon={<PlayArrowRoundedIcon />}
                      variant="contained"
                    >
                      В работу
                    </Button>
                  )}
                  {canManageMaintenance && task.status === 'in_progress' && (
                    <Button
                      onClick={() => openCompleteDialog(task)}
                      startIcon={<AssignmentTurnedInRoundedIcon />}
                      variant="contained"
                    >
                      Завершить
                    </Button>
                  )}
                  {canManageMaintenance && (task.status === 'open' || task.status === 'in_progress') && (
                    <Button
                      color="inherit"
                      onClick={() => setCancelTask(task)}
                      startIcon={<CancelRoundedIcon />}
                      variant="text"
                    >
                      Отменить
                    </Button>
                  )}
                </Stack>
              </Paper>
            ))}
          </Box>
        ) : (
          <EmptyState
            title="Задачи не найдены"
            description="По текущим фильтрам нет задач технического обслуживания. Создайте новую задачу или сбросьте фильтры."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <Dialog
        fullWidth
        maxWidth="sm"
        open={createDialogOpen}
        onClose={() => !mutationsPending && setCreateDialogOpen(false)}
      >
        <Box component="form" onSubmit={handleCreateSubmit}>
          <DialogTitle>Создать задачу ТО</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              label="Оборудование"
              onChange={(event) => setCreateForm((current) => ({ ...current, equipmentId: event.target.value }))}
              required
              select
              value={createForm.equipmentId}
            >
              {equipmentOptions.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Название"
              onChange={(event) => setCreateForm((current) => ({ ...current, title: event.target.value }))}
              required
              value={createForm.title}
            />
            <TextField
              label="Описание"
              multiline
              minRows={3}
              onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))}
              value={createForm.description}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Приоритет"
                onChange={(event) => setCreateForm((current) => ({ ...current, priority: event.target.value }))}
                select
                sx={{ flex: 1 }}
                value={createForm.priority}
              >
                <MenuItem value="low">Низкий</MenuItem>
                <MenuItem value="medium">Средний</MenuItem>
                <MenuItem value="high">Высокий</MenuItem>
              </TextField>
              <TextField
                InputLabelProps={{ shrink: true }}
                label="Срок"
                onChange={(event) => setCreateForm((current) => ({ ...current, dueAt: event.target.value }))}
                sx={{ flex: 1 }}
                type="datetime-local"
                value={createForm.dueAt}
              />
            </Stack>
            <TextField
              label="Исполнитель"
              onChange={(event) => setCreateForm((current) => ({ ...current, assignedToUserId: event.target.value }))}
              select
              value={createForm.assignedToUserId}
            >
              <MenuItem value="">Не назначать</MenuItem>
              {userOptions.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.first_name} {item.last_name}
                </MenuItem>
              ))}
            </TextField>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button disabled={mutationsPending} onClick={() => setCreateDialogOpen(false)}>
              Отмена
            </Button>
            <Button disabled={mutationsPending} type="submit" variant="contained">
              Создать
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog
        fullWidth
        maxWidth="sm"
        open={editDialogOpen}
        onClose={() => !mutationsPending && setEditDialogOpen(false)}
      >
        <Box component="form" onSubmit={handleEditSubmit}>
          <DialogTitle>Редактировать задачу</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              disabled
              label="Оборудование"
              value={selectedTask?.equipment.name ?? ''}
            />
            <TextField
              label="Название"
              onChange={(event) => setEditForm((current) => ({ ...current, title: event.target.value }))}
              required
              value={editForm.title}
            />
            <TextField
              label="Описание"
              minRows={3}
              multiline
              onChange={(event) => setEditForm((current) => ({ ...current, description: event.target.value }))}
              value={editForm.description}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Статус"
                onChange={(event) => setEditForm((current) => ({ ...current, status: event.target.value }))}
                select
                sx={{ flex: 1 }}
                value={editForm.status ?? ''}
              >
                {getStatusOptions(selectedTask?.status).map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Приоритет"
                onChange={(event) => setEditForm((current) => ({ ...current, priority: event.target.value }))}
                select
                sx={{ flex: 1 }}
                value={editForm.priority}
              >
                <MenuItem value="low">Низкий</MenuItem>
                <MenuItem value="medium">Средний</MenuItem>
                <MenuItem value="high">Высокий</MenuItem>
              </TextField>
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                InputLabelProps={{ shrink: true }}
                label="Срок"
                onChange={(event) => setEditForm((current) => ({ ...current, dueAt: event.target.value }))}
                sx={{ flex: 1 }}
                type="datetime-local"
                value={editForm.dueAt}
              />
              <TextField
                label="Исполнитель"
                onChange={(event) => setEditForm((current) => ({ ...current, assignedToUserId: event.target.value }))}
                select
                sx={{ flex: 1 }}
                value={editForm.assignedToUserId}
              >
                <MenuItem value="">Не назначать</MenuItem>
                {userOptions.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.first_name} {item.last_name}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button disabled={mutationsPending} onClick={() => setEditDialogOpen(false)}>
              Отмена
            </Button>
            <Button disabled={mutationsPending} type="submit" variant="contained">
              Сохранить
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog
        fullWidth
        maxWidth="sm"
        open={completeDialogOpen}
        onClose={() => !mutationsPending && setCompleteDialogOpen(false)}
      >
        <Box component="form" onSubmit={handleCompleteSubmit}>
          <DialogTitle>Завершить задачу</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              label="Краткий итог"
              onChange={(event) => setCompleteForm((current) => ({ ...current, summary: event.target.value }))}
              required
              value={completeForm.summary}
            />
            <TextField
              label="Подробности"
              minRows={4}
              multiline
              onChange={(event) => setCompleteForm((current) => ({ ...current, details: event.target.value }))}
              value={completeForm.details}
            />
            <TextField
              InputLabelProps={{ shrink: true }}
              label="Выполнено в"
              onChange={(event) => setCompleteForm((current) => ({ ...current, performedAt: event.target.value }))}
              required
              type="datetime-local"
              value={completeForm.performedAt}
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button disabled={mutationsPending} onClick={() => setCompleteDialogOpen(false)}>
              Отмена
            </Button>
            <Button disabled={mutationsPending} type="submit" variant="contained">
              Завершить задачу
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Snackbar
        autoHideDuration={4000}
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

      <ConfirmDialog
        confirmColor="warning"
        confirmLabel="Отменить задачу"
        description={
          cancelTask
            ? `Задача "${cancelTask.title}" будет переведена в статус "Отменено". Подтвердите отмену, если работа больше не актуальна или выполнение остановлено.`
            : ''
        }
        isSubmitting={updateTaskMutation.isPending}
        onCancel={() => setCancelTask(null)}
        onConfirm={() => {
          if (!cancelTask) {
            return
          }

          updateTaskMutation.mutate({
            taskId: cancelTask.id,
            payload: { status: 'cancelled' },
          })
          setCancelTask(null)
        }}
        open={Boolean(cancelTask)}
        title="Подтвердить отмену задачи"
      />
    </Box>
  )
}
