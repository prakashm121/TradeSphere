/**
 * Login Component
 * ---------------
 * Handles both user authentication and account creation
 * for the TradeSphere platform.
 *
 * Features:
 * - Toggle between Login and Register modes
 * - Controlled form inputs (username & password)
 * - API integration using Axios
 * - Loading & error state handling
 * - Clean, responsive UI using Tailwind CSS
 *
 * Tech Stack:
 * - React (useState)
 * - Axios (API requests)
 * - Tailwind CSS (styling)
 * - lucide-react (icons)
 *
 * Props:
 * @param {Function} onLogin - Callback executed after successful login/register
 *                            Receives authenticated user data from backend
 */
import { useState, useEffect } from 'react'
import { TrendingUp, User, Lock, UserPlus } from 'lucide-react'
import axios from 'axios'
import { auth } from '../utils/auth'

const API_BASE_URL = 'http://127.0.0.1:5000'

function Login({ onLogin, mode }) {
  const [isRegister, setIsRegister] = useState(mode === 'register')
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Keep internal state in sync with App-provided mode (login/register)
  useEffect(() => {
    if (mode === 'register') setIsRegister(true)
    if (mode === 'login') setIsRegister(false)
  }, [mode])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // Backend supports:
      // - POST /auth/login -> { access_token, token_type }
      // - POST /auth/register -> user object (no token) => we auto-login after register
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const response = await axios.post(`${API_BASE_URL}${endpoint}`, formData)
      // Backward compatible parsing:
      // - New backend: { access_token, token_type, user }
      // - Some variants: { token, user } or { accessToken, user }
      // - Old backend: { user_id, username, balance }
      const data = response.data
      const token =
        data?.access_token ??
        data?.token ??
        data?.accessToken ??
        data?.jwt ??
        null
      if (token) auth.setToken(token)

      // If this was register (no token returned), auto-login to get token
      if (isRegister && !token) {
        const loginRes = await axios.post(`${API_BASE_URL}/auth/login`, formData)
        const loginData = loginRes.data
        const loginToken =
          loginData?.access_token ??
          loginData?.token ??
          loginData?.accessToken ??
          loginData?.jwt ??
          null
        if (loginToken) auth.setToken(loginToken)
      }

      // If we have a token, fetch user identity + balance from backend
      const storedToken = auth.getToken()
      if (storedToken) {
        const [meRes, balanceRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/auth/me`),
          axios.get(`${API_BASE_URL}/balance`),
        ])
        const me = meRes.data
        const balance = balanceRes.data?.balance
        onLogin({
          user_id: me.user_id,
          username: me.username,
          balance: typeof balance === 'number' ? balance : 0,
        })
        return
      }

      // Fallback: old backend shape already includes user fields
      const userPayload = data?.user ?? data
      onLogin(userPayload)
    } catch (err) {
      const data = err?.response?.data
      const msg =
        data?.error ??
        data?.detail ??
        (Array.isArray(data?.detail) ? data.detail.map((d) => d?.msg).filter(Boolean).join(', ') : null) ??
        err?.message ??
        'An error occurred'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full mb-4">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">TradeSphere</h1>
          <p className="text-gray-400 mt-2">Trade virtual stocks and build your portfolio</p>
        </div>

        {/* Form */}
        <div className="bg-gray-800 rounded-xl shadow-2xl p-8">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white">
              {isRegister ? 'Create Account' : 'Welcome Back'}
            </h2>
            <p className="text-gray-400 mt-1">
              {isRegister ? 'Start with ₹50,000 virtual money' : 'Sign in to your account'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your password"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-600 bg-opacity-20 border border-red-600 text-red-400 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  {isRegister ? <UserPlus className="w-5 h-5" /> : <User className="w-5 h-5" />}
                  <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsRegister(!isRegister)}
              className="text-blue-400 hover:text-blue-300 transition-colors"
            >
              {isRegister 
                ? 'Already have an account? Sign in' 
                : "Don't have an account? Create one"
              }
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-2 gap-4 text-center text-sm text-gray-400">
          <div>
            <div className="font-semibold text-green-400">₹50,000</div>
            <div>Starting Balance</div>
          </div>
          <div>
            <div className="font-semibold text-blue-400">₹5,000</div>
            <div>Daily Recovery</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login