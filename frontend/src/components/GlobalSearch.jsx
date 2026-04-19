import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import {
  Autocomplete,
  Box,
  CircularProgress,
  InputAdornment,
  TextField,
  Typography,
} from '@mui/material'
import { useDeferredValue, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchGlobalSearch } from '../api/search'

const groupLabels = {
  equipment: 'Оборудование',
  event: 'События',
  maintenance_task: 'Задачи ТО',
  user: 'Пользователи',
}

function buildSearchHref(option, query) {
  const encodedQuery = encodeURIComponent(query)

  if (option.entity_type === 'equipment') {
    return `/equipment/${option.id}`
  }
  if (option.entity_type === 'event') {
    return `/events?q=${encodedQuery}&focus=${option.id}`
  }
  if (option.entity_type === 'maintenance_task') {
    return `/maintenance?q=${encodedQuery}&focus=${option.id}`
  }
  if (option.entity_type === 'user') {
    return `/admin/users?q=${encodedQuery}&focus=${option.id}`
  }

  return '/'
}

export function GlobalSearch() {
  const navigate = useNavigate()
  const [inputValue, setInputValue] = useState('')
  const deferredQuery = useDeferredValue(inputValue.trim())

  const searchQuery = useQuery({
    queryKey: ['global-search', deferredQuery],
    queryFn: () => fetchGlobalSearch({ q: deferredQuery }),
    enabled: deferredQuery.length >= 2,
    staleTime: 30_000,
  })

  const options = useMemo(() => {
    if (!searchQuery.data) {
      return []
    }

    return [
      ...searchQuery.data.equipment.map((item) => ({
        ...item,
        group: groupLabels.equipment,
        href: buildSearchHref(item, deferredQuery),
      })),
      ...searchQuery.data.events.map((item) => ({
        ...item,
        group: groupLabels.event,
        href: buildSearchHref(item, deferredQuery),
      })),
      ...searchQuery.data.maintenance_tasks.map((item) => ({
        ...item,
        group: groupLabels.maintenance_task,
        href: buildSearchHref(item, deferredQuery),
      })),
      ...searchQuery.data.users.map((item) => ({
        ...item,
        group: groupLabels.user,
        href: buildSearchHref(item, deferredQuery),
      })),
    ]
  }, [deferredQuery, searchQuery.data])
  const shouldOpen =
    deferredQuery.length >= 2 &&
    (searchQuery.isFetching || searchQuery.isError || options.length > 0)

  return (
    <Autocomplete
      filterOptions={(items) => items}
      fullWidth
      getOptionLabel={(option) => option.title}
      groupBy={(option) => option.group}
      inputValue={inputValue}
      isOptionEqualToValue={(option, value) =>
        option.entity_type === value.entity_type && option.id === value.id
      }
      loading={searchQuery.isFetching}
      noOptionsText={
        searchQuery.isError
          ? 'Не удалось выполнить поиск'
          : deferredQuery.length < 2
          ? ''
          : 'Ничего не найдено'
      }
      onChange={(_, option) => {
        if (!option) {
          return
        }

        navigate(option.href)
        setInputValue('')
      }}
      onInputChange={(_, value, reason) => {
        if (reason === 'clear' || reason === 'input') {
          setInputValue(value)
        }
      }}
      open={shouldOpen}
      options={options}
      value={null}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Поиск по системе"
          size="small"
          sx={{ minWidth: { sm: 300 } }}
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <>
                <InputAdornment position="start">
                  <SearchRoundedIcon fontSize="small" />
                </InputAdornment>
                {params.InputProps.startAdornment}
              </>
            ),
            endAdornment: (
              <>
                {searchQuery.isFetching ? <CircularProgress color="inherit" size={16} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      renderOption={(props, option) => (
        <Box component="li" {...props} sx={{ display: 'grid', gap: 0.25 }}>
          <Typography sx={{ fontWeight: 700 }}>{option.title}</Typography>
          {option.subtitle ? (
            <Typography color="text.secondary" sx={{ fontSize: 13 }}>
              {option.subtitle}
            </Typography>
          ) : null}
          {option.description ? (
            <Typography color="text.secondary" sx={{ fontSize: 12 }}>
              {option.description}
            </Typography>
          ) : null}
        </Box>
      )}
    />
  )
}
