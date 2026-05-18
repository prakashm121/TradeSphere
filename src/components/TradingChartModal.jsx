import { useEffect } from 'react'
import { X } from 'lucide-react'
import CandleChart from './CandleChart'

function TradingChartModal({
  isOpen,
  onClose,
  selectedStock,
  candles,
  candleLoading,
  candleResolution,
  setCandleResolution,
}) {
  useEffect(() => {
    if (!isOpen) return undefined

    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.body.style.overflow = originalOverflow || ''
    }
  }, [isOpen])
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/70 p-4">
      <div className="mx-auto w-full max-w-6xl rounded-3xl bg-gray-900 border border-gray-700 overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-700">
          <div>
            <h2 className="text-2xl font-semibold text-white">{selectedStock?.symbol ?? 'Chart'}</h2>
            <p className="text-sm text-gray-400">Full-screen candle panel with OHLC data</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 bg-gray-800 hover:bg-gray-700 text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-gray-300">Resolution</div>
            <div className="flex flex-wrap gap-2">
              {['1m', '5m', '1h', '1D', '1W'].map((resolution) => (
                <button
                  key={resolution}
                  onClick={() => setCandleResolution(resolution)}
                  className={`py-2 px-3 rounded-lg text-sm font-medium transition-colors ${candleResolution === resolution ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
                >
                  {resolution.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-3xl bg-gray-800 border border-gray-700 p-4 max-h-[70vh] overflow-hidden">
            {candleLoading ? (
              <div className="flex h-72 items-center justify-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white"></div>
              </div>
            ) : candles.length > 0 ? (
              <div className="overflow-x-auto">
                <CandleChart candles={candles} resolution={candleResolution} />
              </div>
            ) : (
              <div className="h-72 flex items-center justify-center text-gray-400">No candles available yet.</div>
            )}
          </div>

          <div className="overflow-x-auto rounded-3xl bg-gray-800 border border-gray-700 p-4">
            <table className="min-w-full text-sm text-left text-white">
              <thead>
                <tr className="text-xs uppercase text-gray-400 border-b border-gray-700">
                  <th className="py-2 px-2">Time</th>
                  <th className="py-2 px-2">O</th>
                  <th className="py-2 px-2">H</th>
                  <th className="py-2 px-2">L</th>
                  <th className="py-2 px-2">C</th>
                  <th className="py-2 px-2">Vol</th>
                </tr>
              </thead>
              <tbody>
                {candles.map((candle) => {
                  const open = Number(candle.open)
                  const high = Number(candle.high)
                  const low = Number(candle.low)
                  const close = Number(candle.close)
                  const volume = Number.isFinite(Number(candle.volume)) ? Number(candle.volume) : 0
                  const isBull = close >= open
                  return (
                    <tr key={candle.open_time} className="border-b border-gray-700">
                      <td className="py-2 px-2 text-gray-300">
                        {isNaN(new Date(candle.open_time).getTime()) ? '—' : new Date(candle.open_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-2 px-2">₹{Number.isFinite(open) ? open.toFixed(2) : '—'}</td>
                      <td className="py-2 px-2">₹{Number.isFinite(high) ? high.toFixed(2) : '—'}</td>
                      <td className="py-2 px-2">₹{Number.isFinite(low) ? low.toFixed(2) : '—'}</td>
                      <td className={`py-2 px-2 font-semibold ${isBull ? 'text-green-400' : 'text-red-400'}`}>₹{Number.isFinite(close) ? close.toFixed(2) : '—'}</td>
                      <td className="py-2 px-2">{volume}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TradingChartModal;
