import AddRoundedIcon from '@mui/icons-material/AddRounded'
import CategoryRoundedIcon from '@mui/icons-material/CategoryRounded'
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import LinkRoundedIcon from '@mui/icons-material/LinkRounded'
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
import {
  createEquipmentType,
  createEquipmentTypeParameterBinding,
  createParameter,
  deleteEquipmentType,
  deleteEquipmentTypeParameterBinding,
  deleteParameter,
  fetchEquipmentTypeParameters,
  fetchEquipmentTypes,
  fetchParameters,
  updateEquipmentType,
  updateParameter,
} from '../api/equipment'
import { useAuth } from '../auth/useAuth'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

const emptyTypeForm = {
  name: '',
  description: '',
  isActive: true,
}

const emptyParameterForm = {
  code: '',
  name: '',
  unit: '',
  description: '',
  isActive: true,
}

const emptyBindingForm = {
  equipmentTypeId: '',
  parameterId: '',
  isRequired: true,
}

function buildTypePayload(formState) {
  return {
    name: formState.name.trim(),
    description: formState.description.trim() || null,
    is_active: formState.isActive,
  }
}

function buildParameterPayload(formState) {
  return {
    code: formState.code.trim(),
    name: formState.name.trim(),
    unit: formState.unit.trim() || null,
    description: formState.description.trim() || null,
    is_active: formState.isActive,
  }
}

function buildBindingPayload(formState) {
  return {
    equipment_type_id: formState.equipmentTypeId,
    parameter_id: formState.parameterId,
    is_required: formState.isRequired,
  }
}

function typeFormFromItem(item) {
  return {
    name: item.name,
    description: item.description ?? '',
    isActive: item.is_active,
  }
}

function parameterFormFromItem(item) {
  return {
    code: item.code,
    name: item.name,
    unit: item.unit ?? '',
    description: item.description ?? '',
    isActive: item.is_active,
  }
}

function getActiveCount(items) {
  return items.filter((item) => item.is_active).length
}

export function MonitoringCatalogsPage() {
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canManageEquipment = hasPermission('equipment.manage')
  const [typeSearch, setTypeSearch] = useState('')
  const [parameterSearch, setParameterSearch] = useState('')
  const [bindingTypeFilter, setBindingTypeFilter] = useState('')
  const [bindingParameterFilter, setBindingParameterFilter] = useState('')
  const [typeDialogOpen, setTypeDialogOpen] = useState(false)
  const [parameterDialogOpen, setParameterDialogOpen] = useState(false)
  const [bindingDialogOpen, setBindingDialogOpen] = useState(false)
  const [editType, setEditType] = useState(null)
  const [editParameter, setEditParameter] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [typeForm, setTypeForm] = useState(emptyTypeForm)
  const [parameterForm, setParameterForm] = useState(emptyParameterForm)
  const [bindingForm, setBindingForm] = useState(emptyBindingForm)
  const [feedback, setFeedback] = useState({ open: false, message: '' })

  const equipmentTypesQuery = useQuery({
    queryKey: ['equipment-types', 'catalogs'],
    queryFn: fetchEquipmentTypes,
  })
  const parametersQuery = useQuery({
    queryKey: ['parameters', 'catalogs'],
    queryFn: fetchParameters,
  })
  const bindingsQuery = useQuery({
    queryKey: ['equipment-type-parameters', 'catalogs', bindingTypeFilter, bindingParameterFilter],
    queryFn: () =>
      fetchEquipmentTypeParameters({
        ...(bindingTypeFilter ? { equipment_type_id: bindingTypeFilter } : {}),
        ...(bindingParameterFilter ? { parameter_id: bindingParameterFilter } : {}),
      }),
  })

  const equipmentTypes = equipmentTypesQuery.data ?? []
  const parameters = parametersQuery.data ?? []
  const bindings = bindingsQuery.data ?? []
  const normalizedTypeSearch = typeSearch.trim().toLowerCase()
  const normalizedParameterSearch = parameterSearch.trim().toLowerCase()
  const visibleTypes = normalizedTypeSearch
    ? equipmentTypes.filter((item) =>
        [item.name, item.description].filter(Boolean).join(' ').toLowerCase().includes(normalizedTypeSearch),
      )
    : equipmentTypes
  const visibleParameters = normalizedParameterSearch
    ? parameters.filter((item) =>
        [item.code, item.name, item.unit, item.description]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
          .includes(normalizedParameterSearch),
      )
    : parameters
  const requiredBindingsCount = bindings.filter((item) => item.is_required).length

  const createTypeMutation = useMutation({
    mutationFn: createEquipmentType,
    onSuccess: () => {
      invalidateCatalogs()
      setTypeDialogOpen(false)
      setTypeForm(emptyTypeForm)
      showFeedback('Тип оборудования создан.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const updateTypeMutation = useMutation({
    mutationFn: ({ equipmentTypeId, payload }) => updateEquipmentType(equipmentTypeId, payload),
    onSuccess: () => {
      invalidateCatalogs()
      setEditType(null)
      setTypeForm(emptyTypeForm)
      showFeedback('Тип оборудования обновлен.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const deleteTypeMutation = useMutation({
    mutationFn: deleteEquipmentType,
    onSuccess: () => {
      invalidateCatalogs()
      setDeleteTarget(null)
      showFeedback('Тип оборудования удален.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const createParameterMutation = useMutation({
    mutationFn: createParameter,
    onSuccess: () => {
      invalidateCatalogs()
      setParameterDialogOpen(false)
      setParameterForm(emptyParameterForm)
      showFeedback('Параметр создан.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const updateParameterMutation = useMutation({
    mutationFn: ({ parameterId, payload }) => updateParameter(parameterId, payload),
    onSuccess: () => {
      invalidateCatalogs()
      setEditParameter(null)
      setParameterForm(emptyParameterForm)
      showFeedback('Параметр обновлен.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const deleteParameterMutation = useMutation({
    mutationFn: deleteParameter,
    onSuccess: () => {
      invalidateCatalogs()
      setDeleteTarget(null)
      showFeedback('Параметр удален.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const createBindingMutation = useMutation({
    mutationFn: createEquipmentTypeParameterBinding,
    onSuccess: () => {
      invalidateCatalogs()
      setBindingDialogOpen(false)
      setBindingForm(emptyBindingForm)
      showFeedback('Привязка параметра создана.')
    },
    onError: (error) => showFeedback(error.message),
  })
  const deleteBindingMutation = useMutation({
    mutationFn: deleteEquipmentTypeParameterBinding,
    onSuccess: () => {
      invalidateCatalogs()
      setDeleteTarget(null)
      showFeedback('Привязка параметра удалена.')
    },
    onError: (error) => showFeedback(error.message),
  })

  const isSubmitting =
    createTypeMutation.isPending ||
    updateTypeMutation.isPending ||
    deleteTypeMutation.isPending ||
    createParameterMutation.isPending ||
    updateParameterMutation.isPending ||
    deleteParameterMutation.isPending ||
    createBindingMutation.isPending ||
    deleteBindingMutation.isPending

  function invalidateCatalogs() {
    queryClient.invalidateQueries({ queryKey: ['equipment-types'] })
    queryClient.invalidateQueries({ queryKey: ['parameters'] })
    queryClient.invalidateQueries({ queryKey: ['equipment-type-parameters'] })
    queryClient.invalidateQueries({ queryKey: ['equipment'] })
    queryClient.invalidateQueries({ queryKey: ['threshold-rules'] })
  }

  function showFeedback(message) {
    setFeedback({ open: true, message })
  }

  function resetFilters() {
    setTypeSearch('')
    setParameterSearch('')
    setBindingTypeFilter('')
    setBindingParameterFilter('')
  }

  function openTypeCreateDialog() {
    setTypeForm(emptyTypeForm)
    setTypeDialogOpen(true)
  }

  function openTypeEditDialog(item) {
    setEditType(item)
    setTypeForm(typeFormFromItem(item))
  }

  function openParameterCreateDialog() {
    setParameterForm(emptyParameterForm)
    setParameterDialogOpen(true)
  }

  function openParameterEditDialog(item) {
    setEditParameter(item)
    setParameterForm(parameterFormFromItem(item))
  }

  function closeTypeDialog() {
    if (isSubmitting) {
      return
    }
    setTypeDialogOpen(false)
    setEditType(null)
    setTypeForm(emptyTypeForm)
  }

  function closeParameterDialog() {
    if (isSubmitting) {
      return
    }
    setParameterDialogOpen(false)
    setEditParameter(null)
    setParameterForm(emptyParameterForm)
  }

  function closeBindingDialog() {
    if (isSubmitting) {
      return
    }
    setBindingDialogOpen(false)
    setBindingForm(emptyBindingForm)
  }

  function submitType(event) {
    event.preventDefault()
    const payload = buildTypePayload(typeForm)
    if (editType) {
      updateTypeMutation.mutate({ equipmentTypeId: editType.id, payload })
      return
    }
    createTypeMutation.mutate(payload)
  }

  function submitParameter(event) {
    event.preventDefault()
    const payload = buildParameterPayload(parameterForm)
    if (editParameter) {
      updateParameterMutation.mutate({ parameterId: editParameter.id, payload })
      return
    }
    createParameterMutation.mutate(payload)
  }

  function submitBinding(event) {
    event.preventDefault()
    createBindingMutation.mutate(buildBindingPayload(bindingForm))
  }

  function confirmDelete() {
    if (!deleteTarget) {
      return
    }

    if (deleteTarget.kind === 'equipmentType') {
      deleteTypeMutation.mutate(deleteTarget.item.id)
      return
    }
    if (deleteTarget.kind === 'parameter') {
      deleteParameterMutation.mutate(deleteTarget.item.id)
      return
    }
    deleteBindingMutation.mutate(deleteTarget.item.id)
  }

  function getDeleteDescription() {
    if (!deleteTarget) {
      return ''
    }

    if (deleteTarget.kind === 'equipmentType') {
      return `Тип "${deleteTarget.item.name}" будет удален, если он не используется оборудованием и привязками.`
    }
    if (deleteTarget.kind === 'parameter') {
      return `Параметр "${deleteTarget.item.name}" будет удален, если он не используется телеметрией, порогами и привязками.`
    }
    return `Привязка "${deleteTarget.item.parameter.name}" к "${deleteTarget.item.equipment_type.name}" будет удалена.`
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Администрирование"
        title="Справочники мониторинга"
        description="Типы оборудования, измеряемые параметры и привязки параметров к типам техники для телеметрии и пороговых правил."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button onClick={resetFilters} startIcon={<CategoryRoundedIcon />} variant="outlined">
              Сбросить фильтры
            </Button>
            {canManageEquipment ? (
              <Button onClick={() => setBindingDialogOpen(true)} startIcon={<LinkRoundedIcon />} variant="contained">
                Новая привязка
              </Button>
            ) : null}
          </Stack>
        }
      />

      {equipmentTypesQuery.isError || parametersQuery.isError || bindingsQuery.isError ? (
        <Alert severity="error">
          Не удалось загрузить один из справочников. Проверьте право `equipment.read` и доступность API.
        </Alert>
      ) : null}
      {!canManageEquipment ? (
        <Alert severity="info">
          У текущего пользователя есть просмотр справочников, но изменения скрыты без `equipment.manage`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(4, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Типов оборудования" value={formatNumber(equipmentTypes.length)} />
        <StatCard accent="success.main" label="Активных типов" value={formatNumber(getActiveCount(equipmentTypes))} />
        <StatCard label="Параметров" value={formatNumber(parameters.length)} />
        <StatCard accent="primary.main" label="Привязок" value={formatNumber(bindings.length)} />
      </Box>

      <SectionCard
        title="Типы оборудования"
        subtitle="Базовый справочник: самосвалы, экскаваторы, буровые установки и другие классы техники."
        action={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <TextField
              label="Поиск"
              onChange={(event) => setTypeSearch(event.target.value)}
              placeholder="Название или описание"
              size="small"
              sx={{ minWidth: 260 }}
              value={typeSearch}
            />
            {canManageEquipment ? (
              <Button onClick={openTypeCreateDialog} startIcon={<AddRoundedIcon />} variant="outlined">
                Новый тип
              </Button>
            ) : null}
          </Stack>
        }
      >
        {equipmentTypesQuery.isLoading && !equipmentTypes.length ? (
          <Skeleton height={220} variant="rounded" />
        ) : visibleTypes.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 840 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Название</TableCell>
                  <TableCell>Описание</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Обновлено</TableCell>
                  {canManageEquipment ? <TableCell align="right">Действия</TableCell> : null}
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleTypes.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{item.name}</Typography>
                    </TableCell>
                    <TableCell>{item.description || 'Описание не указано.'}</TableCell>
                    <TableCell>
                      <StatusChip value={item.is_active ? 'active' : 'inactive'} />
                    </TableCell>
                    <TableCell>{formatDateTime(item.updated_at)}</TableCell>
                    {canManageEquipment ? (
                      <TableCell align="right">
                        <Tooltip title="Редактировать">
                          <IconButton onClick={() => openTypeEditDialog(item)}>
                            <EditRoundedIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Удалить">
                          <IconButton
                            color="error"
                            onClick={() => setDeleteTarget({ kind: 'equipmentType', item })}
                          >
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
            title="Типы оборудования не найдены"
            description="Сбросьте поиск или создайте новый тип оборудования."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <SectionCard
        title="Параметры телеметрии"
        subtitle="Справочник измеряемых величин: температура, давление, вибрация, моточасы и другие показатели."
        action={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <TextField
              label="Поиск"
              onChange={(event) => setParameterSearch(event.target.value)}
              placeholder="Код, название, единица"
              size="small"
              sx={{ minWidth: 260 }}
              value={parameterSearch}
            />
            {canManageEquipment ? (
              <Button onClick={openParameterCreateDialog} startIcon={<AddRoundedIcon />} variant="outlined">
                Новый параметр
              </Button>
            ) : null}
          </Stack>
        }
      >
        {parametersQuery.isLoading && !parameters.length ? (
          <Skeleton height={220} variant="rounded" />
        ) : visibleParameters.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 940 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Код</TableCell>
                  <TableCell>Название</TableCell>
                  <TableCell>Ед. изм.</TableCell>
                  <TableCell>Описание</TableCell>
                  <TableCell>Статус</TableCell>
                  {canManageEquipment ? <TableCell align="right">Действия</TableCell> : null}
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleParameters.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 800 }}>{item.code}</Typography>
                    </TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.unit || 'без единицы'}</TableCell>
                    <TableCell>{item.description || 'Описание не указано.'}</TableCell>
                    <TableCell>
                      <StatusChip value={item.is_active ? 'active' : 'inactive'} />
                    </TableCell>
                    {canManageEquipment ? (
                      <TableCell align="right">
                        <Tooltip title="Редактировать">
                          <IconButton onClick={() => openParameterEditDialog(item)}>
                            <EditRoundedIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Удалить">
                          <IconButton
                            color="error"
                            onClick={() => setDeleteTarget({ kind: 'parameter', item })}
                          >
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
            title="Параметры не найдены"
            description="Сбросьте поиск или создайте новый параметр телеметрии."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <SectionCard
        title="Привязки параметров к типам"
        subtitle="Определяет, какие параметры доступны для ввода телеметрии у конкретного типа оборудования."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Тип оборудования"
              onChange={(event) => setBindingTypeFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={bindingTypeFilter}
            >
              <MenuItem value="">Все типы</MenuItem>
              {equipmentTypes.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Параметр"
              onChange={(event) => setBindingParameterFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={bindingParameterFilter}
            >
              <MenuItem value="">Все параметры</MenuItem>
              {parameters.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        }
      >
        <Box sx={{ mb: 2 }}>
          <StatCard
            accent="warning.main"
            label="Обязательных привязок"
            value={formatNumber(requiredBindingsCount)}
          />
        </Box>
        {bindingsQuery.isLoading && !bindings.length ? (
          <Skeleton height={220} variant="rounded" />
        ) : bindings.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 860 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Тип оборудования</TableCell>
                  <TableCell>Параметр</TableCell>
                  <TableCell>Ед. изм.</TableCell>
                  <TableCell>Обязательность</TableCell>
                  <TableCell>Создано</TableCell>
                  {canManageEquipment ? <TableCell align="right">Действия</TableCell> : null}
                </TableRow>
              </TableHead>
              <TableBody>
                {bindings.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.equipment_type.name}</TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{item.parameter.name}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {item.parameter.code}
                      </Typography>
                    </TableCell>
                    <TableCell>{item.parameter.unit || 'без единицы'}</TableCell>
                    <TableCell>{item.is_required ? 'Обязательный' : 'Опциональный'}</TableCell>
                    <TableCell>{formatDateTime(item.created_at)}</TableCell>
                    {canManageEquipment ? (
                      <TableCell align="right">
                        <Tooltip title="Удалить привязку">
                          <IconButton
                            color="error"
                            onClick={() => setDeleteTarget({ kind: 'binding', item })}
                          >
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
            title="Привязки не найдены"
            description="Создайте связь между типом оборудования и параметром, чтобы параметр появился в форме ввода телеметрии."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>

      <Dialog fullWidth maxWidth="sm" open={typeDialogOpen || Boolean(editType)} onClose={closeTypeDialog}>
        <Box component="form" onSubmit={submitType}>
          <DialogTitle>{editType ? 'Редактировать тип оборудования' : 'Создать тип оборудования'}</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              label="Название"
              onChange={(event) => setTypeForm((current) => ({ ...current, name: event.target.value }))}
              required
              value={typeForm.name}
            />
            <TextField
              label="Описание"
              multiline
              minRows={3}
              onChange={(event) => setTypeForm((current) => ({ ...current, description: event.target.value }))}
              value={typeForm.description}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={typeForm.isActive}
                  onChange={(event) =>
                    setTypeForm((current) => ({ ...current, isActive: event.target.checked }))
                  }
                />
              }
              label="Тип активен"
            />
          </DialogContent>
          <DialogActions>
            <Button disabled={isSubmitting} onClick={closeTypeDialog}>
              Отмена
            </Button>
            <Button disabled={isSubmitting} type="submit" variant="contained">
              {editType ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog
        fullWidth
        maxWidth="sm"
        open={parameterDialogOpen || Boolean(editParameter)}
        onClose={closeParameterDialog}
      >
        <Box component="form" onSubmit={submitParameter}>
          <DialogTitle>{editParameter ? 'Редактировать параметр' : 'Создать параметр'}</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              label="Код"
              onChange={(event) => setParameterForm((current) => ({ ...current, code: event.target.value }))}
              required
              value={parameterForm.code}
            />
            <TextField
              label="Название"
              onChange={(event) => setParameterForm((current) => ({ ...current, name: event.target.value }))}
              required
              value={parameterForm.name}
            />
            <TextField
              label="Единица измерения"
              onChange={(event) => setParameterForm((current) => ({ ...current, unit: event.target.value }))}
              value={parameterForm.unit}
            />
            <TextField
              label="Описание"
              multiline
              minRows={3}
              onChange={(event) =>
                setParameterForm((current) => ({ ...current, description: event.target.value }))
              }
              value={parameterForm.description}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={parameterForm.isActive}
                  onChange={(event) =>
                    setParameterForm((current) => ({ ...current, isActive: event.target.checked }))
                  }
                />
              }
              label="Параметр активен"
            />
          </DialogContent>
          <DialogActions>
            <Button disabled={isSubmitting} onClick={closeParameterDialog}>
              Отмена
            </Button>
            <Button disabled={isSubmitting} type="submit" variant="contained">
              {editParameter ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog fullWidth maxWidth="sm" open={bindingDialogOpen} onClose={closeBindingDialog}>
        <Box component="form" onSubmit={submitBinding}>
          <DialogTitle>Создать привязку параметра</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <TextField
              label="Тип оборудования"
              onChange={(event) =>
                setBindingForm((current) => ({ ...current, equipmentTypeId: event.target.value }))
              }
              required
              select
              value={bindingForm.equipmentTypeId}
            >
              {equipmentTypes.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Параметр"
              onChange={(event) => setBindingForm((current) => ({ ...current, parameterId: event.target.value }))}
              required
              select
              value={bindingForm.parameterId}
            >
              {parameters.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.name} ({item.code})
                </MenuItem>
              ))}
            </TextField>
            <FormControlLabel
              control={
                <Switch
                  checked={bindingForm.isRequired}
                  onChange={(event) =>
                    setBindingForm((current) => ({ ...current, isRequired: event.target.checked }))
                  }
                />
              }
              label="Параметр обязателен для типа оборудования"
            />
          </DialogContent>
          <DialogActions>
            <Button disabled={isSubmitting} onClick={closeBindingDialog}>
              Отмена
            </Button>
            <Button disabled={isSubmitting} type="submit" variant="contained">
              Создать
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <ConfirmDialog
        confirmColor="error"
        confirmLabel="Удалить"
        description={getDeleteDescription()}
        onClose={() => !isSubmitting && setDeleteTarget(null)}
        onConfirm={confirmDelete}
        open={Boolean(deleteTarget)}
        title="Удалить запись справочника?"
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
