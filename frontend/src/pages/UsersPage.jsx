import AddRoundedIcon from '@mui/icons-material/AddRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Skeleton,
  Stack,
  Switch,
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
import { fetchRoles } from '../api/roles'
import { createUser, fetchUsers, updateUser } from '../api/users'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

const emptyCreateForm = {
  username: '',
  email: '',
  firstName: '',
  lastName: '',
  password: '',
  roleIds: [],
  isActive: true,
}

const emptyEditForm = {
  username: '',
  email: '',
  firstName: '',
  lastName: '',
  password: '',
  roleIds: [],
  isActive: true,
}

function renderRoleNames(roles) {
  if (!roles.length) {
    return 'Без роли'
  }

  return roles.map((role) => role.name).join(', ')
}

export function UsersPage() {
  const [searchParams] = useSearchParams()
  const searchQuery = searchParams.get('q') ?? ''
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canCreateUsers = hasPermission('users.create')
  const canUpdateUsers = hasPermission('users.update')
  const canReadRoles = hasPermission('roles.read')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [createForm, setCreateForm] = useState(emptyCreateForm)
  const [editForm, setEditForm] = useState(emptyEditForm)
  const [searchFilter, setSearchFilter] = useState(searchQuery)
  const focusUserId = searchParams.get('focus')

  useEffect(() => {
    setSearchFilter(searchQuery)
  }, [searchQuery])

  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: fetchUsers,
  })
  const rolesQuery = useQuery({
    queryKey: ['admin', 'roles', 'options'],
    queryFn: fetchRoles,
    enabled: canReadRoles,
  })

  const baseUsers = usersQuery.data ?? []
  const roles = rolesQuery.data ?? []
  const normalizedSearch = searchFilter.trim().toLowerCase()
  const users = baseUsers.filter((item) => {
    if (!normalizedSearch) {
      return true
    }

    const haystack = [
      item.first_name,
      item.last_name,
      item.email,
      item.username,
      ...item.roles.map((role) => role.name),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(normalizedSearch)
  })
  const isInitialLoading = usersQuery.isLoading && baseUsers.length === 0
  const activeCount = users.filter((user) => user.is_active).length
  const inactiveCount = users.filter((user) => !user.is_active).length
  const adminCount = users.filter((user) => user.roles.some((role) => role.name === 'admin')).length

  function invalidateUsers() {
    queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    queryClient.invalidateQueries({ queryKey: ['users'] })
  }

  const createUserMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      invalidateUsers()
      setCreateDialogOpen(false)
      setCreateForm(emptyCreateForm)
    },
  })

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, payload }) => updateUser(userId, payload),
    onSuccess: () => {
      invalidateUsers()
      setEditDialogOpen(false)
      setSelectedUser(null)
      setEditForm(emptyEditForm)
    },
  })

  function openCreateDialog() {
    setCreateForm(emptyCreateForm)
    setCreateDialogOpen(true)
  }

  function openEditDialog(user) {
    setSelectedUser(user)
    setEditForm({
      username: user.username,
      email: user.email,
      firstName: user.first_name,
      lastName: user.last_name,
      password: '',
      roleIds: user.roles.map((role) => role.id),
      isActive: user.is_active,
    })
    setEditDialogOpen(true)
  }

  function handleCreateSubmit(event) {
    event.preventDefault()
    createUserMutation.mutate({
      username: createForm.username.trim(),
      email: createForm.email.trim(),
      first_name: createForm.firstName.trim(),
      last_name: createForm.lastName.trim(),
      password: createForm.password,
      role_ids: createForm.roleIds,
      is_active: createForm.isActive,
    })
  }

  function handleEditSubmit(event) {
    event.preventDefault()

    const payload = {
      username: editForm.username.trim(),
      email: editForm.email.trim(),
      first_name: editForm.firstName.trim(),
      last_name: editForm.lastName.trim(),
      role_ids: editForm.roleIds,
      is_active: editForm.isActive,
    }

    if (editForm.password.trim()) {
      payload.password = editForm.password
    }

    updateUserMutation.mutate({
      userId: selectedUser.id,
      payload,
    })
  }

  const mutationError = createUserMutation.error?.message || updateUserMutation.error?.message
  const isMutating = createUserMutation.isPending || updateUserMutation.isPending

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Admin"
        title="Пользователи"
        description="Управление учетными записями, ролями и активностью пользователей системы."
        actions={
          canCreateUsers ? (
            <Button onClick={openCreateDialog} startIcon={<AddRoundedIcon />} variant="contained">
              Новый пользователь
            </Button>
          ) : null
        }
      />

      {usersQuery.isError ? (
        <Alert severity="error">
          Не удалось загрузить пользователей из API. {usersQuery.error.message}
        </Alert>
      ) : null}
      {canReadRoles && rolesQuery.isError ? (
        <Alert severity="warning">
          Список ролей недоступен. Создание и редактирование пользователей может быть ограничено.
        </Alert>
      ) : null}
      {!canCreateUsers ? (
        <Alert severity="info">
          У текущего пользователя есть доступ к просмотру пользователей, но создание скрыто без `users.create`.
        </Alert>
      ) : null}
      {!canUpdateUsers ? (
        <Alert severity="info">
          Редактирование пользователей скрыто без `users.update`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Всего пользователей" value={formatNumber(users.length)} />
        <StatCard accent="success.main" label="Активные" value={formatNumber(activeCount)} />
        <StatCard accent="primary.main" label="Администраторы" value={formatNumber(adminCount)} hint={`${formatNumber(inactiveCount)} неактивных`} />
      </Box>

      <SectionCard
        title="Список пользователей"
        subtitle="На этом экране администратор может создавать учетные записи и назначать им роли."
        action={
          <TextField
            label="Поиск"
            onChange={(event) => setSearchFilter(event.target.value)}
            placeholder="Имя, email, username"
            size="small"
            sx={{ minWidth: 260 }}
            value={searchFilter}
          />
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} height={72} variant="rounded" />
            ))}
          </Box>
        ) : users.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 980 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Пользователь</TableCell>
                  <TableCell>Роли</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Создан</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id} selected={user.id === focusUserId}>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>
                        {user.first_name} {user.last_name}
                      </Typography>
                      <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                        {user.email} • @{user.username}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                        {user.roles.length ? (
                          user.roles.map((role) => (
                            <Chip key={role.id} label={role.name} size="small" variant="outlined" />
                          ))
                        ) : (
                          <Typography color="text.secondary">Без роли</Typography>
                        )}
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <StatusChip value={user.is_active ? 'active' : 'inactive'} />
                    </TableCell>
                    <TableCell>{formatDateTime(user.created_at)}</TableCell>
                    <TableCell align="right">
                      {canUpdateUsers ? (
                        <Button
                          onClick={() => openEditDialog(user)}
                          startIcon={<EditRoundedIcon />}
                          variant="outlined"
                        >
                          Редактировать
                        </Button>
                      ) : null}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="Пользователи не найдены"
            description="В системе пока нет учетных записей, доступных для просмотра."
          />
        )}
      </SectionCard>

      <Dialog
        fullWidth
        maxWidth="sm"
        onClose={() => !isMutating && setCreateDialogOpen(false)}
        open={createDialogOpen}
      >
        <Box component="form" onSubmit={handleCreateSubmit}>
          <DialogTitle>Создать пользователя</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            {mutationError ? <Alert severity="error">{mutationError}</Alert> : null}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Имя"
                onChange={(event) => setCreateForm((current) => ({ ...current, firstName: event.target.value }))}
                required
                sx={{ flex: 1 }}
                value={createForm.firstName}
              />
              <TextField
                label="Фамилия"
                onChange={(event) => setCreateForm((current) => ({ ...current, lastName: event.target.value }))}
                required
                sx={{ flex: 1 }}
                value={createForm.lastName}
              />
            </Stack>
            <TextField
              label="Username"
              onChange={(event) => setCreateForm((current) => ({ ...current, username: event.target.value }))}
              required
              value={createForm.username}
            />
            <TextField
              label="Email"
              onChange={(event) => setCreateForm((current) => ({ ...current, email: event.target.value }))}
              required
              type="email"
              value={createForm.email}
            />
            <TextField
              label="Пароль"
              onChange={(event) => setCreateForm((current) => ({ ...current, password: event.target.value }))}
              required
              type="password"
              value={createForm.password}
            />
            <TextField
              label="Роли"
              helperText={canReadRoles ? `Выбрано: ${renderRoleNames(roles.filter((role) => createForm.roleIds.includes(role.id)))}` : 'Список ролей недоступен'}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  roleIds: typeof event.target.value === 'string' ? event.target.value.split(',') : event.target.value,
                }))
              }
              select
              SelectProps={{
                multiple: true,
                renderValue: (selected) =>
                  roles
                    .filter((role) => selected.includes(role.id))
                    .map((role) => role.name)
                    .join(', '),
              }}
              value={createForm.roleIds}
            >
              {roles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name}
                </MenuItem>
              ))}
            </TextField>
            <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
              <Switch
                checked={createForm.isActive}
                onChange={(event) =>
                  setCreateForm((current) => ({ ...current, isActive: event.target.checked }))
                }
              />
              <Typography>Пользователь активен</Typography>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button disabled={isMutating} onClick={() => setCreateDialogOpen(false)}>
              Отмена
            </Button>
            <Button disabled={isMutating} type="submit" variant="contained">
              Создать
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog
        fullWidth
        maxWidth="sm"
        onClose={() => !isMutating && setEditDialogOpen(false)}
        open={editDialogOpen}
      >
        <Box component="form" onSubmit={handleEditSubmit}>
          <DialogTitle>Редактировать пользователя</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            {mutationError ? <Alert severity="error">{mutationError}</Alert> : null}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Имя"
                onChange={(event) => setEditForm((current) => ({ ...current, firstName: event.target.value }))}
                required
                sx={{ flex: 1 }}
                value={editForm.firstName}
              />
              <TextField
                label="Фамилия"
                onChange={(event) => setEditForm((current) => ({ ...current, lastName: event.target.value }))}
                required
                sx={{ flex: 1 }}
                value={editForm.lastName}
              />
            </Stack>
            <TextField
              label="Username"
              onChange={(event) => setEditForm((current) => ({ ...current, username: event.target.value }))}
              required
              value={editForm.username}
            />
            <TextField
              label="Email"
              onChange={(event) => setEditForm((current) => ({ ...current, email: event.target.value }))}
              required
              type="email"
              value={editForm.email}
            />
            <TextField
              helperText="Оставьте пустым, если пароль менять не нужно."
              label="Новый пароль"
              onChange={(event) => setEditForm((current) => ({ ...current, password: event.target.value }))}
              type="password"
              value={editForm.password}
            />
            <TextField
              label="Роли"
              helperText={canReadRoles ? `Выбрано: ${renderRoleNames(roles.filter((role) => editForm.roleIds.includes(role.id)))}` : 'Список ролей недоступен'}
              onChange={(event) =>
                setEditForm((current) => ({
                  ...current,
                  roleIds: typeof event.target.value === 'string' ? event.target.value.split(',') : event.target.value,
                }))
              }
              select
              SelectProps={{
                multiple: true,
                renderValue: (selected) =>
                  roles
                    .filter((role) => selected.includes(role.id))
                    .map((role) => role.name)
                    .join(', '),
              }}
              value={editForm.roleIds}
            >
              {roles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name}
                </MenuItem>
              ))}
            </TextField>
            <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
              <Switch
                checked={editForm.isActive}
                onChange={(event) =>
                  setEditForm((current) => ({ ...current, isActive: event.target.checked }))
                }
              />
              <Typography>Пользователь активен</Typography>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button disabled={isMutating} onClick={() => setEditDialogOpen(false)}>
              Отмена
            </Button>
            <Button disabled={isMutating} type="submit" variant="contained">
              Сохранить
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  )
}
