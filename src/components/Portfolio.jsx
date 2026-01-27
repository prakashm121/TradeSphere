import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5000'

function Portfolio({ user }) {
  const [portfolio, setPortfolio] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user?.user_id) return
    fetchPortfolio()
  }, [user?.user_id])

  const fetchPortfolio = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/portfolio`)
      setPortfolio(response.data)
    } catch (error) {
      console.error('Error fetching portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalValue = portfolio.reduce((sum, stock) => sum + stock.current_value, 0)
  const totalShares = portfolio.reduce((sum, stock) => sum + stock.quantity, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
      </div>
    )
  }

  if (portfolio.length === 0) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-400 mb-2">No Holdings Yet</h3>
        <p className="text-gray-500 mb-6">Start trading to build your portfolio</p>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors">
          Start Trading
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Portfolio Value</p>
              <p className="text-2xl font-bold text-green-400">
                ₹{totalValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Shares</p>
              <p className="text-2xl font-bold text-blue-400">{totalShares}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Holdings</p>
              <p className="text-2xl font-bold text-purple-400">{portfolio.length}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Holdings List */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-6">Your Holdings</h3>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-gray-400 font-medium">Stock</th>
                <th className="text-right py-3 px-4 text-gray-400 font-medium">Shares</th>
                <th className="text-right py-3 px-4 text-gray-400 font-medium">Current Price</th>
                <th className="text-right py-3 px-4 text-gray-400 font-medium">Total Value</th>
                <th className="text-right py-3 px-4 text-gray-400 font-medium">Weight</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((stock) => {
                const weight = (stock.current_value / totalValue) * 100
                return (
                  <tr key={stock.stock_id} className="border-b border-gray-700 hover:bg-gray-700 transition-colors">
                    <td className="py-4 px-4">
                      <div>
                        <div className="font-semibold text-white">{stock.symbol}</div>
                        <div className="text-sm text-gray-400">{stock.name}</div>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className="text-white font-medium">{stock.quantity}</span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className="text-white font-medium">
                        ₹{stock.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className="text-green-400 font-semibold">
                        ₹{stock.current_value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <div className="w-16 h-2 bg-gray-600 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 transition-all duration-500"
                            style={{ width: `${Math.min(weight, 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-400 min-w-12">
                          {weight.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Portfolio Distribution */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-6">Portfolio Distribution</h3>
        
        <div className="space-y-4">
          {portfolio.map((stock, index) => {
            const weight = (stock.current_value / totalValue) * 100
            const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-yellow-500', 'bg-red-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500']
            const colorClass = colors[index % colors.length]
            
            return (
              <div key={stock.stock_id} className="flex items-center space-x-4">
                <div className={`w-4 h-4 ${colorClass} rounded`}></div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white font-medium">{stock.symbol}</span>
                    <span className="text-gray-400">{weight.toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${colorClass} transition-all duration-500`}
                      style={{ width: `${weight}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default Portfolio