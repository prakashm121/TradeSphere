import { ShoppingCart, DollarSign, TrendingUp } from 'lucide-react'

function TradingOrderPanel({
  selectedStock,
  tradeType,
  setTradeType,
  orderType,
  setOrderType,
  limitPrice,
  setLimitPrice,
  quantity,
  setQuantity,
  candleResolution,
  setCandleResolution,
  candles,
  candleLoading,
  orderBook,
  getOwnedQuantity,
  orderPrice,
  calculateTotal,
  canAfford,
  handleTrade,
  trading,
  socketStatus,
}) {
  const stockPrice = (selectedStock?.last_traded_price ?? selectedStock?.price) || 0

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-xl font-bold text-white mb-6">Place Order</h3>

      {selectedStock ? (
        <div className="space-y-6">
          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-white">{selectedStock.symbol}</h4>
              <span className="text-lg font-bold text-green-400">
                ₹{stockPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
            </div>
            <p className="text-sm text-gray-400">{selectedStock.name}</p>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-gray-300">
              <div>
                <div className="text-gray-400">Bid</div>
                <div className="text-white">
                  {selectedStock.bid_price ? `₹${selectedStock.bid_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'}
                </div>
              </div>
              <div>
                <div className="text-gray-400">Ask</div>
                <div className="text-white">
                  {selectedStock.ask_price ? `₹${selectedStock.ask_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'}
                </div>
              </div>
            </div>
          </div>

          <p className="text-sm text-gray-400">You own: {getOwnedQuantity(selectedStock.stock_id)} shares</p>
          <p className="text-xs text-gray-500">Market feed: {socketStatus}</p>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Side</label>
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

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Order Type</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setOrderType('MARKET')}
                className={`py-3 px-4 rounded-lg font-semibold transition-colors ${
                  orderType === 'MARKET'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Market
              </button>
              <button
                onClick={() => setOrderType('LIMIT')}
                className={`py-3 px-4 rounded-lg font-semibold transition-colors ${
                  orderType === 'LIMIT'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Limit
              </button>
            </div>
          </div>

          {orderType === 'LIMIT' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Limit Price</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Quantity</label>
            <input
              type="number"
              min="1"
              max={tradeType === 'sell' ? getOwnedQuantity(selectedStock.stock_id) : undefined}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Order Price:</span>
                <span className="text-white">₹{orderPrice().toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
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

          <button
            onClick={handleTrade}
            disabled={trading || !canAfford()}
            className={`w-full py-3 rounded-lg font-semibold transition-colors ${
              canAfford()
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            } ${trading ? 'opacity-70 cursor-wait' : ''}`}
          >
            {trading ? 'Placing order...' : tradeType === 'buy' ? 'Place Buy Order' : 'Place Sell Order'}
          </button>


          {/* Candle controls moved into the main chart area above */}
        </div>
      ) : (
        <div className="text-center py-8">
          <TrendingUp className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Select a stock to start trading</p>
        </div>
      )}
    </div>
  )
}

export default TradingOrderPanel;
