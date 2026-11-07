
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
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

const metrics = [
  {
    title: 'Orders Processed',
    value: '100,000',
    change: 'Simulation example',
    icon: Activity,
    color: 'text-blue-500',
  },
  {
    title: 'Throughput',
    value: '54,297',
    unit: 'orders/sec',
    change: 'Pipeline benchmark',
    icon: Zap,
    color: 'text-emerald-500',
  },
  {
    title: 'Executed Trades',
    value: '72,000',
    change: 'Illustrative value',
    icon: ArrowLeftRight,
    color: 'text-violet-500',
  },
  {
    title: 'p99 Latency',
    value: '201.5',
    unit: 'µs',
    change: 'Pipeline benchmark',
    icon: Clock3,
    color: 'text-amber-500',
  },
]

const performanceData = [
  { time: '09:00', orders: 32000 },
  { time: '09:05', orders: 38500 },
  { time: '09:10', orders: 35000 },
  { time: '09:15', orders: 45000 },
  { time: '09:20', orders: 42000 },
  { time: '09:25', orders: 51000 },
  { time: '09:30', orders: 54297 },
]

const recentTrades = [
  { id: 'SIM-1042', symbol: 'AAPL', side: 'BUY', price: '100.25', quantity: 50 },
  { id: 'SIM-1043', symbol: 'MSFT', side: 'SELL', price: '400.50', quantity: 25 },
  { id: 'SIM-1044', symbol: 'GOOGL', side: 'BUY', price: '150.75', quantity: 80 },
  { id: 'SIM-1045', symbol: 'AAPL', side: 'SELL', price: '100.30', quantity: 40 },
]

export default function Overview() {
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

        <span className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-600 dark:text-amber-400">
          DEMO DATA · NOT LIVE
        </span>
      </div>

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
              Throughput Overview
            </h4>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Illustrative order-processing activity
            </p>
          </div>

          <span className="rounded-lg bg-[var(--surface-secondary)] px-3 py-2 text-xs text-[var(--muted)]">
            Sample session
          </span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={performanceData}>
              <defs>
                <linearGradient id="throughputGradient" x1="0" y1="0" x2="0" y2="1">
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
                  'Throughput',
                ]}
              />

              <Area
                type="monotone"
                dataKey="orders"
                stroke="#3B82F6"
                strokeWidth={3}
                fill="url(#throughputGradient)"
                activeDot={{ r: 5 }}
              />
            </AreaChart>
          </ResponsiveContainer>
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
              Illustrative trade records
            </p>
          </div>

          <span className="text-xs text-[var(--muted)]">
            4 records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-secondary)] text-xs text-[var(--muted)]">
              <tr>
                <th className="px-5 py-3">Trade ID</th>
                <th className="px-5 py-3">Symbol</th>
                <th className="px-5 py-3">Side</th>
                <th className="px-5 py-3">Price</th>
                <th className="px-5 py-3">Quantity</th>
              </tr>
            </thead>

            <tbody>
              {recentTrades.map((trade) => (
                <tr
                  key={trade.id}
                  className="border-t border-[var(--border)] hover:bg-[var(--surface-secondary)]"
                >
                  <td className="whitespace-nowrap px-5 py-4 font-medium text-[var(--foreground)]">
                    {trade.id}
                  </td>

                  <td className="px-5 py-4 font-semibold text-[var(--foreground)]">
                    {trade.symbol}
                  </td>

                  <td className="px-5 py-4">
                    <span className={`flex items-center gap-1 font-semibold ${
                      trade.side === 'BUY'
                        ? 'text-emerald-500'
                        : 'text-rose-500'
                    }`}>
                      {trade.side === 'BUY'
                        ? <ArrowUpRight size={15} />
                        : <ArrowDownRight size={15} />}
                      {trade.side}
                    </span>
                  </td>

                  <td className="px-5 py-4 text-[var(--foreground)]">
                    {trade.price}
                  </td>

                  <td className="px-5 py-4 text-[var(--foreground)]">
                    {trade.quantity}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
