import axios from 'axios'
import { auth } from './auth'

const LOGOUT_EVENT = 'auth:logout'

// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')

// Ensure we only register interceptors once (important with HMR/dev reloads)
if (!axios.__tradesphereAuthInterceptorsInstalled) {
  axios.__tradesphereAuthInterceptorsInstalled = true

  // Give login enough time, but still fail fast if backend is down
  axios.defaults.timeout = 15000

  axios.interceptors.request.use(
    (config) => {
      const token = auth.getToken()
      if (token) {
        config.headers = config.headers ?? {}
        // Don't overwrite if caller already set Authorization
        if (!config.headers.Authorization && !config.headers.authorization) {
          config.headers.Authorization = `Bearer ${token}`
        }
      }
      return config
    },
    (error) => Promise.reject(error),
  )

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error?.response?.status
      if (status === 401 || status === 403) {
        auth.clearAuth()
        // Let the app react without forcing a page reload
        window.dispatchEvent(new Event(LOGOUT_EVENT))
      }
      return Promise.reject(error)
    },
  )
}


