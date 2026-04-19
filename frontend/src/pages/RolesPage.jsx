import AddRoundedIcon from '@mui/icons-material/AddRounded'
import ShieldRoundedIcon from '@mui/icons-material/ShieldRounded'
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
  TextField,
  Typography,
} from '@mui/material'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchPermissions } from '../api/permissions'
import { createRole, fetchRoles } from '../api/roles'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { formatNumber } from '../utils/format'

const emptyRoleForm = {
  name: '',
  description: '',
  permissionIds: [],
}

export function RolesPage() {
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canManageRoles = hasPermission('roles.manage')
  const canReadPermissions = hasPermission('permissions.read')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [createForm, setCreateForm] = useState(emptyRoleForm)

  const rolesQuery = useQuery({
    queryKey: ['admin', 'roles'],
    queryFn: fetchRoles,
  })
  const permissionsQuery = useQuery({
    queryKey: ['admin', 'permissions'],
    queryFn: fetchPermissions,
    enabled: canReadPermissions,
  })

  const roles = rolesQuery.data ?? []
  const permissions = permissionsQuery.data ?? []
  const isInitialLoading = rolesQuery.isLoading && roles.length === 0
  const permissionCount = permissions.length
  const populatedRolesCount = roles.filter((role) => role.permissions.length > 0).length

  const createRoleMutation = useMutation({
    mutationFn: createRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
      setCreateDialogOpen(false)
      setCreateForm(emptyRoleForm)
    },
  })

  function openCreateDialog() {
    setCreateForm(emptyRoleForm)
    setCreateDialogOpen(true)
  }

  function handleCreateSubmit(event) {
    event.preventDefault()
    createRoleMutation.mutate({
      name: createForm.name.trim(),
      description: createForm.description.trim() || null,
      permission_ids: createForm.permissionIds,
    })
  }

  const createError = createRoleMutation.error?.message

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Admin"
        title="Роли и права"
        description="Создание ролей и просмотр permission-наборов, которыми потом управляются пользователи."
        actions={
          canManageRoles ? (
            <Button onClick={openCreateDialog} startIcon={<AddRoundedIcon />} variant="contained">
              Новая роль
            </Button>
          ) : null
        }
      />

      {rolesQuery.isError ? (
        <Alert severity="error">
          Не удалось загрузить роли из API. {rolesQuery.error.message}
        </Alert>
      ) : null}
      {canReadPermissions && permissionsQuery.isError ? (
        <Alert severity="warning">
          Список permissions недоступен. Создание роли без выбора прав будет ограничено.
        </Alert>
      ) : null}
      {!canManageRoles ? (
        <Alert severity="info">
          У текущего пользователя есть доступ к просмотру ролей, но создание скрыто без `roles.manage`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Всего ролей" value={formatNumber(roles.length)} />
        <StatCard accent="secondary.main" label="Ролей с правами" value={formatNumber(populatedRolesCount)} />
        <StatCard accent="primary.main" label="Доступных permissions" value={formatNumber(permissionCount)} />
      </Box>

      <SectionCard
        title="Роли системы"
        subtitle="Роли используются при назначении пользователей и формируют доступ к разделам frontend и backend."
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} height={140} variant="rounded" />
            ))}
          </Box>
        ) : roles.length ? (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', xl: 'repeat(2, minmax(0, 1fr))' },
            }}
          >
            {roles.map((role) => (
              <Box
                key={role.id}
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 4,
                  display: 'grid',
                  gap: 2,
                  p: 2.5,
                }}
              >
                <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                  <Stack direction="row" spacing={1.25} sx={{ alignItems: 'center' }}>
                    <Box
                      sx={{
                        alignItems: 'center',
                        bgcolor: 'primary.main',
                        borderRadius: 3,
                        color: 'primary.contrastText',
                        display: 'inline-flex',
                        height: 40,
                        justifyContent: 'center',
                        width: 40,
                      }}
                    >
                      <ShieldRoundedIcon fontSize="small" />
                    </Box>
                    <Box>
                      <Typography sx={{ fontWeight: 800 }}>{role.name}</Typography>
                      <Typography color="text.secondary">
                        {role.description || 'Описание роли не заполнено.'}
                      </Typography>
                    </Box>
                  </Stack>
                  <Chip
                    label={`${role.permissions.length} прав`}
                    size="small"
                    variant="outlined"
                  />
                </Stack>

                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                  {role.permissions.length ? (
                    role.permissions.map((permission) => (
                      <Chip key={permission.id} label={permission.code} size="small" />
                    ))
                  ) : (
                    <Typography color="text.secondary">У роли пока нет permissions.</Typography>
                  )}
                </Stack>
              </Box>
            ))}
          </Box>
        ) : (
          <EmptyState
            title="Роли не найдены"
            description="В системе пока нет ролей, доступных для просмотра."
          />
        )}
      </SectionCard>

      <SectionCard
        title="Справочник permissions"
        subtitle="Список backend-прав, доступных для включения в новые роли."
      >
        {!canReadPermissions ? (
          <EmptyState
            title="Permissions скрыты"
            description="Для просмотра этого списка нужен доступ `permissions.read`."
          />
        ) : permissionsQuery.isLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} height={60} variant="rounded" />
            ))}
          </Box>
        ) : permissions.length ? (
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
            {permissions.map((permission) => (
              <Chip
                key={permission.id}
                label={permission.code}
                title={permission.description || permission.code}
                variant="outlined"
              />
            ))}
          </Stack>
        ) : (
          <EmptyState
            title="Permissions не найдены"
            description="Справочник прав доступа пока пуст."
          />
        )}
      </SectionCard>

      <Dialog
        fullWidth
        maxWidth="sm"
        onClose={() => !createRoleMutation.isPending && setCreateDialogOpen(false)}
        open={createDialogOpen}
      >
        <Box component="form" onSubmit={handleCreateSubmit}>
          <DialogTitle>Создать роль</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            {createError ? <Alert severity="error">{createError}</Alert> : null}
            <TextField
              label="Название роли"
              onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))}
              required
              value={createForm.name}
            />
            <TextField
              label="Описание"
              minRows={3}
              multiline
              onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))}
              value={createForm.description}
            />
            <TextField
              disabled={!canReadPermissions}
              helperText={
                canReadPermissions
                  ? `${formatNumber(createForm.permissionIds.length)} permissions выбрано`
                  : 'Для выбора прав нужен доступ permissions.read'
              }
              label="Permissions"
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  permissionIds:
                    typeof event.target.value === 'string'
                      ? event.target.value.split(',')
                      : event.target.value,
                }))
              }
              select
              SelectProps={{
                multiple: true,
                renderValue: (selected) =>
                  permissions
                    .filter((permission) => selected.includes(permission.id))
                    .map((permission) => permission.code)
                    .join(', '),
              }}
              value={createForm.permissionIds}
            >
              {permissions.map((permission) => (
                <MenuItem key={permission.id} value={permission.id}>
                  <Box>
                    <Typography sx={{ fontWeight: 700 }}>{permission.code}</Typography>
                    <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                      {permission.description || 'Описание не задано'}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </TextField>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button disabled={createRoleMutation.isPending} onClick={() => setCreateDialogOpen(false)}>
              Отмена
            </Button>
            <Button disabled={createRoleMutation.isPending} type="submit" variant="contained">
              Создать
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  )
}
