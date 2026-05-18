import { useState, useEffect, useRef, useCallback } from 'react'
import { Terminal } from 'lucide-react'
import axios from 'axios'
import { API_BASE_URL, WS_BASE_URL } from '../utils/axiosAuthSetup'
import TradingStockList from './TradingStockList'
import TradingOrderPanel from './TradingOrderPanel'
import TradingChartModal from './TradingChartModal'
import CandleChart from './CandleChart'

function Trading({ user, updateBalance }) {
  const [stocks, setStocks] = useState([])
  const [portfolio, setPortfolio] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const selectedStockId = selectedStock?.stock_id
  const resolutionOptions = ['1m', '5m', '1h', '1D', '1W']
  const [tradeType, setTradeType] = useState('buy')
  const [orderType, setOrderType] = useState('MARKET')
  const [limitPrice, setLimitPrice] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [loading, setLoading] = useState(true)
  const [trading, setTrading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [socketStatus, setSocketStatus] = useState('connecting')
  const [orderBook, setOrderBook] = useState(null)
  const [candles, setCandles] = useState([])
  const [candleResolution, setCandleResolution] = useState('5m')
  const [candleLoading, setCandleLoading] = useState(false)
  const [isChartOpen, setIsChartOpen] = useState(false)
  const socketRef = useRef(null)
  const selectedStockRef = useRef(null)
  const candleResolutionRef = useRef('5m')

  const handleSocketEvent = useCallback((event) => {
    try {
      if (!event?.type) return

      if (event.type === 'market_snapshot' && event.data) {
        const snapshot = event.data
        setStocks((prev) => prev.map((stock) => {
          const update = Object.values(snapshot).find((item) => item.stock_id === stock.stock_id)
          return update ? {
            ...stock,
            price: update.last_price,
            bid_price: update.bid,
            ask_price: update.ask,
            last_traded_price: update.last_price,
          } : stock
        }))
        setSelectedStock((prev) => {
          if (!prev) return prev
          const update = Object.values(snapshot).find((item) => item.stock_id === prev.stock_id)
          return update ? {
            ...prev,
            price: update.last_price,
            bid_price: update.bid,
            ask_price: update.ask,
            last_traded_price: update.last_price,
          } : prev
        })
        return
      }

      if (event.type === 'price_update') {
        setStocks((prev) => prev.map((stock) => {
          if (stock.stock_id !== event.stock_id) return stock
          return {
            ...stock,
            price: event.price,
            bid_price: event.bid,
            ask_price: event.ask,
            last_traded_price: event.price,
          }
        }))

        setSelectedStock((prev) => prev?.stock_id === event.stock_id ? {
          ...prev,
          price: event.price,
          bid_price: event.bid,
          ask_price: event.ask,
          last_traded_price: event.price,
        } : prev)
        return
      }

      if (event.type === 'candle_update' && selectedStockRef.current?.stock_id === event.stock_id && event.resolution === candleResolutionRef.current) {
        setCandles((prev) => {
          const next = [...prev]
          const index = next.findIndex((c) => c.open_time === event.candle.open_time)
          if (index >= 0) {
            next[index] = event.candle
          } else {
            next.push(event.candle)
            next.sort((a, b) => new Date(a.open_time) - new Date(b.open_time))
          }
          return next.slice(-30)
        })
        return
      }

      if (event.type === 'book_snapshot' && selectedStockRef.current?.stock_id === event.stock_id) {
        setOrderBook({ bids: event.bids, asks: event.asks })
        return
      }

      if (event.type === 'trade_tick') {
        setStocks((prev) => prev.map((stock) => {
          if (stock.stock_id !== event.stock_id) return stock
          return {
            ...stock,
            price: event.price,
            last_traded_price: event.price,
          }
        }))
        setSelectedStock((prev) => prev?.stock_id === event.stock_id ? {
          ...prev,
          price: event.price,
          last_traded_price: event.price,
        } : prev)
      }
    } catch (err) {
      console.error('Error handling socket event:', err)
    }
  }, [])

  // Keep refs in sync with state for safe closure access
  useEffect(() => {
    selectedStockRef.current = selectedStock
  }, [selectedStock])

  useEffect(() => {
    candleResolutionRef.current = candleResolution
  }, [candleResolution])

  useEffect(() => {
    if (!user?.user_id) return

    try {
      const socket = new WebSocket(`${WS_BASE_URL}/ws/market`)
      socketRef.current = socket

      socket.addEventListener('open', () => setSocketStatus('connected'))
      socket.addEventListener('close', () => setSocketStatus('disconnected'))
      socket.addEventListener('error', () => setSocketStatus('error'))

      socket.addEventListener('message', (event) => {
        try {
          const message = JSON.parse(event.data)
          handleSocketEvent(message)
        } catch (err) {
          console.warn('Invalid websocket message', err)
        }
      })

      return () => {
        try {
          socket.close(1000, 'Client cleanup')
        } catch (e) {
          console.warn('Error closing WebSocket:', e)
        }
      }
    } catch (err) {
      console.error('Error setting up WebSocket:', err)
      setSocketStatus('error')
    }
  }, [user?.user_id])

  const fetchOrderBook = useCallback(async (stockId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stocks/${stockId}/book`)
      setOrderBook(response.data)
    } catch (error) {
      console.error('Error fetching order book:', error)
      setOrderBook(null)
    }
  }, [])

  const fetchCandles = useCallback(async (stockId, resolution) => {
    setCandleLoading(true)
    try {
      const response = await axios.get(`${API_BASE_URL}/stocks/${stockId}/candles`, {
        params: { resolution, limit: 200 },
      })
      const incoming = response.data || []
      const sorted = [...incoming].sort((a, b) => new Date(a.open_time) - new Date(b.open_time))
      setCandles(sorted)
    } catch (error) {
      console.error('Error fetching candles:', error)
      setCandles([])
    } finally {
      setCandleLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!selectedStockId) {
      setOrderBook(null)
      setCandles([])
      return
    }

    fetchOrderBook(selectedStockId)
    fetchCandles(selectedStockId, candleResolution)
  }, [selectedStockId, candleResolution, fetchOrderBook, fetchCandles])

  useEffect(() => {
    if (!selectedStockId) return
    const initialPrice = Number(selectedStock?.price ?? selectedStock?.last_traded_price)
    setLimitPrice(Number.isFinite(initialPrice) && initialPrice > 0 ? initialPrice.toFixed(2) : '')
  }, [selectedStockId, selectedStock])

  const parseNumeric = (value, fallback = 0) => {
    const number = Number(value)
    return Number.isFinite(number) ? number : fallback
  }

  const selectedCandle = candles[candles.length - 1]
  const currentPrice = parseNumeric(selectedStock?.last_traded_price ?? selectedStock?.price ?? selectedCandle?.close)
  const previousClose = parseNumeric(selectedStock?.previous_close ?? selectedStock?.open_price ?? selectedCandle?.open ?? currentPrice)
  const priceChange = currentPrice && previousClose ? currentPrice - previousClose : 0
  const priceChangePercent = previousClose ? (priceChange / previousClose) * 100 : 0

  const formatPrice = (value) => {
    return Number.isFinite(value) ? value.toFixed(2) : '—'
  }

  const fetchData = useCallback(async (autoSelect = false) => {
    setRefreshing(true)
    setError(null)

    try {
      const [stocksRes, portfolioRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/stocks`),
        axios.get(`${API_BASE_URL}/portfolio`),
      ])
      const fetchedStocks = stocksRes.data
      setStocks(fetchedStocks)
      setPortfolio(portfolioRes.data)

      if (selectedStockRef.current) {
        const updatedSelected = fetchedStocks.find((stock) => stock.stock_id === selectedStockRef.current.stock_id)
        if (updatedSelected) {
          setSelectedStock(updatedSelected)
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      const status = error?.response?.status
      if (status === 401 || status === 403) {
        setError('Session expired or unauthorized. Please log in again.')
        window.dispatchEvent(new Event('auth:logout'))
      } else if (error?.request) {
        setError(`Failed to connect to the backend. Please make sure the backend is running on ${API_BASE_URL}`)
      } else {
        setError(error?.message || `Failed to connect to ${API_BASE_URL}`)
      }
    } finally {
      setLoading(false)
      setTimeout(() => setRefreshing(false), 300)
    }
  }, [])

  useEffect(() => {
    if (!user?.user_id) return

    fetchData(false)

    const interval = setInterval(() => {
      fetchData(false)
    }, 30000)

    return () => clearInterval(interval)
  }, [user?.user_id, fetchData])

  const handleTrade = async () => {
    if (!selectedStock || quantity <= 0) return

    if (orderType === 'LIMIT' && (!limitPrice || Number(limitPrice) <= 0)) {
      alert('Please enter a valid limit price')
      return
    }

    setTrading(true)
    try {
      const requestBody = {
        stock_id: selectedStock.stock_id,
        side: tradeType === 'buy' ? 'BUY' : 'SELL',
        order_type: orderType,
        quantity: parseInt(quantity, 10),
        ...(orderType === 'LIMIT' ? { price: Number(limitPrice) } : {}),
      }

      const response = await axios.post(`${API_BASE_URL}/orders`, requestBody)
      updateBalance(response.data.new_balance)
      await fetchData()
      setQuantity(1)
      alert(`Successfully submitted ${orderType.toLowerCase()} ${tradeType === 'buy' ? 'buy' : 'sell'} order for ${quantity} shares of ${selectedStock.symbol}`)
    } catch (error) {
      console.error('Order error:', error)
      const detail = error?.response?.data?.detail || error?.response?.data?.error
      const message = detail || error?.message || 'Order failed'
      alert(message)
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        window.dispatchEvent(new Event('auth:logout'))
      }
    } finally {
      setTrading(false)
    }
  }

  const getOwnedQuantity = (stockId) => {
    if (!Array.isArray(portfolio)) return 0
    const holding = portfolio.find((p) => p.stock_id === stockId)
    return holding ? holding.quantity : 0
  }

  const handleSelectStock = (stock) => {
    setSelectedStock(stock)
    setIsChartOpen(true)
  }

  const orderPrice = () => {
    if (!selectedStock) return 0
    if (orderType === 'LIMIT') {
      return Number(limitPrice) || 0
    }
    return parseNumeric(selectedStock.ask_price ?? selectedStock.price ?? selectedStock.last_traded_price)
  }

  const calculateTotal = () => {
    return orderPrice() * quantity
  }

  const canAfford = () => {
    if (!selectedStock) return false
    if (tradeType === 'sell') {
      const owned = getOwnedQuantity(selectedStock.stock_id)
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
            onClick={() => fetchData(false)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="px-4 sm:px-0 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {selectedStock ? (
            <div className="bg-gray-900 rounded-3xl border border-gray-700 p-6 space-y-6">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="text-2xl font-bold text-white">{selectedStock.symbol}</div>
                    <span className="text-sm text-gray-400">{selectedStock.name}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="text-4xl font-bold text-green-400">₹{currentPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                    <div className={`text-sm font-semibold ${priceChange >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                    </div>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm text-gray-300">
                    <div className="rounded-2xl bg-slate-950/70 p-3">
                      <div className="text-xs uppercase text-gray-500">Open</div>
                      <div className="font-semibold">₹{formatPrice(selectedCandle?.open)}</div>
                    </div>
                    <div className="rounded-2xl bg-slate-950/70 p-3">
                      <div className="text-xs uppercase text-gray-500">High</div>
                      <div className="font-semibold">₹{formatPrice(selectedCandle?.high)}</div>
                    </div>
                    <div className="rounded-2xl bg-slate-950/70 p-3">
                      <div className="text-xs uppercase text-gray-500">Low</div>
                      <div className="font-semibold">₹{formatPrice(selectedCandle?.low)}</div>
                    </div>
                    <div className="rounded-2xl bg-slate-950/70 p-3">
                      <div className="text-xs uppercase text-gray-500">Close</div>
                      <div className="font-semibold">₹{formatPrice(selectedCandle?.close)}</div>
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {resolutionOptions.map((resolution) => (
                    <button
                      key={resolution}
                      onClick={() => setCandleResolution(resolution)}
                      className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${candleResolution === resolution ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
                    >
                      {resolution.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-3xl border border-gray-700 overflow-hidden bg-slate-950/90">
                <div className="p-4">
                  <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div className="text-sm text-gray-400">Chart available in modal</div>
                    <button
                      onClick={() => setIsChartOpen(true)}
                      className="inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
                    >
                      View chart
                    </button>
                  </div>
                  <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
                    <div className="rounded-3xl bg-black/40 p-6 flex flex-col items-center justify-center text-center min-h-[340px]">
                      <div className="text-white text-lg font-semibold mb-2">Flip open the chart for details.</div>
                      <p className="text-sm text-gray-400 mb-6 max-w-xl">
                        The full candlestick and volume panel is now shown in the modal so the stock list stays compact.
                      </p>
                      <button
                        onClick={() => setIsChartOpen(true)}
                        className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition"
                      >
                        Open chart
                      </button>
                    </div>
                    <div className="bg-slate-950/80 rounded-3xl border border-gray-700 p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h4 className="text-white font-semibold">Order Book</h4>
                          <p className="text-sm text-gray-500">Top 5 bids & asks</p>
                        </div>
                        <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${orderBook ? 'bg-emerald-500/20 text-emerald-200' : 'bg-gray-700 text-gray-300'}`}>
                          {orderBook ? 'LIVE' : 'OFFLINE'}
                        </span>
                      </div>
                      {orderBook ? (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-3 text-xs uppercase text-gray-400 tracking-wide">
                            <span>Bid</span>
                            <span>Ask</span>
                          </div>
                          <div className="space-y-2">
                            {Array.from({ length: 5 }).map((_, index) => {
                              const bid = orderBook.bids?.[index]
                              const ask = orderBook.asks?.[index]
                              const bidMax = orderBook.bids?.length ? Math.max(...orderBook.bids.map((level) => level.quantity || 1)) : 1
                              const askMax = orderBook.asks?.length ? Math.max(...orderBook.asks.map((level) => level.quantity || 1)) : 1
                              const bidWidth = bid ? Math.min(100, Math.max(20, (bid.quantity / bidMax) * 100)) : 0
                              const askWidth = ask ? Math.min(100, Math.max(20, (ask.quantity / askMax) * 100)) : 0
                              return (
                                <div key={`book-row-${index}`} className="grid grid-cols-2 gap-3 text-sm text-white">
                                  <div className="relative rounded-lg bg-gray-900/90 px-3 py-2">
                                    {bid ? (
                                      <>
                                        <div className="absolute inset-y-0 left-0 rounded-l-lg bg-emerald-500/20" style={{ width: `${bidWidth}%` }} />
                                        <div className="relative flex justify-between items-center">
                                          <span>₹{bid.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                                          <span>{bid.quantity}</span>
                                        </div>
                                      </>
                                    ) : (
                                      <div className="text-gray-500">-</div>
                                    )}
                                  </div>
                                  <div className="relative rounded-lg bg-gray-900/90 px-3 py-2">
                                    {ask ? (
                                      <>
                                        <div className="absolute inset-y-0 right-0 rounded-r-lg bg-red-500/20" style={{ width: `${askWidth}%` }} />
                                        <div className="relative flex justify-between items-center">
                                          <span>₹{ask.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                                          <span>{ask.quantity}</span>
                                        </div>
                                      </>
                                    ) : (
                                      <div className="text-gray-500">-</div>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-400">Order book data is loading. Select a stock to fetch bids and asks.</div>
                      )}
                    </div>
                  </div>
                </div>
            </div>
          </div>
          ) : null}

          <TradingStockList
            stocks={stocks}
            selectedStock={selectedStock}
            onSelectStock={handleSelectStock}
            getOwnedQuantity={getOwnedQuantity}
            refreshing={refreshing}
            onRefresh={() => fetchData(false)}
          />
        </div>

        <div className="space-y-6">
          <TradingOrderPanel
            selectedStock={selectedStock}
            tradeType={tradeType}
            setTradeType={setTradeType}
            orderType={orderType}
            setOrderType={setOrderType}
            limitPrice={limitPrice}
            setLimitPrice={setLimitPrice}
            quantity={quantity}
            setQuantity={setQuantity}
            candleResolution={candleResolution}
            setCandleResolution={setCandleResolution}
            candles={candles}
            candleLoading={candleLoading}
            orderBook={orderBook}
            getOwnedQuantity={getOwnedQuantity}
            orderPrice={orderPrice}
            calculateTotal={calculateTotal}
            canAfford={canAfford}
            handleTrade={handleTrade}
            trading={trading}
            socketStatus={socketStatus}
            onOpenChart={() => setIsChartOpen(true)}
          />

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

      <TradingChartModal
        isOpen={isChartOpen}
        onClose={() => setIsChartOpen(false)}
        selectedStock={selectedStock}
        candles={candles}
        candleLoading={candleLoading}
        candleResolution={candleResolution}
        setCandleResolution={setCandleResolution}
      />
    </>
  )
}

export default Trading
