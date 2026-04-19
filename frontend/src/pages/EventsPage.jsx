import FilterListRoundedIcon from '@mui/icons-material/FilterListRounded'
import {
  Alert,
  Box,
  Button,
  MenuItem,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { demoEquipmentList, demoEvents } from '../api/demoData'
import { fetchEquipmentList } from '../api/equipment'
import { fetchEvents } from '../api/events'
import { DataFallbackNotice } from '../components/DataFallbackNotice'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatEventType, formatNumber } from '../utils/format'

export function EventsPage() {
  const [searchParams] = useSearchParams()
  const searchQuery = searchParams.get('q') ?? ''
  const [severityFilter, setSeverityFilter] = useState('')
  const [eventTypeFilter, setEventTypeFilter] = useState('')
  const [equipmentIdFilter, setEquipmentIdFilter] = useState('')
  const [searchFilter, setSearchFilter] = useState(searchQuery)
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

  const usingFallback = eventsQuery.isError
  const baseEvents = usingFallback ? demoEvents : (eventsQuery.data ?? [])
  const equipmentOptions = equipmentQuery.isError ? demoEquipmentList : (equipmentQuery.data ?? [])
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
  const isInitialLoading = !usingFallback && eventsQuery.isLoading && baseEvents.length === 0
  const criticalCount = events.filter((item) => item.severity === 'critical').length
  const warningCount = events.filter((item) => item.severity === 'warning').length
  const eventTypeOptions = Array.from(new Set(baseEvents.map((item) => item.event_type))).sort()

  function resetFilters() {
    setSeverityFilter('')
    setEventTypeFilter('')
    setEquipmentIdFilter('')
    setSearchFilter('')
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

      {usingFallback ? <DataFallbackNotice /> : null}
      {!usingFallback && eventsQuery.isError ? (
        <Alert severity="warning">
          Не удалось получить события из API. Показан резервный набор данных.
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
            <Table sx={{ minWidth: 920 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Событие</TableCell>
                  <TableCell>Оборудование</TableCell>
                  <TableCell>Тип</TableCell>
                  <TableCell>Критичность</TableCell>
                  <TableCell>Создано</TableCell>
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
    </Box>
  )
}
