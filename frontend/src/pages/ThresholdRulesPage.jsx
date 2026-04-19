import AddRoundedIcon from '@mui/icons-material/AddRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import RuleRoundedIcon from '@mui/icons-material/RuleRounded'
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
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchEquipmentTypeParameterBindings,
  fetchEquipmentTypes,
  fetchParameters,
} from '../api/equipment'
import {
  createThresholdRule,
  deleteThresholdRule,
  fetchThresholdRules,
  updateThresholdRule,
} from '../api/thresholdRules'
import { useAuth } from '../auth/useAuth'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

const emptyRuleForm = {
  equipmentTypeId: '',
  parameterId: '',
  warningMin: '',
  warningMax: '',
  criticalMin: '',
  criticalMax: '',
  isActive: true,
}

function toOptionalNumber(value) {
  return value === '' || value === null || value === undefined ? null : value
}

function buildRulePayload(formState) {
  return {
    equipment_type_id: formState.equipmentTypeId,
    parameter_id: formState.parameterId,
    warning_min: toOptionalNumber(formState.warningMin),
    warning_max: toOptionalNumber(formState.warningMax),
    critical_min: toOptionalNumber(formState.criticalMin),
    critical_max: toOptionalNumber(formState.criticalMax),
    is_active: formState.isActive,
  }
}

function formFromRule(rule) {
  return {
    equipmentTypeId: rule.equipment_type.id,
    parameterId: rule.parameter.id,
    warningMin: rule.warning_min ?? '',
    warningMax: rule.warning_max ?? '',
    criticalMin: rule.critical_min ?? '',
    criticalMax: rule.critical_max ?? '',
    isActive: rule.is_active,
  }
}

function getThresholdSummary(rule) {
  const parts = [
    rule.critical_min ? `critical min ${rule.critical_min}` : null,
    rule.warning_min ? `warning min ${rule.warning_min}` : null,
    rule.warning_max ? `warning max ${rule.warning_max}` : null,
    rule.critical_max ? `critical max ${rule.critical_max}` : null,
  ].filter(Boolean)

  return parts.length ? parts.join(' / ') : 'Пороги не заданы'
}

export function ThresholdRulesPage() {
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canManageRules = hasPermission('threshold_rules.manage')
  const [equipmentTypeFilter, setEquipmentTypeFilter] = useState('')
  const [parameterFilter, setParameterFilter] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editRule, setEditRule] = useState(null)
  const [deleteRule, setDeleteRule] = useState(null)
  const [formState, setFormState] = useState(emptyRuleForm)
  const [feedback, setFeedback] = useState({ open: false, message: '', severity: 'success' })

  const rulesQuery = useQuery({
    queryKey: ['threshold-rules', equipmentTypeFilter, parameterFilter],
    queryFn: () =>
      fetchThresholdRules({
        ...(equipmentTypeFilter ? { equipment_type_id: equipmentTypeFilter } : {}),
        ...(parameterFilter ? { parameter_id: parameterFilter } : {}),
      }),
  })
  const equipmentTypesQuery = useQuery({
    queryKey: ['equipment-types'],
    queryFn: fetchEquipmentTypes,
  })
  const parametersQuery = useQuery({
    queryKey: ['parameters'],
    queryFn: fetchParameters,
  })
  const bindingsQuery = useQuery({
    queryKey: ['equipment-type-parameters', formState.equipmentTypeId],
    queryFn: () => fetchEquipmentTypeParameterBindings(formState.equipmentTypeId),
    enabled: Boolean(formState.equipmentTypeId),
  })

  const rules = rulesQuery.data ?? []
  const equipmentTypes = equipmentTypesQuery.data ?? []
  const parameters = parametersQuery.data ?? []
  const parameterOptions = formState.equipmentTypeId
    ? (bindingsQuery.data ?? []).map((binding) => binding.parameter)
    : parameters
  const activeRulesCount = rules.filter((rule) => rule.is_active).length
  const inactiveRulesCount = rules.length - activeRulesCount
  const isInitialLoading = rulesQuery.isLoading && rules.length === 0

  const createRuleMutation = useMutation({
    mutationFn: createThresholdRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threshold-rules'] })
      setCreateDialogOpen(false)
      setFormState(emptyRuleForm)
      setFeedback({
        open: true,
        message: 'Пороговое правило создано.',
        severity: 'success',
      })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message || 'Не удалось создать пороговое правило.',
        severity: 'error',
      })
    },
  })

  const updateRuleMutation = useMutation({
    mutationFn: ({ ruleId, payload }) => updateThresholdRule(ruleId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threshold-rules'] })
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
      setEditRule(null)
      setFormState(emptyRuleForm)
      setFeedback({
        open: true,
        message: 'Пороговое правило обновлено.',
        severity: 'success',
      })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message || 'Не удалось обновить пороговое правило.',
        severity: 'error',
      })
    },
  })

  const deleteRuleMutation = useMutation({
    mutationFn: deleteThresholdRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threshold-rules'] })
      setDeleteRule(null)
      setFeedback({
        open: true,
        message: 'Пороговое правило удалено.',
        severity: 'success',
      })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message || 'Не удалось удалить пороговое правило.',
        severity: 'error',
      })
    },
  })

  const effectiveIsSubmitting =
    createRuleMutation.isPending || updateRuleMutation.isPending || deleteRuleMutation.isPending

  function resetFilters() {
    setEquipmentTypeFilter('')
    setParameterFilter('')
  }

  function openCreateDialog() {
    setFormState(emptyRuleForm)
    setCreateDialogOpen(true)
  }

  function openEditDialog(rule) {
    setFormState(formFromRule(rule))
    setEditRule(rule)
  }

  function closeRuleDialog() {
    if (effectiveIsSubmitting) {
      return
    }
    setCreateDialogOpen(false)
    setEditRule(null)
    setFormState(emptyRuleForm)
  }

  function handleEquipmentTypeChange(value) {
    setFormState((current) => ({
      ...current,
      equipmentTypeId: value,
      parameterId: '',
    }))
  }

  function submitRule(event) {
    event.preventDefault()

    if (!formState.equipmentTypeId || !formState.parameterId) {
      setFeedback({
        open: true,
        message: 'Выберите тип оборудования и параметр.',
        severity: 'warning',
      })
      return
    }

    const payload = buildRulePayload(formState)
    if (editRule) {
      updateRuleMutation.mutate({ ruleId: editRule.id, payload })
      return
    }

    createRuleMutation.mutate(payload)
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Мониторинг"
        title="Пороговые правила"
        description="Настройка границ warning и critical, по которым система оценивает входящую телеметрию."
        actions={
          canManageRules ? (
            <Button onClick={openCreateDialog} startIcon={<AddRoundedIcon />} variant="contained">
              Новое правило
            </Button>
          ) : null
        }
      />

      {rulesQuery.isError ? (
        <Alert severity="error">
          Не удалось загрузить пороговые правила. {rulesQuery.error.message}
        </Alert>
      ) : null}
      {!canManageRules ? (
        <Alert severity="info">
          У текущего пользователя есть доступ к просмотру, но изменение скрыто без `threshold_rules.manage`.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
        }}
      >
        <StatCard label="Правил в выборке" value={formatNumber(rules.length)} />
        <StatCard accent="success.main" label="Активные" value={formatNumber(activeRulesCount)} />
        <StatCard accent="warning.main" label="Отключенные" value={formatNumber(inactiveRulesCount)} />
      </Box>

      <SectionCard
        title="Матрица порогов"
        subtitle="Каждая строка связывает тип оборудования, параметр и границы состояния."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Тип оборудования"
              onChange={(event) => setEquipmentTypeFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={equipmentTypeFilter}
            >
              <MenuItem value="">Все типы</MenuItem>
              {equipmentTypes.map((equipmentType) => (
                <MenuItem key={equipmentType.id} value={equipmentType.id}>
                  {equipmentType.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Параметр"
              onChange={(event) => setParameterFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 220 }}
              value={parameterFilter}
            >
              <MenuItem value="">Все параметры</MenuItem>
              {parameters.map((parameter) => (
                <MenuItem key={parameter.id} value={parameter.id}>
                  {parameter.name}
                </MenuItem>
              ))}
            </TextField>
            <Button onClick={resetFilters} startIcon={<RuleRoundedIcon />} variant="outlined">
              Сбросить
            </Button>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} height={74} variant="rounded" />
            ))}
          </Box>
        ) : rules.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 1080 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Тип оборудования</TableCell>
                  <TableCell>Параметр</TableCell>
                  <TableCell>Warning min/max</TableCell>
                  <TableCell>Critical min/max</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Обновлено</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.id}>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{rule.equipment_type.name}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{rule.parameter.name}</Typography>
                      <Typography color="text.secondary" sx={{ fontSize: 13 }}>
                        {rule.parameter.code} {rule.parameter.unit ? `• ${rule.parameter.unit}` : ''}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {formatNumber(rule.warning_min)} / {formatNumber(rule.warning_max)}
                    </TableCell>
                    <TableCell>
                      {formatNumber(rule.critical_min)} / {formatNumber(rule.critical_max)}
                    </TableCell>
                    <TableCell>
                      <StatusChip value={rule.is_active ? 'normal' : 'warning'} />
                    </TableCell>
                    <TableCell>{formatDateTime(rule.updated_at)}</TableCell>
                    <TableCell align="right">
                      <Tooltip title={getThresholdSummary(rule)}>
                        <span>
                          <IconButton disabled={!canManageRules} onClick={() => openEditDialog(rule)}>
                            <EditRoundedIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="Пороговые правила не найдены"
            description="Создайте правило для связки типа оборудования и параметра, чтобы телеметрия могла оцениваться."
            actionLabel={canManageRules ? 'Создать правило' : undefined}
            onAction={canManageRules ? openCreateDialog : undefined}
          />
        )}
      </SectionCard>

      <Dialog
        fullWidth
        maxWidth="md"
        onClose={closeRuleDialog}
        open={createDialogOpen || Boolean(editRule)}
      >
        <Box component="form" onSubmit={submitRule}>
          <DialogTitle>{editRule ? 'Редактировать пороговое правило' : 'Создать пороговое правило'}</DialogTitle>
          <DialogContent sx={{ display: 'grid', gap: 2.5, pt: '10px !important' }}>
            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' },
              }}
            >
              <TextField
                disabled={Boolean(editRule)}
                label="Тип оборудования"
                onChange={(event) => handleEquipmentTypeChange(event.target.value)}
                required
                select
                value={formState.equipmentTypeId}
              >
                {equipmentTypes.map((equipmentType) => (
                  <MenuItem key={equipmentType.id} value={equipmentType.id}>
                    {equipmentType.name}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                disabled={!formState.equipmentTypeId || Boolean(editRule)}
                helperText={
                  formState.equipmentTypeId
                    ? 'Показываются параметры, привязанные к выбранному типу.'
                    : 'Сначала выберите тип оборудования.'
                }
                label="Параметр"
                onChange={(event) =>
                  setFormState((current) => ({
                    ...current,
                    parameterId: event.target.value,
                  }))
                }
                required
                select
                value={formState.parameterId}
              >
                {parameterOptions.map((parameter) => (
                  <MenuItem key={parameter.id} value={parameter.id}>
                    {parameter.name} {parameter.unit ? `(${parameter.unit})` : ''}
                  </MenuItem>
                ))}
              </TextField>
            </Box>

            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns: { xs: '1fr', md: 'repeat(4, minmax(0, 1fr))' },
              }}
            >
              <TextField
                inputProps={{ step: '0.0001' }}
                label="Warning min"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, warningMin: event.target.value }))
                }
                type="number"
                value={formState.warningMin}
              />
              <TextField
                inputProps={{ step: '0.0001' }}
                label="Warning max"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, warningMax: event.target.value }))
                }
                type="number"
                value={formState.warningMax}
              />
              <TextField
                inputProps={{ step: '0.0001' }}
                label="Critical min"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, criticalMin: event.target.value }))
                }
                type="number"
                value={formState.criticalMin}
              />
              <TextField
                inputProps={{ step: '0.0001' }}
                label="Critical max"
                onChange={(event) =>
                  setFormState((current) => ({ ...current, criticalMax: event.target.value }))
                }
                type="number"
                value={formState.criticalMax}
              />
            </Box>
            <FormControlLabel
              control={
                <Switch
                  checked={formState.isActive}
                  onChange={(event) =>
                    setFormState((current) => ({ ...current, isActive: event.target.checked }))
                  }
                />
              }
              label="Правило активно"
            />
            <Alert severity="info">
              Должно быть задано хотя бы одно пороговое значение. Для верхнего порога обычно используют
              `warning_max` и `critical_max`, для нижнего - `warning_min` и `critical_min`.
            </Alert>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            {editRule ? (
              <Button
                color="error"
                disabled={effectiveIsSubmitting}
                onClick={() => setDeleteRule(editRule)}
              >
                Удалить
              </Button>
            ) : null}
            <Box sx={{ flex: 1 }} />
            <Button disabled={effectiveIsSubmitting} onClick={closeRuleDialog}>
              Отмена
            </Button>
            <Button disabled={effectiveIsSubmitting} type="submit" variant="contained">
              {editRule ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <ConfirmDialog
        confirmColor="error"
        confirmLabel="Удалить"
        description={
          deleteRule
            ? `Удалить правило для "${deleteRule.equipment_type.name}" / "${deleteRule.parameter.name}"?`
            : ''
        }
        isSubmitting={deleteRuleMutation.isPending}
        onCancel={() => setDeleteRule(null)}
        onConfirm={() => deleteRuleMutation.mutate(deleteRule.id)}
        open={Boolean(deleteRule)}
        title="Удалить пороговое правило"
      />

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
