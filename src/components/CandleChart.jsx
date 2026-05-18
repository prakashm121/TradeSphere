import { useMemo } from 'react'

function formatTimeLabel(openTime, resolution) {
  const date = new Date(openTime)
  if (Number.isNaN(date.getTime())) return ''

  if (resolution === '1D' || resolution === '1W') {
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  }

  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
}

function toNumber(value, fallback = 0) {
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}

function CandleChart({ candles = [], width = 820, height = 420, maxBars = 40, resolution = '5m' }) {
  const chartCandles = useMemo(
    () => candles
      .map((c) => ({
        ...c,
        open: toNumber(c.open),
        high: toNumber(c.high),
        low: toNumber(c.low),
        close: toNumber(c.close),
        volume: Number.isFinite(Number(c.volume)) ? Number(c.volume) : 0,
      }))
      .sort((a, b) => new Date(a.open_time) - new Date(b.open_time))
      .slice(-maxBars),
    [candles, maxBars],
  )

  const closes = useMemo(() => chartCandles.map((c) => c.close), [chartCandles])

  const movingAverage = useMemo(() => {
    const period = Math.min(20, chartCandles.length)
    return chartCandles.map((_, index) => {
      if (index < period - 1) return null
      const slice = closes.slice(index - period + 1, index + 1)
      const avg = slice.reduce((sum, value) => sum + value, 0) / period
      return avg
    })
  }, [chartCandles, closes])

  const bollingerBands = useMemo(() => {
    const period = Math.min(20, chartCandles.length)
    return chartCandles.map((_, index) => {
      if (index < period - 1) return null
      const slice = closes.slice(index - period + 1, index + 1)
      const avg = slice.reduce((sum, value) => sum + value, 0) / period
      const variance = slice.reduce((sum, value) => sum + Math.pow(value - avg, 2), 0) / period
      const deviation = Math.sqrt(variance)
      return {
        upper: avg + deviation * 2,
        lower: avg - deviation * 2,
      }
    })
  }, [chartCandles, closes])

  if (!chartCandles.length) {
    return (
      <div className="text-gray-400 text-sm text-center py-8">
        No candle data yet. Trade volume will populate candles automatically.
      </div>
    )
  }

  const values = chartCandles.flatMap((c) => [c.open, c.high, c.low, c.close])
  const maxValue = Math.max(...values)
  const minValue = Math.min(...values)
  const valueRange = maxValue - minValue || 1

  const volumeMax = Math.max(...chartCandles.map((c) => c.volume || 0), 1)

  const padding = 50
  const priceHeight = height - 110
  const volumeHeight = 70
  const innerWidth = width - padding * 2
  const visibleCandles = Math.max(chartCandles.length, 8)
  const candleGap = innerWidth / visibleCandles
  const candleWidth = Math.min(24, Math.max(8, candleGap * 0.6))
  const xOffset = chartCandles.length < visibleCandles ? ((visibleCandles - chartCandles.length) / 2) * candleGap : 0

  const scalePrice = (value) => padding + ((maxValue - value) / valueRange) * priceHeight
  const scaleVolume = (value) => priceHeight + padding + volumeHeight - (value / volumeMax) * volumeHeight

  const lastPrice = chartCandles[chartCandles.length - 1].close
  const lastPriceY = scalePrice(lastPrice)

  return (
    <div className="overflow-x-auto rounded-3xl border border-gray-700 bg-slate-950/90 p-2">
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet" className="block mx-auto max-w-full">
        {/* Price grid + axis */}
        {[0, 1 / 3, 2 / 3, 1].map((ratio) => {
          const y = padding + ratio * priceHeight
          const value = maxValue - ratio * valueRange
          return (
            <g key={`grid-${ratio}`}>
              <line x1={padding} x2={width - padding} y1={y} y2={y} stroke="#334155" strokeWidth="1" />
              <text x={padding - 10} y={y + 4} textAnchor="end" fontSize="12" fill="#94a3b8">
                ₹{value.toFixed(2)}
              </text>
            </g>
          )
        })}

        {/* Bollinger band area */}
        {bollingerBands.map((band, index) => {
          if (!band) return null
          const x = padding + xOffset + index * candleGap + candleGap / 2
          const upperY = scalePrice(band.upper)
          const lowerY = scalePrice(band.lower)
          return (
            <line
              key={`bb-${index}`}
              x1={x}
              x2={x}
              y1={upperY}
              y2={lowerY}
              stroke="#38bdf8"
              strokeWidth="0.5"
              opacity="0.35"
            />
          )
        })}

        {/* Moving average line */}
        <path
          d={movingAverage
            .map((value, index) => {
              if (value == null) return ''
              const x = padding + xOffset + index * candleGap + candleGap / 2
              const y = scalePrice(value)
              return `${index === 0 || movingAverage[index - 1] == null ? 'M' : 'L'} ${x} ${y}`
            })
            .join(' ')
          }
          fill="none"
          stroke="#60a5fa"
          strokeWidth="2"
          opacity="0.85"
        />

        {/* Candles */}
        {chartCandles.map((candle, index) => {
          const x = padding + xOffset + index * candleGap + (candleGap - candleWidth) / 2
          const openY = scalePrice(candle.open)
          const closeY = scalePrice(candle.close)
          const highY = scalePrice(candle.high)
          const lowY = scalePrice(candle.low)
          const isBull = candle.close >= candle.open
          const color = isBull ? '#22c55e' : '#ef4444'
          const bodyY = Math.min(openY, closeY)
          const bodyHeight = Math.max(2, Math.abs(closeY - openY))

          return (
            <g key={candle.open_time}>
              <line x1={x + candleWidth / 2} x2={x + candleWidth / 2} y1={highY} y2={lowY} stroke={color} strokeWidth="2" />
              <rect x={x} y={bodyY} width={candleWidth} height={bodyHeight} fill={color} opacity="0.9" />
            </g>
          )
        })}

        {/* Last price marker */}
        <line x1={padding} x2={width - padding} y1={lastPriceY} y2={lastPriceY} stroke="#22c55e" strokeWidth="1" strokeDasharray="4 4" />
        <text x={width - padding + 8} y={lastPriceY + 4} fontSize="12" fill="#22c55e">₹{lastPrice.toFixed(2)}</text>

        {/* Volume bars */}
        {chartCandles.map((candle, index) => {
          const x = padding + xOffset + index * candleGap + (candleGap - candleWidth) / 2
          const volumeTop = scaleVolume(candle.volume || 0)
          const volumeBottom = priceHeight + padding + volumeHeight
          const barHeight = Math.max(2, volumeBottom - volumeTop)
          const isBull = candle.close >= candle.open
          const color = isBull ? '#22c55e' : '#ef4444'
          return (
            <rect
              key={`vol-${candle.open_time}`}
              x={x}
              y={volumeTop}
              width={candleWidth}
              height={barHeight}
              fill={color}
              opacity="0.7"
            />
          )
        })}

        {/* Volume axis line */}
        <line x1={padding} x2={width - padding} y1={priceHeight + padding + volumeHeight} y2={priceHeight + padding + volumeHeight} stroke="#475569" strokeWidth="1" />
        <text x={padding - 10} y={priceHeight + padding + 14} textAnchor="end" fontSize="12" fill="#94a3b8">Vol</text>

        {/* Time axis labels */}
        {chartCandles.map((candle, index) => {
          const labelInterval = Math.max(1, Math.floor(chartCandles.length / 7))
          if (index % labelInterval !== 0) return null
          const x = padding + xOffset + index * candleGap + candleWidth / 2
          return (
            <text key={`time-${candle.open_time}`} x={x} y={height - 6} textAnchor="middle" fontSize="10" fill="#94a3b8">
              {formatTimeLabel(candle.open_time, resolution)}
            </text>
          )
        })}
      </svg>
    </div>
  )
}

export default CandleChart
