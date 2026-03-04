import { useState, useEffect } from 'react'
import { User, TrendingUp, Wallet, BarChart3, Menu, X } from 'lucide-react'
import Landing from './components/Landing'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import Portfolio from './components/Portfolio'
import Trading from './components/Trading'
import Transactions from './components/Transactions'
import './App.css'
import { auth } from './utils/auth'

function App() {
  const [user, setUser] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [authView, setAuthView] = useState('landing')

  useEffect(() => {
    // Restore session only if BOTH token + user are present.
    const token = auth.getToken()
    const savedUser = auth.getUser()

    if (token && savedUser) {
      if (savedUser && savedUser.user_id && typeof savedUser.balance === 'number') {
        setUser(savedUser)
      } else {
        console.warn('Invalid saved user in localStorage; clearing auth.')
        auth.clearAuth()
      }
    } else {
      // Avoid half-sessions (user without token or token without user)
      auth.clearAuth()
    }
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    auth.setUser(userData)
  }

  const handleLogout = () => {
    setUser(null)
    auth.clearAuth()
    setActiveTab('dashboard')
    setAuthView('landing')
  }

  const updateUserBalance = (newBalance) => {
    const updatedUser = { ...user, balance: newBalance }
    setUser(updatedUser)
    auth.setUser(updatedUser)
  }

  useEffect(() => {
    const onForcedLogout = () => {
      // Triggered by axios interceptor on 401/403
      setUser(null)
      setActiveTab('dashboard')
      setAuthView('landing')
    }
    window.addEventListener('auth:logout', onForcedLogout)
    return () => window.removeEventListener('auth:logout', onForcedLogout)
  }, [])

  if (!user) {
    if (authView === 'landing') {
      return (
        <Landing
          onLoginClick={() => setAuthView('login')}
          onSignupClick={() => setAuthView('signup')}
        />
      )
    }

    return (
      <Login
        key={authView}
        onLogin={handleLogin}
        mode={authView === 'signup' ? 'register' : 'login'}
        onBack={() => setAuthView('landing')}
      />
    )
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard user={user} updateBalance={updateUserBalance} />
      case 'portfolio':
        return <Portfolio user={user} />
      case 'trading':
        return <Trading user={user} updateBalance={updateUserBalance} />
      case 'transactions':
        return <Transactions user={user} />
      default:
        return <Dashboard user={user} updateBalance={updateUserBalance} />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white overflow-x-hidden">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 sm:px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-green-400" />
            <h1 className="text-xl sm:text-2xl font-bold">TradeSphere</h1>
          </div>
          
          {/* Desktop: balance, user, logout | Mobile: balance + logout */}
          <div className="hidden sm:flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <Wallet className="w-5 h-5 text-green-400" />
              <span className="text-lg font-semibold">
                ₹{user.balance?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5" />
              <span>{user.username}</span>
            </div>
            
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors text-sm"
            >
              Logout
            </button>
          </div>

          {/* Mobile: compact balance + hamburger */}
          <div className="sm:hidden flex items-center space-x-4">
            <div className="flex items-center space-x-1 text-sm">
              <Wallet className="w-4 h-4 text-green-400" />
              <span>₹{user.balance?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
            </div>
            <button
              className="p-2 rounded-md text-gray-300 hover:text-white hover:bg-gray-700"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 px-4 sm:px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <div className="hidden sm:flex space-x-8 overflow-x-auto whitespace-nowrap">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'portfolio', label: 'Portfolio', icon: Wallet },
              { id: 'trading', label: 'Trading', icon: TrendingUp },
              { id: 'transactions', label: 'Transactions', icon: User }
            ].map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-shrink-0 flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Mobile menu dropdown */}
      {menuOpen && (
        <div className="sm:hidden bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'portfolio', label: 'Portfolio', icon: Wallet },
              { id: 'trading', label: 'Trading', icon: TrendingUp },
              { id: 'transactions', label: 'Transactions', icon: User }
            ].map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id)
                    setMenuOpen(false)
                  }}
                  className={`w-full flex items-center space-x-2 px-4 py-3 text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
            {/* Mobile-only user info + logout */}
            <div className="border-t border-gray-700 px-4 py-3">
              <div className="flex items-center space-x-2 mb-3 pb-3 border-b border-gray-700">
                <User className="w-5 h-5" />
                <span className="font-semibold">{user.username}</span>
              </div>
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors font-semibold"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {renderContent()}
      </main>
    </div>
  )
}

export default App