const STORAGE_KEY = 'mem-auth-session'

export function loadStoredSession() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)

    if (!value) {
      return null
    }

    const parsed = JSON.parse(value)

    if (!parsed?.accessToken) {
      return null
    }

    return {
      accessToken: parsed.accessToken,
      user: parsed.user ?? null,
    }
  } catch {
    return null
  }
}

export function saveStoredSession(session) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearStoredSession() {
  window.localStorage.removeItem(STORAGE_KEY)
}
