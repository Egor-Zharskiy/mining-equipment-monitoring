import BoltRoundedIcon from '@mui/icons-material/BoltRounded'
import EngineeringRoundedIcon from '@mui/icons-material/EngineeringRounded'
import InsightsRoundedIcon from '@mui/icons-material/InsightsRounded'
import SecurityRoundedIcon from '@mui/icons-material/SecurityRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { alpha } from '@mui/material/styles'
import { useMutation } from '@tanstack/react-query'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { getDefaultAuthorizedPath } from '../auth/permissions'
import { LoadingScreen } from '../components/LoadingScreen'
import { useAuth } from '../auth/useAuth'

const featureNotes = [
  {
    icon: SecurityRoundedIcon,
    title: 'Защищенные маршруты',
    description: 'JWT-сессия, сброс при неавторизованном ответе и закрытая навигация по системе.',
  },
  {
    icon: InsightsRoundedIcon,
    title: 'Аналитика',
    description: 'Панели мониторинга, показатели и графики для ежедневного контроля состояния парка.',
  },
  {
    icon: EngineeringRoundedIcon,
    title: 'Операционный UI',
    description: 'Рабочий интерфейс для оборудования, событий, задач ТО и административных операций.',
  },
  {
    icon: InsightsRoundedIcon,
    title: 'Ролевой доступ',
    description: 'Доступ к разделам и действиям зависит от роли и назначенных прав пользователя.',
  },
]

export function LoginPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, isInitializing, login } = useAuth()
  const redirectTo = location.state?.from?.pathname || '/'

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      navigate(location.state?.from?.pathname || getDefaultAuthorizedPath(user), { replace: true })
    },
  })

  function handleSubmit(event) {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)

    loginMutation.mutate({
      email: String(formData.get('email') ?? ''),
      password: String(formData.get('password') ?? ''),
    })
  }

  if (isInitializing) {
    return <LoadingScreen label="Восстановление сессии" />
  }

  if (isAuthenticated) {
    return <Navigate replace to={redirectTo} />
  }

  return (
    <Box
      sx={{
        alignItems: 'stretch',
        background:
          'radial-gradient(circle at top left, rgba(29,117,101,0.22), transparent 34%), radial-gradient(circle at bottom right, rgba(203,122,51,0.18), transparent 30%), linear-gradient(180deg, #eff4f1 0%, #e7eeeb 100%)',
        display: 'grid',
        gap: 3,
        gridTemplateColumns: { xs: '1fr', lg: '1.2fr 0.8fr' },
        minHeight: '100vh',
        p: { xs: 2, md: 3 },
      }}
    >
      <Paper
        sx={{
          border: '1px solid',
          borderColor: 'divider',
          overflow: 'hidden',
          p: { xs: 3, md: 5 },
          position: 'relative',
        }}
      >
        <Box
          sx={{
            background: 'linear-gradient(135deg, rgba(29,117,101,0.12), rgba(203,122,51,0.06))',
            borderRadius: '50%',
            height: 320,
            position: 'absolute',
            right: -90,
            top: -120,
            width: 320,
          }}
        />

        <Stack spacing={3} sx={{ maxWidth: 560, position: 'relative' }}>
          <Stack direction="row" spacing={1.25} sx={{ alignItems: 'center' }}>
            <Box
              sx={{
                alignItems: 'center',
                backgroundColor: 'primary.main',
                borderRadius: 3,
                color: 'primary.contrastText',
                display: 'inline-flex',
                height: 48,
                justifyContent: 'center',
                width: 48,
              }}
            >
              <BoltRoundedIcon />
            </Box>
            <Box>
              <Typography sx={{ fontSize: 26, fontWeight: 800 }}>
                Мониторинг горного оборудования
              </Typography>
              <Typography color="text.secondary">
                Единое рабочее пространство для контроля состояния парка.
              </Typography>
            </Box>
          </Stack>

          <Box>
            <Typography variant="h1" sx={{ fontSize: { xs: '2.6rem', md: '4.2rem' }, mb: 2 }}>
              Операционный обзор для горного парка.
            </Typography>
            <Typography color="text.secondary" sx={{ fontSize: 18, maxWidth: 520 }}>
              Интерфейс объединяет защищенные модули, ролевой доступ и связанный рабочий маршрут по системе
              без перегрузки архитектуры.
            </Typography>
          </Box>

          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
            <Chip label="Vite + React" color="primary" />
            <Chip label="React Router" variant="outlined" />
            <Chip label="TanStack Query" variant="outlined" />
            <Chip label="MUI + Recharts" variant="outlined" />
          </Stack>

          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
              mt: 2,
            }}
          >
            {featureNotes.map((item) => {
              const Icon = item.icon

              return (
                <Paper
                  key={item.title}
                  sx={{
                    backgroundColor: alpha('#ffffff', 0.72),
                    border: '1px solid',
                    borderColor: 'divider',
                    p: 2.5,
                  }}
                >
                  <Box
                    sx={{
                      alignItems: 'center',
                      backgroundColor: 'primary.main',
                      borderRadius: 3,
                      color: 'primary.contrastText',
                      display: 'inline-flex',
                      height: 42,
                      justifyContent: 'center',
                      mb: 1.5,
                      width: 42,
                    }}
                  >
                    <Icon fontSize="small" />
                  </Box>
                  <Typography sx={{ fontWeight: 800, mb: 1 }}>{item.title}</Typography>
                  <Typography color="text.secondary">{item.description}</Typography>
                </Paper>
              )
            })}
          </Box>
        </Stack>
      </Paper>

      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          alignSelf: 'center',
          border: '1px solid',
          borderColor: 'divider',
          p: { xs: 3, md: 4 },
        }}
      >
        <Stack spacing={2.5}>
          <Box>
            <Typography sx={{ color: 'primary.main', fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              Вход
            </Typography>
            <Typography variant="h3" sx={{ mt: 1 }}>
              Войдите в защищенное рабочее пространство
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Используйте корпоративную учетную запись для доступа к системе мониторинга.
            </Typography>
          </Box>

          {loginMutation.isError ? (
            <Alert severity="error">{loginMutation.error.message}</Alert>
          ) : null}

          <TextField
            autoComplete="email"
            autoFocus
            fullWidth
            label="Электронная почта"
            name="email"
            placeholder="operator@example.com"
            type="email"
          />
          <TextField
            autoComplete="current-password"
            fullWidth
            label="Пароль"
            name="password"
            placeholder="Введите пароль"
            type="password"
          />

          <Button disabled={loginMutation.isPending} fullWidth size="large" type="submit" variant="contained">
            {loginMutation.isPending ? 'Вход...' : 'Войти'}
          </Button>

          <Typography color="text.secondary" sx={{ textAlign: 'center' }}>
            Доступ к разделам и операциям определяется ролью и назначенными правами пользователя.
          </Typography>
        </Stack>
      </Paper>
    </Box>
  )
}
