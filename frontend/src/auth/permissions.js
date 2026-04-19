const defaultRouteOrder = [
  { href: '/dashboard', permissions: ['analytics.read'] },
  { href: '/equipment', permissions: ['equipment.read'] },
  { href: '/events', permissions: ['events.read'] },
  { href: '/maintenance', permissions: ['maintenance.read'] },
  { href: '/notifications', permissions: ['notifications.read'] },
]

export function getUserPermissions(user) {
  const permissions = new Set()

  for (const role of user?.roles ?? []) {
    for (const permission of role.permissions ?? []) {
      if (permission?.code) {
        permissions.add(permission.code)
      }
    }
  }

  return Array.from(permissions)
}

export function hasPermission(user, permission) {
  if (!permission) {
    return true
  }

  return getUserPermissions(user).includes(permission)
}

export function hasAllPermissions(user, permissions = []) {
  if (!permissions.length) {
    return true
  }

  const permissionSet = new Set(getUserPermissions(user))
  return permissions.every((permission) => permissionSet.has(permission))
}

export function hasAnyPermission(user, permissions = []) {
  if (!permissions.length) {
    return true
  }

  const permissionSet = new Set(getUserPermissions(user))
  return permissions.some((permission) => permissionSet.has(permission))
}

export function getDefaultAuthorizedPath(user) {
  const matchedRoute = defaultRouteOrder.find((item) =>
    hasAllPermissions(user, item.permissions),
  )

  return matchedRoute?.href ?? '/dashboard'
}
