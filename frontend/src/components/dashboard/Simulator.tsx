
import { useState } from 'react'
import {
  Activity,
  Play,
  Square,
  RotateCcw,
  Settings2,
  Zap,
  Info,
} from 'lucide-react'

type SimulationStatus = 'idle' | 'running' | 'stopped'

export default function Simulator() {
  const [symbol, setSymbol] = useState('AAPL')
  const [orderCount, setOrderCount] = useState(1000)
  const [speed, setSpeed] = useState('normal')
  const [status, setStatus] = useState<SimulationStatus>('idle')

  const isValidOrderCount =
    Number.isInteger(orderCount) &&
    orderCount >= 100 &&
    orderCount <= 1000000

  const handleStart = () => {
    if (!isValidOrderCount || status === 'running') return
    setStatus('running')
  }

  const handleStop = () => {
    if (status === 'running') {
      setStatus('stopped')
    }
  }

  const handleReset = () => {
    setStatus('idle')
    setSymbol('AAPL')
    setOrderCount(1000)
    setSpeed('normal')
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
      description: 'Demo session marked as running.',
      color: 'text-emerald-500',
      dot: 'bg-emerald-500',
    },
    stopped: {
      label: 'Stopped',
      description: 'Demo session has been stopped.',
      color: 'text-amber-500',
      dot: 'bg-amber-500',
    },
  }

  const currentStatus = statusDetails[status]

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
            Configure and control simulated market sessions.
          </p>
        </div>

        <span className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-600 dark:text-amber-400">
          FRONTEND DEMO · NOT CONNECTED
        </span>
      </div>

      {/* Information */}
      <div className="flex gap-3 rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
        <Info size={19} className="mt-0.5 shrink-0 text-blue-500" />

        <p className="text-sm leading-relaxed text-[var(--muted)]">
          These controls currently demonstrate the frontend interaction.
          They do not start the Python market simulator or generate
          actual backend orders. Backend integration will be added later.
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
              <span className={`h-3 w-3 rounded-full ${currentStatus.dot}`} />

              <h4 className={`text-xl font-bold ${currentStatus.color}`}>
                {currentStatus.label}
              </h4>
            </div>

            <p className="mt-2 text-xs text-[var(--muted)]">
              {currentStatus.description}
            </p>
          </div>

          <div className="rounded-xl bg-[var(--surface-secondary)] p-4">
            <Activity size={28} className="text-blue-500" />
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">

        <div className="mb-6 flex items-center gap-2">
          <Settings2 size={20} className="text-blue-500" />

          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Simulation Configuration
            </h4>

            <p className="mt-1 text-xs text-[var(--muted)]">
              Configure your demonstration session.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">

          {/* Symbol */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[var(--foreground)]">
              Trading Symbol
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
          </div>

          {/* Order count */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[var(--foreground)]">
              Number of Orders
            </label>

            <input
              type="number"
              min={100}
              max={1000000}
              step={100}
              value={orderCount}
              disabled={status === 'running'}
              onChange={(event) =>
                setOrderCount(Number(event.target.value))
              }
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-3 text-sm text-[var(--foreground)] outline-none focus:border-blue-500 disabled:opacity-60"
            />

            <p className="mt-2 text-xs text-[var(--muted)]">
              Allowed range: 100–1,000,000 orders.
            </p>

            {!isValidOrderCount && (
              <p className="mt-2 text-xs text-rose-500">
                Enter a whole number between 100 and 1,000,000.
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
                { id: 'slow', label: 'Slow', description: 'Gradual' },
                { id: 'normal', label: 'Normal', description: 'Balanced' },
                { id: 'fast', label: 'Fast', description: 'Rapid' },
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
            <Play size={17} fill="currentColor" />
            Start Demo
          </button>

          <button
            onClick={handleStop}
            disabled={status !== 'running'}
            className="flex items-center gap-2 rounded-xl border border-rose-500/30 px-5 py-3 text-sm font-semibold text-rose-500 transition hover:bg-rose-500/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Square size={16} fill="currentColor" />
            Stop
          </button>

          <button
            onClick={handleReset}
            className="flex items-center gap-2 rounded-xl border border-[var(--border)] px-5 py-3 text-sm font-semibold text-[var(--muted)] transition hover:bg-[var(--surface-secondary)] hover:text-[var(--foreground)]"
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
              Selected Symbol
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
              {orderCount.toLocaleString()}
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

    </div>
  )
}
