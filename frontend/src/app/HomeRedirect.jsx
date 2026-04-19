import { Navigate } from 'react-router-dom'
import { getDefaultAuthorizedPath } from '../auth/permissions'
import { useAuth } from '../auth/useAuth'

export function HomeRedirect() {
  const { user } = useAuth()

  return <Navigate replace to={getDefaultAuthorizedPath(user)} />
}
