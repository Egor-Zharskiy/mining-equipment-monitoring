import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import {
  Alert,
  Box,
  Button,
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
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link as RouterLink, useParams } from 'react-router-dom'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { fetchTelemetryHistory } from '../api/dashboard'
import { demoEquipmentList, findDemoEquipmentDetails } from '../api/demoData'
import { fetchEquipmentDetails, fetchEquipmentTypeParameterBindings } from '../api/equipment'
import { createTelemetryReading } from '../api/telemetry'
import { useAuth } from '../auth/useAuth'
import { DataFallbackNotice } from '../components/DataFallbackNotice'
import { EmptyState } from '../components/EmptyState'
import { LoadingScreen } from '../components/LoadingScreen'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import {
  formatDateTime,
  formatNumber,
  formatShortDate,
  formatSpecificationLabel,
} from '../utils/format'

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

function buildParameterOptions(parameterStates, bindings) {
  const options = new Map()

  parameterStates.forEach((state) => {
    options.set(state.parameter.id, {
      id: state.parameter.id,
      name: state.parameter.name,
      unit: state.parameter.unit,
      code: state.parameter.code,
      status: state.status,
      value: state.value,
    })
  })

  bindings.forEach((binding) => {
    if (!options.has(binding.parameter.id)) {
      options.set(binding.parameter.id, {
        id: binding.parameter.id,
        name: binding.parameter.name,
        unit: binding.parameter.unit,
        code: binding.parameter.code,
        status: null,
        value: null,
      })
    }
  })

  return Array.from(options.values())
}

export function EquipmentDetailsPage() {
  const { equipmentId = '' } = useParams()
  const queryClient = useQueryClient()
  const { hasPermission } = useAuth()
  const canCreateTelemetry = hasPermission('telemetry.create')
  const demoData = findDemoEquipmentDetails(equipmentId)
  const [selectedParameterId, setSelectedParameterId] = useState('')
  const [telemetryForm, setTelemetryForm] = useState({
    parameterId: '',
    value: '',
    measuredAt: toDateTimeLocalValue(new Date().toISOString()),
  })
  const [feedback, setFeedback] = useState({ open: false, message: '', severity: 'success' })

  const equipmentQuery = useQuery({
    queryKey: ['equipment', 'details', equipmentId],
    queryFn: () => fetchEquipmentDetails(equipmentId),
    enabled: Boolean(equipmentId),
  })

  const equipment = equipmentQuery.data ?? demoData
  const usingFallback = equipmentQuery.isError && Boolean(demoData)
  const monitoringState = equipment
    ? (equipment.monitoringState ?? {
        status: equipment.monitoringStatus ?? 'unknown',
        warning_count: equipment.warningCount ?? 0,
        critical_count: equipment.criticalCount ?? 0,
        last_evaluated_at: equipment.lastEvaluatedAt ?? null,
        parameter_states: [],
      })
    : null
  const parameterStates = monitoringState?.parameter_states ?? []
  const specifications = Object.entries(equipment?.specifications ?? {})
  const resolvedSelectedParameterId = parameterStates.some(
    (item) => item.parameter.id === selectedParameterId,
  )
    ? selectedParameterId
    : (parameterStates[0]?.parameter.id ?? '')
  const selectedParameter =
    parameterStates.find((item) => item.parameter.id === resolvedSelectedParameterId) ?? null

  const parameterBindingsQuery = useQuery({
    queryKey: ['equipment-type-parameters', equipment?.equipment_type?.id],
    queryFn: () => fetchEquipmentTypeParameterBindings(equipment.equipment_type.id),
    enabled: Boolean(equipment?.equipment_type?.id && !usingFallback),
  })
  const telemetryParameterOptions = buildParameterOptions(
    parameterStates,
    parameterBindingsQuery.data ?? [],
  )
  const resolvedTelemetryParameterId = telemetryParameterOptions.some(
    (item) => item.id === telemetryForm.parameterId,
  )
    ? telemetryForm.parameterId
    : (telemetryParameterOptions[0]?.id ?? '')
  const telemetryParameter = telemetryParameterOptions.find(
    (item) => item.id === resolvedTelemetryParameterId,
  )

  const telemetryHistoryQuery = useQuery({
    queryKey: ['equipment', 'telemetry-history', equipment?.id, selectedParameter?.parameter.id],
    queryFn: () =>
      fetchTelemetryHistory({
        equipmentId: equipment.id,
        parameterId: selectedParameter.parameter.id,
        limit: 50,
      }),
    enabled: Boolean(equipment?.id && selectedParameter?.parameter.id),
  })

  const telemetryChartData = (telemetryHistoryQuery.data?.points ?? []).map((point) => ({
    measuredAt: point.measured_at,
    value: Number(point.value),
  }))

  const telemetryMutation = useMutation({
    mutationFn: createTelemetryReading,
    onSuccess: (reading) => {
      setFeedback({
        open: true,
        message: `Телеметрия принята. Статус оценки: ${reading.evaluation?.status ?? 'нет оценки'}.`,
        severity: 'success',
      })
      setTelemetryForm((current) => ({
        ...current,
        value: '',
        measuredAt: toDateTimeLocalValue(new Date().toISOString()),
      }))
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
      queryClient.invalidateQueries({ queryKey: ['events'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
    onError: (error) => {
      setFeedback({
        open: true,
        message: error.message || 'Не удалось отправить телеметрию.',
        severity: 'error',
      })
    },
  })

  function submitTelemetry(event) {
    event.preventDefault()

    if (!equipment?.id || !resolvedTelemetryParameterId || !telemetryForm.value.trim()) {
      setFeedback({
        open: true,
        message: 'Выберите параметр и укажите значение телеметрии.',
        severity: 'warning',
      })
      return
    }

    telemetryMutation.mutate({
      equipment_id: equipment.id,
      parameter_id: resolvedTelemetryParameterId,
      value: telemetryForm.value.trim(),
      measured_at: toApiDateTime(telemetryForm.measuredAt),
    })
  }

  if (equipmentQuery.isLoading && !equipment) {
    return <LoadingScreen label="Загрузка карточки оборудования" />
  }

  if (!equipment || !monitoringState) {
    return (
      <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
        <PageHeader
          eyebrow="Оборудование"
          title="Карточка оборудования"
          description="Для этого маршрута нет доступных данных по оборудованию."
          actions={
            <Button component={RouterLink} startIcon={<ArrowBackRoundedIcon />} to="/equipment">
              Назад к списку
            </Button>
          }
        />
        <SectionCard
          title="Оборудование не найдено"
          subtitle="Сначала откройте одну из доступных единиц из списка."
        >
          <Typography color="text.secondary">
            Доступные карточки оборудования:{' '}
            {demoEquipmentList.slice(0, 2).map((item) => item.code).join(', ')}.
          </Typography>
        </SectionCard>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow={equipment.equipment_type.name}
        title={equipment.name}
        description={`${equipment.code} • ${equipment.location}`}
        actions={
          <Button component={RouterLink} startIcon={<ArrowBackRoundedIcon />} to="/equipment">
            Назад к оборудованию
          </Button>
        }
      />

      {usingFallback ? <DataFallbackNotice /> : null}
      {!usingFallback && equipmentQuery.isError ? (
        <Alert severity="warning">
          Не удалось загрузить карточку оборудования из API. Проверьте, существует ли запись и есть ли права доступа.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            md: 'repeat(3, minmax(0, 1fr))',
          },
        }}
      >
        <StatCard
          accent={
            monitoringState.status === 'critical'
              ? 'error.main'
              : monitoringState.status === 'warning'
                ? 'warning.main'
                : 'success.main'
          }
          label="Текущее состояние"
          value={<StatusChip value={monitoringState.status} size="medium" />}
        />
        <StatCard
          accent="warning.main"
          label="Метрики с предупреждением"
          value={formatNumber(monitoringState.warning_count)}
        />
        <StatCard
          accent="error.main"
          label="Критические метрики"
          value={formatNumber(monitoringState.critical_count)}
        />
      </Box>

      <Box
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', xl: '0.8fr 1.2fr' },
        }}
      >
        <SectionCard
          title="Профиль актива"
          subtitle="Статическая информация об оборудовании из реестра."
        >
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            <Typography><strong>Серийный номер:</strong> {equipment.serial_number || 'Не указан'}</Typography>
            <Typography><strong>Тип:</strong> {equipment.equipment_type.name}</Typography>
            <Typography><strong>Локация:</strong> {equipment.location}</Typography>
            <Typography><strong>Последнее обновление:</strong> {formatDateTime(equipment.updated_at)}</Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              {equipment.description || 'Описание для этой единицы пока не заполнено.'}
            </Typography>
          </Box>
        </SectionCard>

        <SectionCard
          title="Текущий снимок параметров"
          subtitle={`Последняя оценка: ${formatDateTime(monitoringState.last_evaluated_at)}.`}
        >
          {parameterStates.length ? (
            <Box sx={{ overflowX: 'auto' }}>
              <Table sx={{ minWidth: 640 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Параметр</TableCell>
                    <TableCell>Значение</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Измерено</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parameterStates.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Typography sx={{ fontWeight: 800 }}>{item.parameter.name}</Typography>
                        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                          {item.parameter.code}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {formatNumber(item.value)} {item.parameter.unit || ''}
                      </TableCell>
                      <TableCell>
                        <StatusChip value={item.status} />
                      </TableCell>
                      <TableCell>{formatDateTime(item.measured_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          ) : (
            <EmptyState
              title="Параметры пока не оценены"
              description="Для этой единицы еще не поступило достаточно телеметрии, чтобы сформировать актуальный снимок параметров."
            />
          )}
        </SectionCard>
      </Box>

      <SectionCard
        title="Демо-ввод телеметрии"
        subtitle="Отправьте новое измерение, чтобы сразу пересчитать состояние, создать событие и запустить уведомления."
      >
        {!canCreateTelemetry ? (
          <Alert severity="info">
            У текущего пользователя нет права `telemetry.create`, поэтому отправка телеметрии скрыта.
          </Alert>
        ) : usingFallback ? (
          <Alert severity="warning">
            Карточка открыта на резервных demo-данных. Отправка телеметрии доступна только для реальной записи из API.
          </Alert>
        ) : !telemetryParameterOptions.length ? (
          <EmptyState
            title="Нет доступных параметров"
            description="Для типа оборудования не найдены параметры мониторинга. Сначала настройте привязки параметров."
          />
        ) : (
          <Box component="form" onSubmit={submitTelemetry}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField
                label="Параметр"
                onChange={(event) =>
                  setTelemetryForm((current) => ({
                    ...current,
                    parameterId: event.target.value,
                  }))
                }
                select
                size="small"
                sx={{ minWidth: { md: 280 } }}
                value={resolvedTelemetryParameterId}
              >
                {telemetryParameterOptions.map((option) => (
                  <MenuItem key={option.id} value={option.id}>
                    {option.name} {option.status ? `• ${option.status}` : ''}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                helperText={telemetryParameter?.unit ? `Единица: ${telemetryParameter.unit}` : 'Числовое значение'}
                inputProps={{ step: '0.0001' }}
                label="Значение"
                onChange={(event) =>
                  setTelemetryForm((current) => ({
                    ...current,
                    value: event.target.value,
                  }))
                }
                placeholder="например 95.0000"
                size="small"
                type="number"
                value={telemetryForm.value}
              />
              <TextField
                label="Время измерения"
                onChange={(event) =>
                  setTelemetryForm((current) => ({
                    ...current,
                    measuredAt: event.target.value,
                  }))
                }
                size="small"
                type="datetime-local"
                value={telemetryForm.measuredAt}
              />
              <Button
                disabled={telemetryMutation.isPending}
                sx={{ minWidth: 180 }}
                type="submit"
                variant="contained"
              >
                {telemetryMutation.isPending ? 'Отправка...' : 'Отправить'}
              </Button>
            </Stack>
            <Typography color="text.secondary" sx={{ mt: 1.5 }}>
              Текущий выбранный параметр: {telemetryParameter?.name || 'не выбран'}.
              {telemetryParameter?.value !== null && telemetryParameter?.value !== undefined
                ? ` Последнее значение: ${formatNumber(telemetryParameter.value)} ${telemetryParameter.unit || ''}.`
                : ' Последнее значение еще не сформировано.'}
            </Typography>
          </Box>
        )}
      </SectionCard>

      <SectionCard
        title="История параметра"
        subtitle="Мини-график по выбранному параметру из analytics telemetry history."
        action={
          parameterStates.length ? (
            <TextField
              label="Параметр"
              onChange={(event) => setSelectedParameterId(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 240 }}
              value={resolvedSelectedParameterId}
            >
              {parameterStates.map((item) => (
                <MenuItem key={item.id} value={item.parameter.id}>
                  {item.parameter.name}
                </MenuItem>
              ))}
            </TextField>
          ) : null
        }
      >
        {!parameterStates.length ? (
          <EmptyState
            title="История пока недоступна"
            description="Для этой единицы еще нет оцененных параметров с доступной телеметрией."
          />
        ) : telemetryHistoryQuery.isLoading ? (
          <Skeleton height={280} variant="rounded" />
        ) : telemetryChartData.length ? (
          <Box sx={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetryChartData}>
                <defs>
                  <linearGradient id="telemetryGradient" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#cb7a33" stopOpacity={0.36} />
                    <stop offset="100%" stopColor="#cb7a33" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#d7dfdc" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  axisLine={false}
                  dataKey="measuredAt"
                  tickFormatter={formatShortDate}
                  tickLine={false}
                />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(value) => [
                    `${formatNumber(value)} ${selectedParameter?.parameter.unit || ''}`.trim(),
                    selectedParameter?.parameter.name || 'Параметр',
                  ]}
                  labelFormatter={(label) => formatDateTime(label)}
                />
                <Area
                  dataKey="value"
                  fill="url(#telemetryGradient)"
                  stroke="#cb7a33"
                  strokeWidth={3}
                  type="monotone"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        ) : (
          <EmptyState
            title="История измерений отсутствует"
            description="API вернул пустой набор точек для выбранного параметра. Это нормально для новых или редко измеряемых метрик."
          />
        )}
      </SectionCard>

      <SectionCard
        title="Статические характеристики"
        subtitle="Технические свойства намеренно отделены от динамической телеметрии."
      >
        {specifications.length ? (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
            }}
          >
            {specifications.map(([key, value]) => (
              <Box
                key={key}
                sx={{
                  backgroundColor: 'background.default',
                  borderRadius: 3,
                  p: 2,
                }}
              >
                <Typography color="text.secondary" sx={{ fontSize: 13, mb: 0.75 }}>
                  {formatSpecificationLabel(key)}
                </Typography>
                <Typography sx={{ fontSize: 24, fontWeight: 800 }}>{String(value)}</Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography color="text.secondary">
            Для этой единицы статические характеристики пока не добавлены.
          </Typography>
        )}
      </SectionCard>

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
