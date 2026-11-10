
import { useState } from 'react'
import {
  Activity,
  Play,
  RotateCcw,
  Settings2,
  Zap,
  Info,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from 'lucide-react'

import {
  runSimulation,
  type SimulationResponse,
} from '../../services/api'

type SimulationStatus = 'idle' | 'running' | 'completed' | 'error'

const speedIntervals: Record<string, number> = {
  slow: 0.01,
  normal: 0,
  fast: 0,
}

export default function Simulator() {
  const [symbol, setSymbol] = useState('AAPL')
  const [orderCount, setOrderCount] = useState(1000)
  const [speed, setSpeed] = useState('normal')
  const [status, setStatus] = useState<SimulationStatus>('idle')

  const [simulationResult, setSimulationResult] =
    useState<SimulationResponse | null>(null)

  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const isValidOrderCount =
    Number.isInteger(orderCount) &&
    orderCount >= 100 &&
    orderCount <= 100000

  const handleStart = async () => {
    if (!isValidOrderCount || status === 'running') return

    setStatus('running')
    setErrorMessage(null)
    setSimulationResult(null)

    try {
      const result = await runSimulation({
        order_count: orderCount,
        seed: 42,
        interval_seconds: speedIntervals[speed],
        buffer_capacity: 64,
      })

    setSimulationResult(result)
      sessionStorage.setItem(
      'chronosmatch_latest_simulation',
      JSON.stringify(result),
      )
     setStatus('completed')
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Unable to connect to the ChronosMatch API.',
      )
      setStatus('error')
    }
  }

  const handleReset = () => {
    if (status === 'running') return

    setStatus('idle')
    setSymbol('AAPL')
    setOrderCount(1000)
    setSpeed('normal')
    setSimulationResult(null)
    setErrorMessage(null)
  }

  const statusDetails = {
    idle: {
      label: 'Ready',
      description: 'Waiting for simulation configuration.',
      color: 'text-[var(--muted)]',
      dot: 'bg-slate-400',
    },
    running: {
      label: 'Running',
      description: 'ChronosMatch backend is processing orders.',
      color: 'text-blue-500',
      dot: 'bg-blue-500',
    },
    completed: {
      label: 'Completed',
      description: 'Simulation successfully processed by the backend.',
      color: 'text-emerald-500',
      dot: 'bg-emerald-500',
    },
    error: {
      label: 'Failed',
      description: 'The simulation could not be completed.',
      color: 'text-rose-500',
      dot: 'bg-rose-500',
    },
  }

  const currentStatus = statusDetails[status]

  const selectedTrades =
    simulationResult?.trades.filter(
      (trade) => trade.symbol === symbol,
    ) ?? []

  const selectedBook =
    simulationResult?.order_books.find(
      (book) => book.symbol === symbol,
    )

  const formatNumber = (value: number) =>
    value.toLocaleString('en-IN')

  const formatLatency = (value: number) =>
    `${(value / 1000).toFixed(2)} µs`

  return (
    <div className="space-y-6">

      {/* Heading */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Activity size={22} className="text-blue-500" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">
              Market Simulator
            </h3>
          </div>

          <p className="mt-1 text-sm text-[var(--muted)]">
            Configure and execute simulations using the Python backend.
          </p>
        </div>

        <span className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-600 dark:text-emerald-400">
          API CONNECTED
        </span>
      </div>

      {/* Information */}
      <div className="flex gap-3 rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
        <Info size={19} className="mt-0.5 shrink-0 text-blue-500" />

        <p className="text-sm leading-relaxed text-[var(--muted)]">
          Simulations run through the FastAPI backend, using the
          ChronosMatch matching engine and market pipeline. The backend
          generates orders for AAPL, MSFT and GOOGL. Select a symbol
          below to filter the displayed results.
        </p>
      </div>

      {/* Status */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-[var(--muted)]">
              Simulation Status
            </p>

            <div className="mt-3 flex items-center gap-3">
              <span
                className={`h-3 w-3 rounded-full ${currentStatus.dot}`}
              />

              <h4 className={`text-xl font-bold ${currentStatus.color}`}>
                {currentStatus.label}
              </h4>
            </div>

            <p className="mt-2 text-xs text-[var(--muted)]">
              {currentStatus.description}
            </p>
          </div>

          <div className="rounded-xl bg-[var(--surface-secondary)] p-4">
            {status === 'running' ? (
              <Loader2
                size={28}
                className="animate-spin text-blue-500"
              />
            ) : status === 'completed' ? (
              <CheckCircle2 size={28} className="text-emerald-500" />
            ) : status === 'error' ? (
              <AlertCircle size={28} className="text-rose-500" />
            ) : (
              <Activity size={28} className="text-blue-500" />
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {errorMessage && (
        <div className="flex gap-3 rounded-xl border border-rose-500/30 bg-rose-500/5 p-4">
          <AlertCircle size={20} className="shrink-0 text-rose-500" />

          <div>
            <p className="font-semibold text-rose-500">
              Simulation Error
            </p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {errorMessage}
            </p>
            <p className="mt-2 text-xs text-[var(--muted)]">
              Check that the FastAPI server is running on port 8000.
            </p>
          </div>
        </div>
      )}

      {/* Configuration */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">

        <div className="mb-6 flex items-center gap-2">
          <Settings2 size={20} className="text-blue-500" />

          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Simulation Configuration
            </h4>

            <p className="mt-1 text-xs text-[var(--muted)]">
              Configure your backend simulation.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">

          {/* Symbol */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[var(--foreground)]">
              Display Trading Symbol
            </label>

            <select
              value={symbol}
              disabled={status === 'running'}
              onChange={(event) => setSymbol(event.target.value)}
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-3 text-sm text-[var(--foreground)] outline-none focus:border-blue-500 disabled:opacity-60"
            >
              <option value="AAPL">AAPL</option>
              <option value="MSFT">MSFT</option>
              <option value="GOOGL">GOOGL</option>
            </select>

            <p className="mt-2 text-xs text-[var(--muted)]">
              Selects which symbol's results to display.
            </p>
          </div>

          {/* Order count */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[var(--foreground)]">
              Number of Orders
            </label>

            <input
              type="number"
              min={100}
              max={100000}
              step={100}
              value={orderCount}
              disabled={status === 'running'}
              onChange={(event) =>
                setOrderCount(Number(event.target.value))
              }
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-3 text-sm text-[var(--foreground)] outline-none focus:border-blue-500 disabled:opacity-60"
            />

            <p className="mt-2 text-xs text-[var(--muted)]">
              Allowed range: 100–100,000 orders.
            </p>

            {!isValidOrderCount && (
              <p className="mt-2 text-xs text-rose-500">
                Enter a whole number between 100 and 100,000.
              </p>
            )}
          </div>

          {/* Speed */}
          <div className="md:col-span-2">
            <label className="mb-2 block text-sm font-medium text-[var(--foreground)]">
              Simulation Speed
            </label>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {[
                { id: 'slow', label: 'Slow', description: '10 ms interval' },
                { id: 'normal', label: 'Normal', description: 'No delay' },
                { id: 'fast', label: 'Fast', description: 'No delay' },
              ].map((option) => (
                <button
                  key={option.id}
                  disabled={status === 'running'}
                  onClick={() => setSpeed(option.id)}
                  className={`rounded-xl border p-4 text-left transition ${
                    speed === option.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-[var(--border)] bg-[var(--surface-secondary)] hover:border-blue-500/50'
                  } disabled:cursor-not-allowed disabled:opacity-60`}
                >
                  <p className="text-sm font-semibold text-[var(--foreground)]">
                    {option.label}
                  </p>

                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {option.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-8 flex flex-wrap gap-3 border-t border-[var(--border)] pt-6">

          <button
            onClick={handleStart}
            disabled={!isValidOrderCount || status === 'running'}
            className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {status === 'running' ? (
              <Loader2 size={17} className="animate-spin" />
            ) : (
              <Play size={17} fill="currentColor" />
            )}

            {status === 'running' ? 'Processing...' : 'Run Simulation'}
          </button>

          <button
            onClick={handleReset}
            disabled={status === 'running'}
            className="flex items-center gap-2 rounded-xl border border-[var(--border)] px-5 py-3 text-sm font-semibold text-[var(--muted)] transition hover:bg-[var(--surface-secondary)] hover:text-[var(--foreground)] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <RotateCcw size={16} />
            Reset
          </button>
        </div>
      </div>

      {/* Configuration summary */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <div className="flex items-center gap-2">
          <Zap size={19} className="text-amber-500" />

          <h4 className="font-semibold text-[var(--foreground)]">
            Session Configuration
          </h4>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-[var(--muted)]">
              Display Symbol
            </p>
            <p className="mt-1 font-semibold text-[var(--foreground)]">
              {symbol}
            </p>
          </div>

          <div>
            <p className="text-xs text-[var(--muted)]">
              Configured Orders
            </p>
            <p className="mt-1 font-semibold text-[var(--foreground)]">
              {formatNumber(orderCount)}
            </p>
          </div>

          <div>
            <p className="text-xs text-[var(--muted)]">
              Selected Speed
            </p>
            <p className="mt-1 font-semibold capitalize text-[var(--foreground)]">
              {speed}
            </p>
          </div>
        </div>
      </div>

      {/* Actual backend results */}
      {simulationResult && (
        <>
          <div className="flex items-center gap-2">
            <CheckCircle2 size={20} className="text-emerald-500" />
            <h4 className="text-lg font-bold text-[var(--foreground)]">
              Backend Simulation Results
            </h4>
          </div>

          {/* Summary cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              {
                label: 'Orders Generated',
                value: simulationResult.summary.orders_generated,
              },
              {
                label: 'Orders Processed',
                value: simulationResult.summary.orders_processed,
              },
              {
                label: 'Total Trades',
                value: simulationResult.summary.trade_count,
              },
              {
                label: 'Throughput',
                value: `${formatNumber(
                  Math.round(
                    simulationResult.performance.throughput_orders_per_second,
                  ),
                )} / sec`,
              },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"
              >
                <p className="text-sm text-[var(--muted)]">
                  {item.label}
                </p>
                <p className="mt-3 text-2xl font-bold text-[var(--foreground)]">
                  {typeof item.value === 'number'
                    ? formatNumber(item.value)
                    : item.value}
                </p>
              </div>
            ))}
          </div>

          {/* Performance */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h4 className="font-semibold text-[var(--foreground)]">
              Performance Metrics
            </h4>

            <div className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-3">
              {[
                {
                  label: 'Elapsed Time',
                  value: `${(
                    simulationResult.performance.elapsed_ns / 1_000_000
                  ).toFixed(2)} ms`,
                },
                {
                  label: 'Minimum Latency',
                  value: formatLatency(
                    simulationResult.performance.latency_min_ns,
                  ),
                },
                {
                  label: 'Maximum Latency',
                  value: formatLatency(
                    simulationResult.performance.latency_max_ns,
                  ),
                },
                {
                  label: 'P50 Latency',
                  value: formatLatency(
                    simulationResult.performance.latency_p50_ns,
                  ),
                },
                {
                  label: 'P95 Latency',
                  value: formatLatency(
                    simulationResult.performance.latency_p95_ns,
                  ),
                },
                {
                  label: 'P99 Latency',
                  value: formatLatency(
                    simulationResult.performance.latency_p99_ns,
                  ),
                },
              ].map((metric) => (
                <div key={metric.label}>
                  <p className="text-xs text-[var(--muted)]">
                    {metric.label}
                  </p>
                  <p className="mt-1 font-semibold text-[var(--foreground)]">
                    {metric.value}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Order book */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <h4 className="font-semibold text-[var(--foreground)]">
              {symbol} Order Book Summary
            </h4>

            {selectedBook ? (
              <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-[var(--muted)]">
                    Active Orders
                  </p>
                  <p className="mt-1 text-xl font-bold text-[var(--foreground)]">
                    {formatNumber(selectedBook.active_order_count)}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-[var(--muted)]">
                    Best Bid (Ticks)
                  </p>
                  <p className="mt-1 text-xl font-bold text-emerald-500">
                    {selectedBook.best_bid ?? '—'}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-[var(--muted)]">
                    Best Ask (Ticks)
                  </p>
                  <p className="mt-1 text-xl font-bold text-rose-500">
                    {selectedBook.best_ask ?? '—'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-[var(--muted)]">
                No order book information available for this symbol.
              </p>
            )}
          </div>

          {/* Recent trades */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h4 className="font-semibold text-[var(--foreground)]">
                {symbol} Executed Trades
              </h4>

              <span className="text-xs text-[var(--muted)]">
                Showing up to 20 trades
              </span>
            </div>

            {selectedTrades.length > 0 ? (
              <div className="mt-5 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-xs text-[var(--muted)]">
                      <th className="px-3 py-3">Maker Order</th>
                      <th className="px-3 py-3">Taker Order</th>
                      <th className="px-3 py-3">Price (Ticks)</th>
                      <th className="px-3 py-3">Quantity</th>
                    </tr>
                  </thead>

                  <tbody>
                    {selectedTrades.slice(0, 20).map((trade, index) => (
                      <tr
                        key={`${trade.maker_order_id}-${trade.taker_order_id}-${index}`}
                        className="border-b border-[var(--border)] last:border-0"
                      >
                        <td className="px-3 py-3 font-mono text-xs text-[var(--foreground)]">
                          {trade.maker_order_id}
                        </td>
                        <td className="px-3 py-3 font-mono text-xs text-[var(--foreground)]">
                          {trade.taker_order_id}
                        </td>
                        <td className="px-3 py-3 text-[var(--foreground)]">
                          {trade.price_ticks}
                        </td>
                        <td className="px-3 py-3 text-[var(--foreground)]">
                          {trade.quantity}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 text-sm text-[var(--muted)]">
                No trades were executed for this symbol.
              </p>
            )}
          </div>

          <p className="text-xs text-[var(--muted)]">
            These results are generated by the ChronosMatch backend
            simulator. They are simulated market data, not live exchange data.
          </p>
        </>
      )}
    </div>
  )
}
