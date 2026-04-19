import AddRoundedIcon from '@mui/icons-material/AddRounded'
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import EventRepeatRoundedIcon from '@mui/icons-material/EventRepeatRounded'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  MenuItem,
  Skeleton,
  Snackbar,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchEquipmentList, fetchEquipmentTypes } from '../api/equipment'
import {
  createMaintenancePlan,
  deleteMaintenancePlan,
  fetchMaintenancePlans,
  updateMaintenancePlan,
} from '../api/maintenance'
import { useAuth } from '../auth/useAuth'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

const emptyPlanForm = {
  targetType: 'equipment_type',
  equipmentTypeId: '',
  equipmentId: '',
  title: '',
  description: '',
  intervalHours: '',
  intervalDays: '',
  isActive: true,
}

function toOptionalInt(value) {
  return value === '' || value === null || value === undefined ? null : Number(value)
}

function getTargetLabel(plan) {
  if (plan.equipment) {
    return `${plan.equipment.name} (${plan.equipment.code})`
  }

  if (plan.equipment_type) {
    return plan.equipment_type.name
  }

  return 'Цель не указана'
}

function getTargetKind(plan) {
  return plan.equipment ? 'Оборудование' : 'Тип оборудования'
}

function getIntervalLabel(plan) {
  const parts = [
    plan.interval_hours ? `каждые ${formatNumber(plan.interval_hours)} м/ч` : null,
    plan.interval_days ? `каждые ${formatNumber(plan.interval_days)} дн.` : null,
  ].filter(Boolean)

  return parts.length ? parts.join(' / ') : 'Интервал не задан'
}

function buildPlanPayload(formState) {
  const isEquipmentTarget = formState.targetType === 'equipment'

  return {
    equipment_type_id: isEquipmentTarget ? null : formState.equipmentTypeId,
    equipment_id: isEquipmentTarget ? formState.equipmentId : null,
    title: formState.title.trim(),
    description: formState.description.trim() || null,
    interval_hours: toOptionalInt(formState.intervalHours),
    interval_days: toOptionalInt(formState.intervalDays),
    is_active: formState.isActive,
  }
}

function formFromPlan(plan) {
  return {
    targetType: plan.equipment ? 'equipment' : 'equipment_type',
    equipmentTypeId: plan.equipment_type?.id ?? '',
    equipmentId: plan.equipment?.id ?? '',
    title: plan.title,
    description: plan.description ?? '',
    intervalHours: plan.interval_hours ?? '',
    intervalDays: plan.interval_days ?? '',
    isActive: plan.is_active,
  }
}

function getSearchHaystack(plan) {
  return [
    plan.title,
    plan.description,
    plan.equipment_type?.name,
    plan.equipment?.name,
    plan.equipment?.code,
    plan.equipment?.equipment_type?.name,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

export function MaintenancePlansPage() {
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canManageMaintenance = hasPermission('maintenance.manage')
  const [equipmentTypeFilter, setEquipmentTypeFilter] = useState('')
  const [equipmentFilter, setEquipmentFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  const [searchFilter, setSearchFilter] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editPlan, setEditPlan] = useState(null)
  const [deletePlan, setDeletePlan] = useState(null)
  const [formState, setFormState] = useState(emptyPlanForm)
  const [feedback, setFeedback] = useState({ open: false, message: '', severity: 'success' })

  const plansQuery = useQuery({
    queryKey: ['maintenance', 'plans', equipmentTypeFilter, equipmentFilter, activeFilter],
    queryFn: () =>
      fetchMaintenancePlans({
        ...(equipmentTypeFilter ? { equipment_type_id: equipmentTypeFilter } : {}),
        ...(equipmentFilter ? { equipment_id: equipmentFilter } : {}),
        ...(activeFilter ? { is_active: activeFilter } : {}),
      }),
  })
  const equipmentTypesQuery = useQuery({
    queryKey: ['equipment-types', 'maintenance-plan-options'],
    queryFn: fetchEquipmentTypes,
  })
  const equipmentQuery = useQuery({
    queryKey: ['equipment', 'maintenance-plan-options'],
    queryFn: fetchEquipmentList,
  })

  const plans = plansQuery.data ?? []
  const normalizedSearch = searchFilter.trim().toLowerCase()
  const filteredPlans = normalizedSearch
    ? plans.filter((plan) => getSearchHaystack(plan).includes(normalizedSearch))
    : plans
  const equipmentTypes = equipmentTypesQuery.data ?? []
  const equipment = equipmentQuery.data ?? []
  const activePlansCount = filteredPlans.filter((plan) => plan.is_active).length
  const inactivePlansCount = filteredPlans.length - activePlansCount
  const equipmentTargetCount = filteredPlans.filter((plan) => Boolean(plan.equipment)).length
  const typeTargetCount = filteredPlans.length - equipmentTargetCount
  const isInitialLoading = plansQuery.isLoading && plans.length === 0

  const createPlanMutation = useMutation({
    mutationFn: createMaintenancePlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
      setCreateDialogOpen(false)
      setFormState(emptyPlanForm)
      setFeedback({ open: true, message: 'План ТО создан.', severity: 'success' })
    },
    onError: (error) => {
      setFeedback({ open: true, message: error.message, severity: 'error' })
    },
  })

  const updatePlanMutation = useMutation({
    mutationFn: ({ planId, payload }) => updateMaintenancePlan(planId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
      setEditPlan(null)
      setFormState(emptyPlanForm)
      setFeedback({ open: true, message: 'План ТО обновлен.', severity: 'success' })
    },
    onError: (error) => {
      setFeedback({ open: true, message: error.message, severity: 'error' })
    },
  })

  const deletePlanMutation = useMutation({
    mutationFn: deleteMaintenancePlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
      setDeletePlan(null)
      setFeedback({ open: true, message: 'План ТО удален.', severity: 'success' })
    },
    onError: (error) => {
      setFeedback({ open: true, message: error.message, severity: 'error' })
    },
  })

  const isSubmitting =
    createPlanMutation.isPending || updatePlanMutation.isPending || deletePlanMutation.isPending

  function resetFilters() {
    setEquipmentTypeFilter('')
    setEquipmentFilter('')
    setActiveFilter('')
    setSearchFilter('')
  }

  function openCreateDialog() {
    setFormState(emptyPlanForm)
    setCreateDialogOpen(true)
  }

  function openEditDialog(plan) {
    setEditPlan(plan)
    setFormState(formFromPlan(plan))
  }

  function closeDialog() {
    if (isSubmitting) {
      return
    }
    setCreateDialogOpen(false)
    setEditPlan(null)
    setFormState(emptyPlanForm)
  }

  function handleTargetTypeChange(targetType) {
    setFormState((current) => ({
      ...current,
      targetType,
      equipmentTypeId: '',
      equipmentId: '',
    }))
  }

  function submitPlan(event) {
    event.preventDefault()

    const hasTarget =
      formState.targetType === 'equipment' ? formState.equipmentId : formState.equipmentTypeId
    if (!hasTarget) {
      setFeedback({ open: true, message: 'Выберите цель плана ТО.', severity: 'warning' })
      return
    }
    if (!formState.intervalHours && !formState.intervalDays) {
      setFeedback({ open: true, message: 'Укажите интервал в моточасах или днях.', severity: 'warning' })
      return
    }

    const payload = buildPlanPayload(formState)
    if (editPlan) {
      updatePlanMutation.mutate({ planId: editPlan.id, payload })
      return
    }

    createPlanMutation.mutate(payload)
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Техническое обслуживание"
        title="Планы ТО"
        description="Регламенты обслуживания для типов оборудования или конкретных единиц техники с интервалами по моточасам и календарным дням."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button onClick={resetFilters} startIcon={<EventRepeatRoundedIcon />} variant="outlined">
              Сбросить фильтры
            </Button>
            {canManageMaintenance ? (
              <Button onClick={openCreateDialog} startIcon={<AddRoundedIcon />} variant="contained">
                Новый план
              </Button>
            ) : null}
          </Stack>
        }
      />

      {plansQuery.isError ? (
        <Alert severity="error">Не удалось загрузить планы ТО. {plansQuery.error.message}</Alert>
      ) : null}
      {equipmentTypesQuery.isError || equipmentQuery.isError ? (
        <Alert severity="info">
          Один из справочников недоступен. Просмотр планов работает, но создание и фильтры могут быть ограничены.
        </Alert>
      ) : null}
      {!canManageMaintenance ? (
        <Alert severity="info">
          У текущего пользователя есть просмотр планов ТО, но создание, редактирование и удаление скрыты без `maintenance.manage`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(4, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Планов в выборке" value={formatNumber(filteredPlans.length)} />
        <StatCard accent="success.main" label="Активные" value={formatNumber(activePlansCount)} />
        <StatCard accent="text.secondary" label="Отключенные" value={formatNumber(inactivePlansCount)} />
        <StatCard
          accent="primary.main"
          label="Типы / единицы"
          value={`${formatNumber(typeTargetCount)} / ${formatNumber(equipmentTargetCount)}`}
        />
      </Box>

      <SectionCard
        title="Регламенты обслуживания"
        subtitle="План задает периодичность. Далее на его основе можно создавать задачи ТО для исполнителей."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Поиск"
              onChange={(event) => setSearchFilter(event.target.value)}
              placeholder="Название, цель, описание"
              size="small"
              sx={{ minWidth: 240 }}
              value={searchFilter}
            />
            <TextField
              label="Тип оборудования"
              onChange={(event) => setEquipmentTypeFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={equipmentTypeFilter}
            >
              <MenuItem value="">Все типы</MenuItem>
              {equipmentTypes.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Оборудование"
              onChange={(event) => setEquipmentFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 260 }}
              value={equipmentFilter}
            >
              <MenuItem value="">Все оборудование</MenuItem>
              {equipment.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name} ({item.code})
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Активность"
              onChange={(event) => setActiveFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 170 }}
              value={activeFilter}
            >
              <MenuItem value="">Все</MenuItem>
              <MenuItem value="true">Активные</MenuItem>
              <MenuItem value="false">Отключенные</MenuItem>
            </TextField>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} height={82} variant="rounded" />
            ))}
          </Box>
        ) : filteredPlans.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 1080 }}>
              <TableHead>
                <TableRow>
                  <TableCell>План</TableCell>
                  <TableCell>Цель</TableCell>
                  <TableCell>Интервал</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Обновлено</TableCell>
                  {canManageMaintenance ? <TableCell align="right">Действия</TableCell> : null}
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPlans.map((plan) => (
                  <TableRow key={plan.id}>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{plan.title}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {plan.description || 'Описание не указано.'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{getTargetLabel(plan)}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {getTargetKind(plan)}
                      </Typography>
                    </TableCell>
                    <TableCell>{getIntervalLabel(plan)}</TableCell>
                    <TableCell>
                      <StatusChip value={plan.is_active ? 'active' : 'inactive'} />
                    </TableCell>
                    <TableCell>
                      <Typography>{formatDateTime(plan.updated_at)}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        Создано: {formatDateTime(plan.created_at)}
                      </Typography>
                    </TableCell>
                    {canManageMaintenance ? (
                      <TableCell align="right">
                        <Tooltip title="Редактировать">
                          <IconButton onClick={() => openEditDialog(plan)}>
                            <EditRoundedIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Удалить">
                          <IconButton color="error" onClick={() => setDeletePlan(plan)}>
                            <DeleteRoundedIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="Планы ТО не найдены"
            description="По текущим фильтрам регламенты обслуживания отсутствуют. Сбросьте фильтры или создайте новый план."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <Dialog fullWidth maxWidth="sm" open={createDialogOpen || Boolean(editPlan)} onClose={closeDialog}>
        <Box component="form" onSubmit={submitPlan}>
          <DialogTitle>{editPlan ? 'Редактировать план ТО' : 'Создать план ТО'}</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              label="Цель плана"
              onChange={(event) => handleTargetTypeChange(event.target.value)}
              select
              value={formState.targetType}
            >
              <MenuItem value="equipment_type">Тип оборудования</MenuItem>
              <MenuItem value="equipment">Конкретное оборудование</MenuItem>
            </TextField>
            {formState.targetType === 'equipment_type' ? (
              <TextField
                label="Тип оборудования"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, equipmentTypeId: event.target.value }))
                }
                required
                select
                value={formState.equipmentTypeId}
              >
                {equipmentTypes.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.name}
                  </MenuItem>
                ))}
              </TextField>
            ) : (
              <TextField
                label="Оборудование"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, equipmentId: event.target.value }))
                }
                required
                select
                value={formState.equipmentId}
              >
                {equipment.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.name} ({item.code})
                  </MenuItem>
                ))}
              </TextField>
            )}
            <TextField
              label="Название"
              onChange={(event) => setFormState((current) => ({ ...current, title: event.target.value }))}
              required
              value={formState.title}
            />
            <TextField
              label="Описание"
              multiline
              minRows={3}
              onChange={(event) =>
                setFormState((current) => ({ ...current, description: event.target.value }))
              }
              value={formState.description}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                inputProps={{ min: 1 }}
                label="Интервал, моточасы"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, intervalHours: event.target.value }))
                }
                sx={{ flex: 1 }}
                type="number"
                value={formState.intervalHours}
              />
              <TextField
                inputProps={{ min: 1 }}
                label="Интервал, дни"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, intervalDays: event.target.value }))
                }
                sx={{ flex: 1 }}
                type="number"
                value={formState.intervalDays}
              />
            </Stack>
            <FormControlLabel
              control={
                <Switch
                  checked={formState.isActive}
                  onChange={(event) =>
                    setFormState((current) => ({ ...current, isActive: event.target.checked }))
                  }
                />
              }
              label="План активен"
            />
          </DialogContent>
          <DialogActions>
            <Button disabled={isSubmitting} onClick={closeDialog}>
              Отмена
            </Button>
            <Button disabled={isSubmitting} type="submit" variant="contained">
              {editPlan ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <ConfirmDialog
        confirmColor="error"
        confirmLabel="Удалить"
        description={
          deletePlan
            ? `План "${deletePlan.title}" будет удален. История уже выполненных работ останется в журнале.`
            : ''
        }
        onClose={() => !isSubmitting && setDeletePlan(null)}
        onConfirm={() => deletePlanMutation.mutate(deletePlan.id)}
        open={Boolean(deletePlan)}
        title="Удалить план ТО?"
      />

      <Snackbar
        autoHideDuration={4000}
        message={feedback.message}
        onClose={() => setFeedback((current) => ({ ...current, open: false }))}
        open={feedback.open}
      />
    </Box>
  )
}
