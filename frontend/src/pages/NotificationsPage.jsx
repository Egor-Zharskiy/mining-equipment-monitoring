import AddRoundedIcon from '@mui/icons-material/AddRounded'
import MarkEmailReadRoundedIcon from '@mui/icons-material/MarkEmailReadRounded'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Skeleton,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createManualNotification,
  fetchNotifications,
  fetchUnreadNotificationCount,
  markNotificationAsRead,
} from '../api/notifications'
import { fetchUsers } from '../api/users'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNotificationType, formatNumber } from '../utils/format'

const emptyManualForm = {
  recipientUserIds: [],
  channels: ['internal'],
  title: '',
  message: '',
}

export function NotificationsPage() {
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canManageNotifications = hasPermission('notifications.manage')
  const canReadUsers = hasPermission('users.read')
  const [channelFilter, setChannelFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [readFilter, setReadFilter] = useState('all')
  const [manualDialogOpen, setManualDialogOpen] = useState(false)
  const [manualForm, setManualForm] = useState(emptyManualForm)
  const [feedback, setFeedback] = useState({ open: false, message: '', severity: 'success' })

  const notificationsQuery = useQuery({
    queryKey: ['notifications', 'list', channelFilter, typeFilter, readFilter],
    queryFn: () =>
      fetchNotifications({
        ...(channelFilter ? { channel: channelFilter } : {}),
        ...(typeFilter ? { notification_type: typeFilter } : {}),
        ...(readFilter === 'all' ? {} : { is_read: readFilter === 'read' }),
      }),
  })
  const unreadCountQuery = useQuery({
    queryKey: ['notifications', 'unread-count', channelFilter],
    queryFn: () =>
      fetchUnreadNotificationCount({
        ...(channelFilter ? { channel: channelFilter } : {}),
      }),
  })
  const usersQuery = useQuery({
    queryKey: ['users', 'notification-recipients'],
    queryFn: fetchUsers,
    enabled: canManageNotifications && canReadUsers,
  })

  const markReadMutation = useMutation({
    mutationFn: markNotificationAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      setFeedback({
        open: true,
        message: 'Уведомление отмечено как прочитанное.',
        severity: 'success',
      })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message,
        severity: 'error',
      })
    },
  })
  const createManualMutation = useMutation({
    mutationFn: createManualNotification,
    onSuccess: (createdNotifications) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      setManualDialogOpen(false)
      setManualForm(emptyManualForm)
      setFeedback({
        open: true,
        message: `Создано уведомлений: ${createdNotifications.length}.`,
        severity: 'success',
      })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message || 'Не удалось создать ручное уведомление.',
        severity: 'error',
      })
    },
  })

  const notifications = notificationsQuery.data ?? []
  const users = usersQuery.data ?? []
  const unreadCount = unreadCountQuery.data?.unread_count ?? 0
  const emailCount = notifications.filter((item) => item.channel === 'email').length
  const unreadVisibleCount = notifications.filter((item) => !item.is_read).length
  const notificationTypeOptions = Array.from(
    new Set(notifications.map((item) => item.notification_type)),
  ).sort()
  const isInitialLoading = notificationsQuery.isLoading && notifications.length === 0

  function resetFilters() {
    setChannelFilter('')
    setTypeFilter('')
    setReadFilter('all')
  }

  function openManualDialog() {
    setManualForm(emptyManualForm)
    setManualDialogOpen(true)
  }

  function submitManualNotification(event) {
    event.preventDefault()

    if (!manualForm.recipientUserIds.length || !manualForm.channels.length) {
      setFeedback({
        open: true,
        message: 'Выберите получателей и хотя бы один канал.',
        severity: 'warning',
      })
      return
    }

    createManualMutation.mutate({
      recipient_user_ids: manualForm.recipientUserIds,
      channels: manualForm.channels,
      title: manualForm.title.trim(),
      message: manualForm.message.trim(),
    })
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Оповещения"
        title="Уведомления"
        description="Лента оповещений с фильтрами, непрочитанными сообщениями и действием чтения."
        actions={
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            {canManageNotifications ? (
              <Button onClick={openManualDialog} startIcon={<AddRoundedIcon />} variant="contained">
                Ручное уведомление
              </Button>
            ) : null}
            <Button onClick={resetFilters} startIcon={<MarkEmailReadRoundedIcon />} variant="outlined">
              Сбросить фильтры
            </Button>
          </Stack>
        }
      />

      {notificationsQuery.isError ? (
        <Alert severity="warning">
          Не удалось загрузить уведомления из API. Проверьте доступность backend или права пользователя.
        </Alert>
      ) : null}
      {unreadCountQuery.isError ? (
        <Alert severity="info">
          Счетчик непрочитанных временно недоступен. Список уведомлений продолжает работать.
        </Alert>
      ) : null}
      {canManageNotifications && !canReadUsers ? (
        <Alert severity="info">
          Для ручной отправки нужен доступ к списку пользователей: `users.read`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Видимых уведомлений" value={formatNumber(notifications.length)} />
        <StatCard accent="warning.main" label="Непрочитанные" value={formatNumber(unreadCount)} />
        <StatCard accent="secondary.main" label="Email-канал" value={formatNumber(emailCount)} />
        <StatCard accent="primary.main" label="Непрочитано в ленте" value={formatNumber(unreadVisibleCount)} />
      </Box>

      <SectionCard
        title="Лента уведомлений"
        subtitle="Можно фильтровать канал, тип и состояние чтения, а также помечать уведомления как прочитанные."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Канал"
              onChange={(event) => setChannelFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={channelFilter}
            >
              <MenuItem value="">Все каналы</MenuItem>
              <MenuItem value="internal">Внутренний</MenuItem>
              <MenuItem value="email">Email</MenuItem>
            </TextField>
            <TextField
              label="Тип"
              onChange={(event) => setTypeFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 260 }}
              value={typeFilter}
            >
              <MenuItem value="">Все типы</MenuItem>
              {notificationTypeOptions.map((item) => (
                <MenuItem key={item} value={item}>
                  {formatNotificationType(item)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Чтение"
              onChange={(event) => setReadFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={readFilter}
            >
              <MenuItem value="all">Все</MenuItem>
              <MenuItem value="unread">Непрочитанные</MenuItem>
              <MenuItem value="read">Прочитанные</MenuItem>
            </TextField>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} height={92} variant="rounded" />
            ))}
          </Box>
        ) : notifications.length ? (
          <List disablePadding>
            {notifications.map((notification, index) => (
              <Box key={notification.id}>
                <ListItem
                  disableGutters
                  secondaryAction={
                    !notification.is_read ? (
                      <Button
                        disabled={markReadMutation.isPending}
                        onClick={() => markReadMutation.mutate(notification.id)}
                        size="small"
                        variant="outlined"
                      >
                        Прочитать
                      </Button>
                    ) : null
                  }
                  sx={{ alignItems: 'flex-start', gap: 2, px: 0, py: 2 }}
                >
                  <ListItemText
                    primaryTypographyProps={{ component: 'div' }}
                    secondaryTypographyProps={{ component: 'div' }}
                    primary={
                      <Box sx={{ alignItems: 'center', display: 'flex', flexWrap: 'wrap', gap: 1, mb: 0.75 }}>
                        <Typography sx={{ fontWeight: 800 }}>{notification.title}</Typography>
                        <StatusChip value={notification.channel} />
                        <StatusChip value={notification.is_read ? 'read' : 'unread'} />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography color="text.secondary" sx={{ mb: 1 }}>
                          {notification.message}
                        </Typography>
                        <Typography color="text.secondary" sx={{ fontSize: 13, mb: 0.5 }}>
                          {formatNotificationType(notification.notification_type)}
                          {' • '}
                          {notification.event?.equipment?.name || notification.maintenance_task?.equipment?.name || 'Система'}
                        </Typography>
                        <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                          Создано: {formatDateTime(notification.created_at)}
                          {notification.read_at ? ` • Прочитано: ${formatDateTime(notification.read_at)}` : ''}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                {index < notifications.length - 1 ? <Divider /> : null}
              </Box>
            ))}
          </List>
        ) : (
          <EmptyState
            title="Уведомления не найдены"
            description="По текущим фильтрам уведомлений нет. Сбросьте фильтры или дождитесь новых событий и задач."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <Dialog
        fullWidth
        maxWidth="sm"
        onClose={() => !createManualMutation.isPending && setManualDialogOpen(false)}
        open={manualDialogOpen}
      >
        <Box component="form" onSubmit={submitManualNotification}>
          <DialogTitle>Создать ручное уведомление</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            {usersQuery.isError ? (
              <Alert severity="warning">
                Не удалось загрузить пользователей. {usersQuery.error.message}
              </Alert>
            ) : null}
            <TextField
              disabled={!canReadUsers || usersQuery.isLoading}
              helperText={
                canReadUsers
                  ? `Выбрано получателей: ${manualForm.recipientUserIds.length}`
                  : 'Для выбора получателей нужен users.read'
              }
              label="Получатели"
              onChange={(event) =>
                setManualForm((current) => ({
                  ...current,
                  recipientUserIds:
                    typeof event.target.value === 'string'
                      ? event.target.value.split(',')
                      : event.target.value,
                }))
              }
              required
              select
              SelectProps={{
                multiple: true,
                renderValue: (selected) =>
                  users
                    .filter((user) => selected.includes(user.id))
                    .map((user) => `${user.first_name} ${user.last_name}`)
                    .join(', '),
              }}
              value={manualForm.recipientUserIds}
            >
              {users.map((user) => (
                <MenuItem key={user.id} value={user.id}>
                  <Box>
                    <Typography sx={{ fontWeight: 800 }}>
                      {user.first_name} {user.last_name}
                    </Typography>
                    <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                      {user.email} {user.is_active ? '' : '• неактивен'}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </TextField>
            <TextField
              helperText="Можно выбрать внутренний канал, email или оба."
              label="Каналы"
              onChange={(event) =>
                setManualForm((current) => ({
                  ...current,
                  channels:
                    typeof event.target.value === 'string'
                      ? event.target.value.split(',')
                      : event.target.value,
                }))
              }
              required
              select
              SelectProps={{
                multiple: true,
                renderValue: (selected) => selected.join(', '),
              }}
              value={manualForm.channels}
            >
              <MenuItem value="internal">Внутренний</MenuItem>
              <MenuItem value="email">Email</MenuItem>
            </TextField>
            <TextField
              label="Заголовок"
              onChange={(event) =>
                setManualForm((current) => ({ ...current, title: event.target.value }))
              }
              required
              value={manualForm.title}
            />
            <TextField
              label="Сообщение"
              minRows={4}
              multiline
              onChange={(event) =>
                setManualForm((current) => ({ ...current, message: event.target.value }))
              }
              required
              value={manualForm.message}
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button
              disabled={createManualMutation.isPending}
              onClick={() => setManualDialogOpen(false)}
            >
              Отмена
            </Button>
            <Button disabled={createManualMutation.isPending || !canReadUsers} type="submit" variant="contained">
              Отправить
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
    </Box>
  )
}
