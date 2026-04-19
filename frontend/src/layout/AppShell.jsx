import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded'
import MenuRoundedIcon from '@mui/icons-material/MenuRounded'
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import { alpha } from '@mui/material/styles'
import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { navigationItems } from './navigation'
import { useAuth } from '../auth/useAuth'
import { GlobalSearch } from '../components/GlobalSearch'
import { getUserInitials } from '../utils/format'

const drawerWidth = 288

function getPageMeta(pathname) {
  if (pathname.startsWith('/equipment/')) {
    return {
      title: 'Карточка оборудования',
      description: 'Текущее состояние, статический профиль и последний мониторинговый снимок.',
    }
  }

  const match = navigationItems.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  )

  if (match) {
    return {
      title: match.label,
      description: match.description,
    }
  }

  return {
    title: 'Рабочее пространство',
    description: 'Операционная панель мониторинга.',
  }
}

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const { hasAnyPermission, logout, user } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const pageMeta = getPageMeta(location.pathname)
  const visibleNavigationItems = navigationItems.filter((item) =>
    hasAnyPermission(item.requiredPermissions),
  )
  const roleNames = (user?.roles ?? []).map((role) => role.name).join(', ')

  function handleDrawerToggle() {
    setMobileOpen((currentValue) => !currentValue)
  }

  function handleNavigate(href) {
    navigate(href)
    setMobileOpen(false)
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ px: 3, pt: 3, pb: 2 }}>
        <Typography
          sx={{
            color: '#f5faf8',
            fontSize: 22,
            fontWeight: 800,
            letterSpacing: '-0.04em',
          }}
        >
          MEM Console
        </Typography>
        <Typography sx={{ color: alpha('#eef7f4', 0.72), mt: 1 }}>
          Рабочее пространство мониторинга горного оборудования.
        </Typography>
      </Box>

      <List sx={{ px: 2, py: 1 }}>
        {visibleNavigationItems.map((item) => {
          const isSelected =
            location.pathname === item.href ||
            location.pathname.startsWith(`${item.href}/`)
          const Icon = item.icon

          return (
            <ListItemButton
              key={item.href}
              onClick={() => handleNavigate(item.href)}
              selected={isSelected}
              sx={{
                borderRadius: 3,
                color: isSelected ? '#ffffff' : alpha('#eef7f4', 0.78),
                mb: 1,
                '&.Mui-selected': {
                  backgroundColor: alpha('#d6f7ef', 0.12),
                },
                '&.Mui-selected:hover, &:hover': {
                  backgroundColor: alpha('#d6f7ef', 0.16),
                },
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 42 }}>
                <Icon />
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                secondary={item.description}
                primaryTypographyProps={{ fontWeight: 700 }}
                secondaryTypographyProps={{
                  color: 'inherit',
                  sx: { opacity: 0.7 },
                }}
              />
            </ListItemButton>
          )
        })}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        color="transparent"
        elevation={0}
        position="fixed"
        sx={{
          backdropFilter: 'blur(18px)',
          backgroundColor: alpha('#eef2ef', 0.82),
          borderBottom: '1px solid',
          borderColor: 'divider',
          display: { md: 'none' },
          left: 0,
          width: '100%',
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography sx={{ fontWeight: 800 }}>MEM Console</Typography>
          <IconButton onClick={handleDrawerToggle}>
            <MenuRoundedIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          open={mobileOpen}
          onClose={handleDrawerToggle}
          variant="temporary"
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawerContent}
        </Drawer>
        <Drawer
          open
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        sx={{
          display: 'flex',
          flex: 1,
          flexDirection: 'column',
          minWidth: 0,
          pl: { md: 1.5 },
          pr: { xs: 2, md: 3 },
          pb: { xs: 2, md: 3 },
        }}
      >
        <Toolbar sx={{ display: { xs: 'flex', md: 'none' } }} />

        <Box
          sx={{
            position: 'sticky',
            top: { xs: 64, md: 0 },
            zIndex: 10,
            py: { xs: 2, md: 3 },
            backdropFilter: 'blur(16px)',
            backgroundColor: alpha('#eef2ef', 0.82),
          }}
        >
          <Stack
            direction={{ xs: 'column', lg: 'row' }}
            spacing={2}
            sx={{ alignItems: { lg: 'center' }, justifyContent: 'space-between' }}
          >
            <Box>
              <Typography
                sx={{
                  color: 'primary.main',
                  fontSize: 13,
                  fontWeight: 800,
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                }}
              >
                Операционная консоль
              </Typography>
              <Typography sx={{ fontSize: { xs: 28, md: 34 }, fontWeight: 800, mt: 0.5 }}>
                {pageMeta.title}
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                {pageMeta.description}
              </Typography>
            </Box>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
              <GlobalSearch />
              <Stack
                direction="row"
                spacing={1.5}
                sx={{
                  alignItems: 'center',
                  backgroundColor: 'background.paper',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 999,
                  px: 1,
                  py: 0.75,
                }}
              >
                <Avatar sx={{ bgcolor: 'primary.main', color: 'primary.contrastText' }}>
                  {getUserInitials(user)}
                </Avatar>
                <Box sx={{ minWidth: 0 }}>
                  <Typography noWrap sx={{ fontWeight: 800 }}>
                    {user ? `${user.first_name} ${user.last_name}` : 'Авторизованный пользователь'}
                  </Typography>
                  <Typography color="text.secondary" noWrap sx={{ fontSize: 13 }}>
                    {roleNames || user?.email || 'Сессия активна'}
                  </Typography>
                </Box>
                <Divider flexItem orientation="vertical" />
                <IconButton color="primary" onClick={handleLogout}>
                  <LogoutRoundedIcon />
                </IconButton>
              </Stack>
            </Stack>
          </Stack>
        </Box>

        <Box component="main" sx={{ display: 'flex', flex: 1, minWidth: 0 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
