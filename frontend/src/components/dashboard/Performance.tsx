
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

const throughputData = [
  { metric: 'Throughput', Python: 697693, Cython: 1550818 },
]

const latencyData = [
  { percentile: 'p50', Python: 1.5, Cython: 0.6 },
  { percentile: 'p95', Python: 2.8, Cython: 1.1 },
  { percentile: 'p99', Python: 3.4, Cython: 1.5 },
]

const benchmarks = [
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
]

export default function Performance() {
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
            Analyze matching engine performance and latency.
          </p>
        </div>

        <span className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-600 dark:text-amber-400">
          RECORDED BENCHMARK · NOT LIVE
        </span>
      </div>

      {/* Benchmark information */}
      <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
        <p className="text-sm font-semibold text-[var(--foreground)]">
          Benchmark configuration
        </p>

        <div className="mt-3 flex flex-wrap gap-x-8 gap-y-2 text-xs text-[var(--muted)]">
          <span>Workload: 100,000 orders</span>
          <span>Trials: 5</span>
          <span>Warm-up: 2,000 orders</span>
          <span>Trades: 50,000</span>
        </div>

        <p className="mt-3 text-xs text-[var(--muted)]">
          Local synthetic matching-engine benchmark.
          Results depend on hardware and workload.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {benchmarks.map((item) => {
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

      {/* Throughput comparison */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
        <div className="mb-6">
          <h4 className="font-semibold text-[var(--foreground)]">
            Matching Engine Throughput
          </h4>

          <p className="mt-1 text-xs text-[var(--muted)]">
            Median throughput across five benchmark trials.
          </p>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={throughputData}>
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

      {/* Latency comparison */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6">
        <div className="mb-6 flex items-center gap-2">
          <Clock3 size={20} className="text-blue-500" />

          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Latency Percentiles
            </h4>

            <p className="mt-1 text-xs text-[var(--muted)]">
              Python vs Cython · Microseconds (µs)
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
                  `${Number(value).toFixed(1)} µs`,
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

      {/* Interpretation */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <h4 className="font-semibold text-[var(--foreground)]">
          Benchmark Interpretation
        </h4>

        <ul className="mt-4 space-y-3 text-sm text-[var(--muted)]">
          <li>
            • Cython achieved approximately 2.22× the median throughput
            of the Python reference engine in this workload.
          </li>

          <li>
            • Cython recorded lower p50, p95 and p99 latency.
          </li>

          <li>
            • Both engines produced the same 50,000 trades.
          </li>

          <li>
            • These results describe a synthetic alternating
            buy/sell workload, not production exchange performance.
          </li>
        </ul>
      </div>

    </div>
  )
}
