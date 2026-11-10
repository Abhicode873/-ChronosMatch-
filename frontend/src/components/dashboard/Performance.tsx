
import { useState } from 'react'
import {
  Activity,
  Zap,
  Clock3,
  Gauge,
  Cpu,
} from 'lucide-react'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { SimulationResponse } from '../../services/api'

const STORAGE_KEY = 'chronosmatch_latest_simulation'

function loadLatestSimulation(): SimulationResponse | null {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    return stored ? (JSON.parse(stored) as SimulationResponse) : null
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

// Historical Python vs Cython benchmark.
const throughputBenchmark = [
  { metric: 'Throughput', Python: 697693, Cython: 1550818 },
]

const latencyBenchmark = [
  { percentile: 'P50', Python: 1.5, Cython: 0.6 },
  { percentile: 'P95', Python: 2.8, Cython: 1.1 },
  { percentile: 'P99', Python: 3.4, Cython: 1.5 },
]

const formatNumber = (value: number) =>
  value.toLocaleString('en-US')

const formatLatency = (nanoseconds: number) =>
  (nanoseconds / 1000).toFixed(2)

export default function Performance() {
  const [simulation] = useState<SimulationResponse | null>(
    loadLatestSimulation,
  )

  if (!simulation) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Gauge size={22} className="text-blue-500" />
          <h3 className="text-xl font-bold text-[var(--foreground)]">
            Performance Analytics
          </h3>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
          <Activity size={32} className="mx-auto text-[var(--muted)]" />

          <h4 className="mt-3 font-semibold text-[var(--foreground)]">
            No performance data available
          </h4>

          <p className="mt-2 text-sm text-[var(--muted)]">
            Run a simulation first to view actual backend performance metrics.
          </p>
        </div>
      </div>
    )
  }

  const performance = simulation.performance

  const currentMetrics = [
    {
      label: 'Orders Processed',
      value: formatNumber(performance.orders_processed),
      unit: 'backend processed orders',
      icon: Activity,
      color: 'text-blue-500',
    },
    {
      label: 'Throughput',
      value: formatNumber(
        Math.round(performance.throughput_orders_per_second),
      ),
      unit: 'orders/sec',
      icon: Zap,
      color: 'text-emerald-500',
    },
    {
      label: 'P99 Latency',
      value: formatLatency(performance.latency_p99_ns),
      unit: 'µs',
      icon: Clock3,
      color: 'text-amber-500',
    },
    {
      label: 'Execution Time',
      value: (performance.elapsed_ns / 1_000_000).toFixed(2),
      unit: 'milliseconds',
      icon: Gauge,
      color: 'text-violet-500',
    },
  ]

  const latencyData = [
    {
      percentile: 'P50',
      latency: performance.latency_p50_ns / 1000,
    },
    {
      percentile: 'P95',
      latency: performance.latency_p95_ns / 1000,
    },
    {
      percentile: 'P99',
      latency: performance.latency_p99_ns / 1000,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Heading */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Gauge size={22} className="text-blue-500" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">
              Performance Analytics
            </h3>
          </div>

          <p className="mt-1 text-sm text-[var(--muted)]">
            Analyze actual simulation throughput and latency.
          </p>
        </div>

        <span className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-500">
          BACKEND DATA
        </span>
      </div>

      {/* Current simulation metrics */}
      <div>
        <div className="mb-4">
          <h4 className="font-semibold text-[var(--foreground)]">
            Latest Simulation Performance
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Measurements returned by the FastAPI backend.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {currentMetrics.map((item) => {
            const Icon = item.icon

            return (
              <div
                key={item.label}
                className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-[var(--muted)]">
                    {item.label}
                  </p>
                  <Icon size={20} className={item.color} />
                </div>

                <h4 className="mt-4 text-2xl font-bold text-[var(--foreground)]">
                  {item.value}
                </h4>

                <p className="mt-2 text-xs text-[var(--muted)]">
                  {item.unit}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Additional metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-sm text-[var(--muted)]">Executed Trades</p>
          <h4 className="mt-2 text-2xl font-bold text-[var(--foreground)]">
            {formatNumber(performance.trades_executed)}
          </h4>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-sm text-[var(--muted)]">Minimum Latency</p>
          <h4 className="mt-2 text-2xl font-bold text-emerald-500">
            {formatLatency(performance.latency_min_ns)} µs
          </h4>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <p className="text-sm text-[var(--muted)]">Maximum Latency</p>
          <h4 className="mt-2 text-2xl font-bold text-rose-500">
            {formatLatency(performance.latency_max_ns)} µs
          </h4>
        </div>
      </div>

      {/* Current simulation latency */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
        <div className="mb-6 flex items-center gap-2">
          <Clock3 size={20} className="text-blue-500" />

          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Simulation Latency Percentiles
            </h4>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Actual backend latency · Microseconds (µs)
            </p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={latencyData}>
              <CartesianGrid
                stroke="var(--border)"
                strokeDasharray="4 4"
                vertical={false}
              />

              <XAxis
                dataKey="percentile"
                stroke="var(--muted)"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                stroke="var(--muted)"
                tickLine={false}
                axisLine={false}
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

              <Bar
                dataKey="latency"
                name="Latency"
                fill="#3B82F6"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Historical engine benchmarks */}
      <div>
        <div className="mb-4">
          <h4 className="font-semibold text-[var(--foreground)]">
            Historical Engine Benchmark
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Recorded Python reference engine vs Cython engine results.
            Separate from the latest simulation.
          </p>
        </div>

        <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
          <div className="flex flex-wrap gap-x-8 gap-y-2 text-xs text-[var(--muted)]">
            <span>Workload: 100,000 orders</span>
            <span>Trials: 5</span>
            <span>Warm-up: 2,000 orders</span>
            <span>Trades: 50,000</span>
          </div>

          <p className="mt-3 text-xs text-[var(--muted)]">
            Local synthetic matching-engine benchmark. Results depend on
            hardware and workload and do not represent production exchange
            performance.
          </p>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            {
              label: 'Python Engine',
              value: '697,693',
              unit: 'orders/sec',
              icon: Cpu,
              color: 'text-blue-500',
            },
            {
              label: 'Cython Engine',
              value: '1,550,818',
              unit: 'orders/sec',
              icon: Zap,
              color: 'text-emerald-500',
            },
            {
              label: 'Performance Ratio',
              value: '2.22×',
              unit: 'Cython advantage',
              icon: Gauge,
              color: 'text-violet-500',
            },
            {
              label: 'Orders Tested',
              value: '100,000',
              unit: 'synthetic workload',
              icon: Activity,
              color: 'text-amber-500',
            },
          ].map((item) => {
            const Icon = item.icon

            return (
              <div
                key={item.label}
                className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-[var(--muted)]">
                    {item.label}
                  </p>
                  <Icon size={20} className={item.color} />
                </div>

                <h4 className="mt-4 text-2xl font-bold text-[var(--foreground)]">
                  {item.value}
                </h4>

                <p className="mt-2 text-xs text-[var(--muted)]">
                  {item.unit}
                </p>
              </div>
            )
          })}
        </div>

        {/* Historical throughput chart */}
        <div className="mt-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
          <h4 className="font-semibold text-[var(--foreground)]">
            Historical Matching Engine Throughput
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Recorded median throughput across five benchmark trials.
          </p>

          <div className="mt-5 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={throughputBenchmark}>
                <CartesianGrid
                  stroke="var(--border)"
                  strokeDasharray="4 4"
                  vertical={false}
                />

                <XAxis
                  dataKey="metric"
                  stroke="var(--muted)"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  stroke="var(--muted)"
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) =>
                    `${(Number(value) / 1000000).toFixed(1)}M`
                  }
                />

                <Tooltip
                  contentStyle={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: '12px',
                    color: 'var(--foreground)',
                  }}
                  formatter={(value) => [
                    `${Number(value).toLocaleString()} orders/sec`,
                  ]}
                />

                <Legend />

                <Bar
                  dataKey="Python"
                  fill="#3B82F6"
                  radius={[6, 6, 0, 0]}
                />

                <Bar
                  dataKey="Cython"
                  fill="#10B981"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Historical latency chart */}
        <div className="mt-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
          <h4 className="font-semibold text-[var(--foreground)]">
            Historical Engine Latency Comparison
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Recorded Python vs Cython latency · Microseconds (µs).
          </p>

          <div className="mt-5 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyBenchmark}>
                <CartesianGrid
                  stroke="var(--border)"
                  strokeDasharray="4 4"
                  vertical={false}
                />

                <XAxis
                  dataKey="percentile"
                  stroke="var(--muted)"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  stroke="var(--muted)"
                  tickLine={false}
                  axisLine={false}
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
                  ]}
                />

                <Legend />

                <Bar
                  dataKey="Python"
                  fill="#3B82F6"
                  radius={[6, 6, 0, 0]}
                />

                <Bar
                  dataKey="Cython"
                  fill="#10B981"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Interpretation */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <h4 className="font-semibold text-[var(--foreground)]">
          Performance Interpretation
        </h4>

        <ul className="mt-4 space-y-3 text-sm text-[var(--muted)]">
          <li>
            • Current throughput and latency measurements come from the
            latest backend simulation.
          </li>
          <li>
            • P50, P95 and P99 represent different points in the measured
            latency distribution.
          </li>
          <li>
            • Historical benchmark results show the Cython engine achieved
            approximately 2.22× the Python reference engine throughput
            in the recorded workload.
          </li>
          <li>
            • Historical benchmark results and current pipeline measurements
            are separate experiments and should not be directly compared.
          </li>
        </ul>
      </div>
    </div>
  )
}
