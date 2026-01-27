import { useState, useEffect } from 'react'
import { ArrowUpRight, ArrowDownLeft, Clock, Filter } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5000'

function Transactions({ user }) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    if (!user?.user_id) return
    fetchTransactions()
  }, [user?.user_id])

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/transactions`)
      setTransactions(response.data)
    } catch (error) {
      console.error('Error fetching transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredTransactions = transactions.filter(transaction => {
    if (filter === 'all') return true
    return transaction.type.toLowerCase() === filter
  })

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const totalBuyAmount = transactions
    .filter(t => t.type === 'BUY')
    .reduce((sum, t) => sum + (t.price_at_transaction * t.quantity), 0)

  const totalSellAmount = transactions
    .filter(t => t.type === 'SELL')
    .reduce((sum, t) => sum + (t.price_at_transaction * t.quantity), 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Transaction Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Transactions</p>
              <p className="text-2xl font-bold text-white">{transactions.length}</p>
            </div>
            <Clock className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Invested</p>
              <p className="text-2xl font-bold text-red-400">
                ₹{totalBuyAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <ArrowUpRight className="w-8 h-8 text-red-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Returns</p>
              <p className="text-2xl font-bold text-green-400">
                ₹{totalSellAmount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </p>
            </div>
            <ArrowDownLeft className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Transaction List */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">Transaction History</h3>
          
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Transactions</option>
              <option value="buy">Buy Orders</option>
              <option value="sell">Sell Orders</option>
            </select>
          </div>
        </div>

        {filteredTransactions.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No Transactions Yet</h3>
            <p className="text-gray-500">Start trading to see your transaction history</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Type</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Stock</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Quantity</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Price</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Total</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((transaction) => {
                  const total = transaction.price_at_transaction * transaction.quantity
                  const isBuy = transaction.type === 'BUY'
                  
                  return (
                    <tr key={transaction.transaction_id} className="border-b border-gray-700 hover:bg-gray-700 transition-colors">
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-2">
                          {isBuy ? (
                            <ArrowUpRight className="w-5 h-5 text-red-400" />
                          ) : (
                            <ArrowDownLeft className="w-5 h-5 text-green-400" />
                          )}
                          <span className={`font-semibold ${isBuy ? 'text-red-400' : 'text-green-400'}`}>
                            {transaction.type}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <div className="font-semibold text-white">{transaction.symbol}</div>
                          <div className="text-sm text-gray-400">{transaction.name}</div>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <span className="text-white font-medium">{transaction.quantity}</span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <span className="text-white">
                          ₹{transaction.price_at_transaction.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <span className={`font-semibold ${isBuy ? 'text-red-400' : 'text-green-400'}`}>
                          {isBuy ? '-' : '+'}₹{total.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <span className="text-gray-400 text-sm">
                          {formatDate(transaction.timestamp)}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Transactions