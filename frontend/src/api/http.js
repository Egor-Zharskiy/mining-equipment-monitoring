import axios from 'axios'
import { clearStoredSession, loadStoredSession } from '../auth/storage'

const apiBaseUrl =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ||
  'http://localhost:8000/api/v1'

let unauthorizedHandler = null

function isAuthRequest(url = '') {
  return url.includes('/auth/login')
}

function getErrorMessage(error) {
  const detail = error.response?.data?.detail

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(', ')
  }

  if (typeof detail === 'string') {
    return detail
  }

  if (error.code === 'ECONNABORTED') {
    return 'The request timed out.'
  }

  return error.message || 'Request failed.'
}

function toApiError(error) {
  const apiError = new Error(getErrorMessage(error))
  apiError.status = error.response?.status
  apiError.data = error.response?.data
  return apiError
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

export const http = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10_000,
})

http.interceptors.request.use((config) => {
  const session = loadStoredSession()

  if (session?.accessToken) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${session.accessToken}`
  }

  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !isAuthRequest(error.config?.url)) {
      clearStoredSession()
      unauthorizedHandler?.()
    }

    return Promise.reject(toApiError(error))
  },
)
