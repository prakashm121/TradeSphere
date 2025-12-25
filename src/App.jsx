import { useState, useEffect } from 'react'
import { User, TrendingUp, Wallet, BarChart3 } from 'lucide-react'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import Portfolio from './components/Portfolio'
import Trading from './components/Trading'
import Transactions from './components/Transactions'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser)
        if (parsed && parsed.user_id && typeof parsed.balance === 'number') {
          setUser(parsed)
        } else {
          console.warn('Invalid saved user in localStorage; clearing it.')
          localStorage.removeItem('user')
        }
      } catch (e) {
        console.warn('Failed to parse saved user; clearing it.', e)
        localStorage.removeItem('user')
      }
    }
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('user')
    setActiveTab('dashboard')
  }

  const updateUserBalance = (newBalance) => {
    const updatedUser = { ...user, balance: newBalance }
    setUser(updatedUser)
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-green-400" />
            <h1 className="text-2xl font-bold">TradeSphere</h1>
          </div>
          
          <div className="flex items-center space-x-6">
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
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <div className="flex space-x-8">
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
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {renderContent()}
      </main>
    </div>
  )
}

export default App