import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded'
import FilterAltOffRoundedIcon from '@mui/icons-material/FilterAltOffRounded'
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
import { useDeferredValue, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchEquipmentList } from '../api/equipment'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { StatCard } from '../components/StatCard'
import { StatusChip } from '../components/StatusChip'
import { formatDateTime, formatNumber } from '../utils/format'

export function EquipmentListPage() {
  const navigate = useNavigate()
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const deferredSearchValue = useDeferredValue(searchValue)

  const equipmentQuery = useQuery({
    queryKey: ['equipment', 'list'],
    queryFn: fetchEquipmentList,
  })

  const equipment = equipmentQuery.data ?? []
  const normalizedSearch = deferredSearchValue.trim().toLowerCase()
  const filteredEquipment = equipment.filter((item) => {
    const matchesStatus =
      statusFilter === 'all' ? true : item.monitoringStatus === statusFilter
    const searchTarget = [
      item.name,
      item.code,
      item.location,
      item.equipment_type.name,
      item.serial_number,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    const matchesSearch =
      normalizedSearch.length === 0 ? true : searchTarget.includes(normalizedSearch)

    return matchesStatus && matchesSearch
  })
  const isInitialLoading = equipmentQuery.isLoading && equipment.length === 0
  const activeCount = filteredEquipment.filter((item) => item.is_active).length
  const warningCount = filteredEquipment.filter((item) => item.monitoringStatus === 'warning').length
  const criticalCount = filteredEquipment.filter((item) => item.monitoringStatus === 'critical').length

  function resetFilters() {
    setSearchValue('')
    setStatusFilter('all')
  }

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <PageHeader
        eyebrow="Реестр активов"
        title="Список оборудования"
        description="Таблица парка с мониторинговым контекстом для навигации и оценки текущего состояния."
        actions={
          <Button onClick={resetFilters} startIcon={<FilterAltOffRoundedIcon />} variant="outlined">
            Сбросить фильтры
          </Button>
        }
      />

      {equipmentQuery.isError ? (
        <Alert severity="warning">
          Не удалось загрузить список оборудования. Проверьте доступ к API или попробуйте обновить страницу.
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            md: 'repeat(2, minmax(0, 1fr))',
            xl: 'repeat(4, minmax(0, 1fr))',
          },
        }}
      >
        <StatCard label="Единиц парка" value={formatNumber(equipment.length)} />
        <StatCard accent="success.main" label="Активные единицы" value={formatNumber(activeCount)} />
        <StatCard accent="warning.main" label="Предупреждения" value={formatNumber(warningCount)} />
        <StatCard accent="error.main" label="Критические единицы" value={formatNumber(criticalCount)} />
      </Box>

      <SectionCard
        title="Каталог парка"
        subtitle="Выберите единицу, чтобы открыть детальную карточку оборудования."
        action={
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <TextField
              label="Поиск"
              onChange={(event) => setSearchValue(event.target.value)}
              placeholder="Название, код, локация"
              size="small"
              value={searchValue}
            />
            <TextField
              label="Статус"
              onChange={(event) => setStatusFilter(event.target.value)}
              select
              size="small"
              sx={{ minWidth: 180 }}
              value={statusFilter}
            >
              <MenuItem value="all">Все статусы</MenuItem>
              <MenuItem value="normal">Норма</MenuItem>
              <MenuItem value="warning">Предупреждение</MenuItem>
              <MenuItem value="critical">Критично</MenuItem>
              <MenuItem value="unknown">Неизвестно</MenuItem>
            </TextField>
          </Box>
        }
      >
        {isInitialLoading ? (
          <Box sx={{ display: 'grid', gap: 1.5 }}>
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} height={68} variant="rounded" />
            ))}
          </Box>
        ) : filteredEquipment.length ? (
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 860 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Оборудование</TableCell>
                  <TableCell>Тип</TableCell>
                  <TableCell>Локация</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Сигналы</TableCell>
                  <TableCell>Последняя оценка</TableCell>
                  <TableCell align="right">Открыть</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredEquipment.map((item) => (
                  <TableRow
                    hover
                    key={item.id}
                    onClick={() => navigate(`/equipment/${item.id}`)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>
                      <Typography sx={{ fontWeight: 800 }}>{item.name}</Typography>
                      <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                        {item.code} • {item.serial_number || 'Серийный номер не указан'}
                      </Typography>
                    </TableCell>
                    <TableCell>{item.equipment_type.name}</TableCell>
                    <TableCell>{item.location}</TableCell>
                    <TableCell>
                      <StatusChip value={item.monitoringStatus} />
                    </TableCell>
                    <TableCell>
                      <Typography sx={{ fontWeight: 700 }}>
                        {item.warningCount} предупреждений / {item.criticalCount} критических
                      </Typography>
                    </TableCell>
                    <TableCell>{formatDateTime(item.lastEvaluatedAt)}</TableCell>
                    <TableCell align="right">
                      <Button endIcon={<ArrowForwardRoundedIcon />} size="small">
                        Детали
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ) : (
          <EmptyState
            title="Оборудование не найдено"
            description="Попробуйте изменить поисковую строку или снять фильтр по статусу."
            actionLabel="Сбросить фильтры"
            onAction={resetFilters}
          />
        )}
      </SectionCard>
    </Box>
  )
}
