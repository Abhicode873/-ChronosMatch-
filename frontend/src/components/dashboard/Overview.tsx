
import { useState } from 'react'
import {
  Activity,
  Clock3,
  Zap,
  ArrowLeftRight,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { SimulationResponse } from '../../services/api'

const STORAGE_KEY = 'chronosmatch_latest_simulation'

function loadLatestSimulation(): SimulationResponse | null {
  const savedResult = sessionStorage.getItem(STORAGE_KEY)

  if (!savedResult) return null

  try {
    return JSON.parse(savedResult) as SimulationResponse
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export default function Overview() {
  const [simulation] = useState<SimulationResponse | null>(
    loadLatestSimulation,
  )

  const formatNumber = (value: number) =>
    value.toLocaleString('en-IN')

  const metrics = [
    {
      title: 'Orders Processed',
      value: simulation
        ? formatNumber(simulation.summary.orders_processed)
        : '—',
      change: simulation ? 'Latest simulation' : 'Run a simulation first',
      icon: Activity,
      color: 'text-blue-500',
    },
    {
      title: 'Throughput',
      value: simulation
        ? formatNumber(
            Math.round(
              simulation.performance.throughput_orders_per_second,
            ),
          )
        : '—',
      unit: 'orders/sec',
      change: simulation ? 'Backend measured' : 'Awaiting backend results',
      icon: Zap,
      color: 'text-emerald-500',
    },
    {
      title: 'Executed Trades',
      value: simulation
        ? formatNumber(simulation.summary.trade_count)
        : '—',
      change: simulation ? 'Latest simulation' : 'No simulation results',
      icon: ArrowLeftRight,
      color: 'text-violet-500',
    },
    {
      title: 'p99 Latency',
      value: simulation
        ? (simulation.performance.latency_p99_ns / 1000).toFixed(2)
        : '—',
      unit: simulation ? 'µs' : undefined,
      change: simulation ? 'Backend measured' : 'Awaiting backend results',
      icon: Clock3,
      color: 'text-amber-500',
    },
  ]

  const performanceData = simulation
    ? [
        {
          time: 'P50',
          latency: simulation.performance.latency_p50_ns / 1000,
        },
        {
          time: 'P95',
          latency: simulation.performance.latency_p95_ns / 1000,
        },
        {
          time: 'P99',
          latency: simulation.performance.latency_p99_ns / 1000,
        },
      ]
    : []

  const recentTrades = simulation
    ? [...simulation.trades].reverse().slice(0, 8)
    : []

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-bold text-[var(--foreground)]">
            Trading Overview
          </h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Your ChronosMatch system at a glance.
          </p>
        </div>

        <span
          className={`rounded-lg border px-3 py-2 text-xs font-medium ${
            simulation
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
              : 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400'
          }`}
        >
          {simulation ? 'BACKEND DATA' : 'AWAITING SIMULATION'}
        </span>
      </div>

      {/* No simulation message */}
      {!simulation && (
        <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
          <p className="text-sm text-[var(--muted)]">
            No simulation results are available yet. Run a simulation
            from the Simulator page to populate this dashboard.
          </p>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <div
              key={metric.title}
              className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 transition duration-200 hover:-translate-y-1 hover:shadow-lg"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-[var(--muted)]">
                  {metric.title}
                </p>

                <div className="rounded-xl bg-[var(--surface-secondary)] p-2">
                  <Icon size={20} className={metric.color} />
                </div>
              </div>

              <div className="mt-4">
                <h4 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
                  {metric.value}
                  {metric.unit && (
                    <span className="ml-2 text-xs font-medium text-[var(--muted)]">
                      {metric.unit}
                    </span>
                  )}
                </h4>

                <p className="mt-2 text-xs text-[var(--muted)]">
                  {metric.change}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Performance chart */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Latency Overview
            </h4>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Actual backend latency percentiles
            </p>
          </div>

          <span className="rounded-lg bg-[var(--surface-secondary)] px-3 py-2 text-xs text-[var(--muted)]">
            {simulation ? 'Latest session · µs' : 'No data'}
          </span>
        </div>

        <div className="h-64 w-full">
          {simulation ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <defs>
                  <linearGradient
                    id="overviewLatencyGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  stroke="var(--border)"
                  strokeDasharray="4 4"
                  vertical={false}
                />

                <XAxis
                  dataKey="time"
                  stroke="var(--muted)"
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                />

                <YAxis
                  stroke="var(--muted)"
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                  unit=" µs"
                />

                <Tooltip
                  contentStyle={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: '12px',
                    color: 'var(--foreground)',
                  }}
                  formatter={(value) => [
                    `${Number(value).toFixed(2)} µs`,
                    'Latency',
                  ]}
                />

                <Area
                  type="monotone"
                  dataKey="latency"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  fill="url(#overviewLatencyGradient)"
                  activeDot={{ r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-[var(--muted)]">
              Run a simulation to view latency metrics.
            </div>
          )}
        </div>
      </div>

      {/* Recent trades */}
      <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="flex items-center justify-between border-b border-[var(--border)] p-5">
          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Recent Trades
            </h4>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Latest backend-generated trade records
            </p>
          </div>

          <span className="text-xs text-[var(--muted)]">
            {recentTrades.length} records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-secondary)] text-xs text-[var(--muted)]">
              <tr>
                <th className="px-5 py-3">Maker Order</th>
                <th className="px-5 py-3">Taker Order</th>
                <th className="px-5 py-3">Symbol</th>
                <th className="px-5 py-3">Price (Ticks)</th>
                <th className="px-5 py-3">Quantity</th>
              </tr>
            </thead>

            <tbody>
              {recentTrades.map((trade, index) => (
                <tr
                  key={`${trade.maker_order_id}-${trade.taker_order_id}-${index}`}
                  className="border-t border-[var(--border)] hover:bg-[var(--surface-secondary)]"
                >
                  <td className="whitespace-nowrap px-5 py-4 font-medium text-[var(--foreground)]">
                    {trade.maker_order_id}
                  </td>

                  <td className="whitespace-nowrap px-5 py-4 font-medium text-[var(--foreground)]">
                    {trade.taker_order_id}
                  </td>

                  <td className="px-5 py-4 font-semibold text-[var(--foreground)]">
                    {trade.symbol}
                  </td>

                  <td className="px-5 py-4 text-[var(--foreground)]">
                    {trade.price_ticks}
                  </td>

                  <td className="px-5 py-4 text-[var(--foreground)]">
                    {trade.quantity}
                  </td>
                </tr>
              ))}

              {recentTrades.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-8 text-center text-sm text-[var(--muted)]"
                  >
                    No trades available. Run a simulation first.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {simulation && (
        <p className="text-xs text-[var(--muted)]">
          Data from the latest ChronosMatch backend simulation.
          These are simulated trades, not live exchange data.
        </p>
      )}
    </div>
  )
}
