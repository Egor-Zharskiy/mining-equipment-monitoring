import { Navigate, useLocation } from 'react-router-dom'
import { LoadingScreen } from '../components/LoadingScreen'
import { AccessDeniedPage } from '../pages/AccessDeniedPage'
import { useAuth } from './useAuth'

export function ProtectedRoute({ children, requiredPermissions = [], requireAll = true }) {
  const location = useLocation()
  const {
    hasAllPermissions,
    hasAnyPermission,
    isAuthenticated,
    isInitializing,
  } = useAuth()

  if (isInitializing) {
    return <LoadingScreen label="Проверка пользовательской сессии" />
  }

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to="/login" />
  }

  const isAuthorized = requireAll
    ? hasAllPermissions(requiredPermissions)
    : hasAnyPermission(requiredPermissions)

  if (!isAuthorized) {
    return <AccessDeniedPage />
  }

  return children
}
