export const AUTH_TOKEN_KEY = 'token'
export const AUTH_USER_KEY = 'user'

export const auth = {
  getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY)
  },

  setToken(token) {
    if (!token) return
    localStorage.setItem(AUTH_TOKEN_KEY, token)
  },

  clearToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY)
  },

  getUser() {
    const raw = localStorage.getItem(AUTH_USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw)
    } catch {
      return null
    }
  },

  setUser(user) {
    if (!user) return
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
  },

  clearUser() {
    localStorage.removeItem(AUTH_USER_KEY)
  },

  clearAuth() {
    this.clearToken()
    this.clearUser()
  },
}


