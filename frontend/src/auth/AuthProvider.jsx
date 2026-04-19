import { useEffect, useState } from 'react'
import { getCurrentUser, loginRequest } from '../api/auth'
import { setUnauthorizedHandler } from '../api/http'
import {
  getUserPermissions,
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
} from './permissions'
import {
  clearStoredSession,
  loadStoredSession,
  saveStoredSession,
} from './storage'
import { AuthContext } from './AuthContext'

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadStoredSession())
  const [isInitializing, setIsInitializing] = useState(
    () => Boolean(loadStoredSession()?.accessToken),
  )

  useEffect(() => {
    function handleUnauthorized() {
      setSession(null)
      clearStoredSession()
    }

    setUnauthorizedHandler(handleUnauthorized)

    return () => {
      setUnauthorizedHandler(null)
    }
  }, [])

  useEffect(() => {
    const storedSession = loadStoredSession()

    if (!storedSession?.accessToken) {
      setIsInitializing(false)
      return undefined
    }

    let isMounted = true

    async function bootstrapSession() {
      try {
        const user = await getCurrentUser(storedSession.accessToken)

        if (!isMounted) {
          return
        }

        const nextSession = {
          accessToken: storedSession.accessToken,
          user,
        }

        setSession(nextSession)
        saveStoredSession(nextSession)
      } catch {
        if (!isMounted) {
          return
        }

        clearStoredSession()
        setSession(null)
      } finally {
        if (isMounted) {
          setIsInitializing(false)
        }
      }
    }

    bootstrapSession()

    return () => {
      isMounted = false
    }
  }, [])

  async function login(credentials) {
    const tokenPayload = await loginRequest(credentials)
    const user = tokenPayload.user ?? (await getCurrentUser(tokenPayload.access_token))

    const nextSession = {
      accessToken: tokenPayload.access_token,
      user,
    }

    saveStoredSession(nextSession)
    setSession(nextSession)
    return user
  }

  function logout() {
    clearStoredSession()
    setSession(null)
  }

  const currentUser = session?.user ?? null
  const permissions = getUserPermissions(currentUser)

  return (
    <AuthContext.Provider
      value={{
        accessToken: session?.accessToken ?? null,
        hasAllPermissions: (requiredPermissions = []) =>
          hasAllPermissions(currentUser, requiredPermissions),
        hasAnyPermission: (requiredPermissions = []) =>
          hasAnyPermission(currentUser, requiredPermissions),
        hasPermission: (requiredPermission) => hasPermission(currentUser, requiredPermission),
        isAuthenticated: Boolean(session?.accessToken),
        isInitializing,
        login,
        logout,
        permissions,
        user: currentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
