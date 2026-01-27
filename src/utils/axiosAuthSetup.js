import axios from 'axios'
import { auth } from './auth'

const LOGOUT_EVENT = 'auth:logout'

// Ensure we only register interceptors once (important with HMR/dev reloads)
if (!axios.__tradesphereAuthInterceptorsInstalled) {
  axios.__tradesphereAuthInterceptorsInstalled = true

  // Fail fast when backend is down (prevents infinite-looking spinners)
  axios.defaults.timeout = 8000

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


