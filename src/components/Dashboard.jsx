import { useState, useEffect, useRef } from 'react'
import { TrendingUp, TrendingDown, RefreshCw, Gift } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5000'

function Dashboard({ user, updateBalance }) {
  const [stocks, setStocks] = useState([])
  const [portfolio, setPortfolio] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [recoveryStatus, setRecoveryStatus] = useState(null)
  const lastFetchTime = useRef(0)
  const cachedStocks = useRef([])

  useEffect(() => {
    if (!user?.user_id) return
    fetchData()
    fetchRecoveryStatus()
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [user?.user_id])

  const fetchData = async () => {
    const currentTime = Date.now();

    // Show refreshing animation
    setRefreshing(true);
    setError(null);

    // If last fetch was within 30 seconds, use cached stocks
    if (currentTime - lastFetchTime.current < 30000 && cachedStocks.current.length > 0) {
      try {
        // Only fetch portfolio data (which doesn't affect stock prices)
        const portfolioRes = await axios.get(`${API_BASE_URL}/portfolio/${user.user_id}`)
        setPortfolio(portfolioRes.data)
        // Keep using cached stocks
        setStocks(cachedStocks.current)
      } catch (error) {
        console.error('Error fetching portfolio data:', error)
        setError('Failed to fetch portfolio data. Please check if the backend server is running.')
      } finally {
        setLoading(false)
        // Hide refreshing animation after a brief delay for visual feedback
        setTimeout(() => setRefreshing(false), 300)
      }
      return;
    }

    try {
      const [stocksRes, portfolioRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/stocks`),
        axios.get(`${API_BASE_URL}/portfolio/${user.user_id}`)
      ])
      setStocks(stocksRes.data)
      setPortfolio(portfolioRes.data)
      cachedStocks.current = stocksRes.data // Cache the stocks
      lastFetchTime.current = currentTime // Update last fetch time
    } catch (error) {
      console.error('Error fetching data:', error)
      setError('Failed to connect to the server. Please make sure the backend is running on http://127.0.0.1:5000')
    } finally {
      setLoading(false)
      // Hide refreshing animation after a brief delay for visual feedback
      setTimeout(() => setRefreshing(false), 300)
    }
  }

  const fetchRecoveryStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/recovery-status/${user.user_id}`)
      setRecoveryStatus(response.data)
    } catch (error) {
      console.error('Error fetching recovery status:', error)
    }
  }

  const handleRecovery = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/recover-balance/${user.user_id}`)
      updateBalance(response.data.new_balance)
      fetchRecoveryStatus()
      alert(`₹${response.data.recovery_amount} added to your account!`)
    } catch (error) {
      alert(error.response?.data?.error || 'Recovery failed')
    }
  }

  const totalPortfolioValue = portfolio.reduce((sum, stock) => sum + stock.current_value, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Available Balance</p>
              <p className="text-2xl font-bold text-green-400">
                ₹{Number(user?.balance ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Portfolio Value</p>
              <p className="text-2xl font-bold text-blue-400">
                ₹{totalPortfolioValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Value</p>
              <p className="text-2xl font-bold text-white">
                ₹{(user.balance + totalPortfolioValue).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Recovery Section */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white mb-2">Daily Balance Recovery</h3>
            <p className="text-gray-400">Recover ₹5,000 every 24 hours to keep trading!</p>
          </div>
          
          {recoveryStatus?.can_recover ? (
            <button
              onClick={handleRecovery}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center space-x-2 transition-colors"
            >
              <Gift className="w-5 h-5" />
              <span>Claim ₹5,000</span>
            </button>
          ) : (
            <div className="text-center">
              <p className="text-gray-400 text-sm">Next recovery in:</p>
              <p className="text-white font-semibold">
                {recoveryStatus?.hours_left}h {recoveryStatus?.minutes_left}m
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Stock Market */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">Stock Market</h3>
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stocks.map((stock) => (
            <div key={stock.stock_id} className="bg-gray-700 rounded-lg p-4 border border-gray-600 hover:border-gray-500 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h4 className="font-semibold text-white">{stock.symbol}</h4>
                  <p className="text-sm text-gray-400">{stock.name}</p>
                </div>
                <TrendingUp className="w-5 h-5 text-green-400" />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-white">
                  ₹{stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </span>
                <span className="text-xs text-green-400">Live</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Portfolio Summary */}
      {portfolio.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-6">Your Holdings</h3>
          
          <div className="space-y-4">
            {portfolio.map((holding) => (
              <div key={holding.stock_id} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg border border-gray-600">
                <div>
                  <h4 className="font-semibold text-white">{holding.symbol}</h4>
                  <p className="text-sm text-gray-400">{holding.quantity} shares</p>
                </div>
                
                <div className="text-right">
                  <p className="font-semibold text-white">
                    ₹{holding.current_value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-sm text-gray-400">
                    @ ₹{holding.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard