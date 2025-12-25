import { useState, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, ShoppingCart, DollarSign, RefreshCw } from 'lucide-react';
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5000'

function Trading({ user, updateBalance }) {
  const [stocks, setStocks] = useState([])
  const [portfolio, setPortfolio] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const [tradeType, setTradeType] = useState('buy')
  const [quantity, setQuantity] = useState(1)
  const [loading, setLoading] = useState(true)
  const [trading, setTrading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  
  // Use refs for caching to avoid unnecessary re-renders
  const cachedStocks = useRef([])
  const lastFetchTime = useRef(0)

  useEffect(() => {
    if (!user?.user_id) return
    fetchData()
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

  const handleTrade = async () => {
    if (!selectedStock || quantity <= 0) return

    setTrading(true)
    try {
      const endpoint = tradeType === 'buy' ? '/buy' : '/sell'
      const response = await axios.post(`${API_BASE_URL}${endpoint}`, {
        user_id: user.user_id,
        stock_id: selectedStock.stock_id,
        quantity: parseInt(quantity)
      })

      updateBalance(response.data.new_balance)
      await fetchData()
      setQuantity(1)
      alert(`Successfully ${tradeType === 'buy' ? 'bought' : 'sold'} ${quantity} shares of ${selectedStock.symbol}!`)
    } catch (error) {
      alert(error.response?.data?.error || 'Trade failed')
    } finally {
      setTrading(false)
    }
  }

  const getOwnedQuantity = (stockId) => {
    const holding = portfolio.find(p => p.stock_id === stockId)
    return holding ? holding.quantity : 0
  }

  const calculateTotal = () => {
    if (!selectedStock) return 0
    return selectedStock.price * quantity
  }

  const canAfford = () => {
    if (tradeType === 'sell') {
      const owned = getOwnedQuantity(selectedStock?.stock_id)
      return quantity <= owned
    }
    return calculateTotal() <= user.balance
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">⚠️ Connection Error</div>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Stock List */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-white">Available Stocks</h3>
            <button
              onClick={fetchData}
              className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors cursor-pointer"
              disabled={refreshing}
            >
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
            </button>
          </div>

          <div className="space-y-3">
            {stocks.map((stock) => {
              const owned = getOwnedQuantity(stock.stock_id)
              const isSelected = selectedStock?.stock_id === stock.stock_id
              
              return (
                <div
                  key={stock.stock_id}
                  onClick={() => setSelectedStock(stock)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    isSelected 
                      ? 'border-blue-500 bg-blue-600 bg-opacity-20' 
                      : 'border-gray-600 hover:border-gray-500 bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-3">
                        <div>
                          <h4 className="font-semibold text-white">{stock.symbol}</h4>
                          <p className="text-sm text-gray-400">{stock.name}</p>
                        </div>
                        {owned > 0 && (
                          <span className="px-2 py-1 bg-green-600 bg-opacity-20 text-green-400 text-xs rounded-full">
                            {owned} owned
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">
                        ₹{stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                      </div>
                      <div className="flex items-center space-x-1 text-xs">
                        <TrendingUp className="w-3 h-3 text-green-400" />
                        <span className="text-green-400">Live</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Trading Panel */}
      <div className="space-y-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-6">Place Order</h3>
          
          {selectedStock ? (
            <div className="space-y-6">
              {/* Selected Stock Info */}
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-white">{selectedStock.symbol}</h4>
                  <span className="text-lg font-bold text-green-400">
                    ₹{selectedStock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </span>
                </div>
                <p className="text-sm text-gray-400">{selectedStock.name}</p>
                <p className="text-sm text-gray-400 mt-1">
                  You own: {getOwnedQuantity(selectedStock.stock_id)} shares
                </p>
              </div>

              {/* Trade Type */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Order Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setTradeType('buy')}
                    className={`py-3 px-4 rounded-lg font-semibold transition-colors ${
                      tradeType === 'buy'
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <ShoppingCart className="w-4 h-4 inline mr-2" />
                    Buy
                  </button>
                  <button
                    onClick={() => setTradeType('sell')}
                    disabled={getOwnedQuantity(selectedStock.stock_id) === 0}
                    className={`py-3 px-4 rounded-lg font-semibold transition-colors ${
                      tradeType === 'sell'
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed'
                    }`}
                  >
                    <DollarSign className="w-4 h-4 inline mr-2" />
                    Sell
                  </button>
                </div>
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Quantity
                </label>
                <input
                  type="number"
                  min="1"
                  max={tradeType === 'sell' ? getOwnedQuantity(selectedStock.stock_id) : undefined}
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Order Summary */}
              <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Price per share:</span>
                    <span className="text-white">₹{selectedStock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Quantity:</span>
                    <span className="text-white">{quantity}</span>
                  </div>
                  <div className="flex justify-between border-t border-gray-600 pt-2">
                    <span className="text-gray-400">Total:</span>
                    <span className={`font-semibold ${tradeType === 'buy' ? 'text-red-400' : 'text-green-400'}`}>
                      {tradeType === 'buy' ? '-' : '+'}₹{calculateTotal().toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Trade Button */}
              <button
                onClick={handleTrade}
                disabled={trading || !canAfford() || quantity <= 0}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                  tradeType === 'buy'
                    ? 'bg-green-600 hover:bg-green-700 disabled:bg-green-800'
                    : 'bg-red-600 hover:bg-red-700 disabled:bg-red-800'
                } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {trading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Processing...</span>
                  </div>
                ) : (
                  `${tradeType === 'buy' ? 'Buy' : 'Sell'} ${quantity} ${quantity === 1 ? 'Share' : 'Shares'}`
                )}
              </button>

              {!canAfford() && (
                <p className="text-red-400 text-sm text-center">
                  {tradeType === 'buy' 
                    ? 'Insufficient balance' 
                    : 'Insufficient shares'
                  }
                </p>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <TrendingUp className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Select a stock to start trading</p>
            </div>
          )}
        </div>

        {/* Account Info */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-bold text-white mb-4">Account Balance</h3>
          <div className="text-center">
            <p className="text-3xl font-bold text-green-400">
              ₹{user.balance.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </p>
            <p className="text-sm text-gray-400 mt-1">Available for trading</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Trading