import { RefreshCw, TrendingUp } from 'lucide-react'

function TradingStockList({ stocks, selectedStock, onSelectStock, getOwnedQuantity, refreshing, onRefresh }) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white">Available Stocks</h3>
        <button
          onClick={onRefresh}
          className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors cursor-pointer"
          disabled={refreshing}
        >
          <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>

      <div className="space-y-3">
        {Array.isArray(stocks) && stocks.map((stock) => {
          const owned = getOwnedQuantity(stock.stock_id)
          const isSelected = selectedStock?.stock_id === stock.stock_id

          return (
            <div
              key={stock.stock_id}
              onClick={() => onSelectStock(stock)}
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
                    ₹{((stock.last_traded_price ?? stock.price) || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
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
  )
}

export default TradingStockList;
