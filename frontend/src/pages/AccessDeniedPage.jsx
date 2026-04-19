import { Box, Button, Stack } from '@mui/material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { EmptyState } from '../components/EmptyState'
import { navigationItems } from '../layout/navigation'

export function AccessDeniedPage() {
  const navigate = useNavigate()
  const { hasAnyPermission, logout, user } = useAuth()

  const visibleTargets = navigationItems.filter((item) =>
    hasAnyPermission(item.requiredPermissions),
  )

  return (
    <Box sx={{ display: 'grid', gap: 3, width: '100%' }}>
      <EmptyState
        title="Недостаточно прав доступа"
        description="У текущего пользователя нет прав для этого раздела. Откройте доступный модуль или войдите под другой ролью."
      />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ flexWrap: 'wrap' }}>
        {visibleTargets.map((item) => (
          <Button component={RouterLink} key={item.href} to={item.href} variant="outlined">
            {item.label}
          </Button>
        ))}
        {!visibleTargets.length && user ? (
          <Button
            onClick={() => {
              logout()
              navigate('/login', { replace: true })
            }}
            variant="outlined"
          >
            Сменить пользователя
          </Button>
        ) : null}
      </Stack>
    </Box>
  )
}
