
import { useMemo, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  Search,
  ArrowLeftRight,
  Activity,
  TrendingUp,
} from 'lucide-react'

type Trade = {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  price: number
  quantity: number
  time: string
}

const demoTrades: Trade[] = [
  { id: 'SIM-1042', symbol: 'AAPL', side: 'BUY', price: 100.25, quantity: 50, time: '09:30:01' },
  { id: 'SIM-1043', symbol: 'MSFT', side: 'SELL', price: 400.50, quantity: 25, time: '09:30:04' },
  { id: 'SIM-1044', symbol: 'GOOGL', side: 'BUY', price: 150.75, quantity: 80, time: '09:30:08' },
  { id: 'SIM-1045', symbol: 'AAPL', side: 'SELL', price: 100.30, quantity: 40, time: '09:30:12' },
  { id: 'SIM-1046', symbol: 'MSFT', side: 'BUY', price: 400.60, quantity: 35, time: '09:30:16' },
  { id: 'SIM-1047', symbol: 'GOOGL', side: 'SELL', price: 150.90, quantity: 60, time: '09:30:20' },
  { id: 'SIM-1048', symbol: 'AAPL', side: 'BUY', price: 100.35, quantity: 70, time: '09:30:24' },
  { id: 'SIM-1049', symbol: 'MSFT', side: 'SELL', price: 400.70, quantity: 45, time: '09:30:28' },
  { id: 'SIM-1050', symbol: 'GOOGL', side: 'BUY', price: 150.85, quantity: 30, time: '09:30:32' },
  { id: 'SIM-1051', symbol: 'AAPL', side: 'SELL', price: 100.40, quantity: 55, time: '09:30:36' },
]

export default function TradeHistory() {
  const [search, setSearch] = useState('')
  const [symbol, setSymbol] = useState('ALL')
  const [side, setSide] = useState('ALL')

  const filteredTrades = useMemo(() => {
    return demoTrades.filter((trade) => {
      const matchesSearch =
        trade.id.toLowerCase().includes(search.toLowerCase()) ||
        trade.symbol.toLowerCase().includes(search.toLowerCase())

      const matchesSymbol =
        symbol === 'ALL' || trade.symbol === symbol

      const matchesSide =
        side === 'ALL' || trade.side === side

      return matchesSearch && matchesSymbol && matchesSide
    })
  }, [search, symbol, side])

  const buyCount = demoTrades.filter((trade) => trade.side === 'BUY').length
  const sellCount = demoTrades.filter((trade) => trade.side === 'SELL').length

  const totalQuantity = demoTrades.reduce(
    (total, trade) => total + trade.quantity,
    0,
  )

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <ArrowLeftRight size={22} className="text-blue-500" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">
              Trade History
            </h3>
          </div>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Review executed simulated trades.
          </p>
        </div>

        <span className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-600 dark:text-amber-400">
          DEMO DATA · NOT LIVE
        </span>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <Activity className="text-blue-500" size={21} />
          <p className="mt-3 text-sm text-[var(--muted)]">
            Total Executions
          </p>
          <h4 className="mt-1 text-2xl font-bold text-[var(--foreground)]">
            {demoTrades.length}
          </h4>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <ArrowUpRight className="text-emerald-500" size={21} />
          <p className="mt-3 text-sm text-[var(--muted)]">
            BUY Executions
          </p>
          <h4 className="mt-1 text-2xl font-bold text-emerald-500">
            {buyCount}
          </h4>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <TrendingUp className="text-rose-500" size={21} />
          <p className="mt-3 text-sm text-[var(--muted)]">
            SELL Executions
          </p>
          <h4 className="mt-1 text-2xl font-bold text-rose-500">
            {sellCount}
          </h4>
        </div>
      </div>

      {/* Quantity summary */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <p className="text-sm text-[var(--muted)]">
          Total executed quantity
        </p>
        <h4 className="mt-2 text-2xl font-bold text-[var(--foreground)]">
          {totalQuantity.toLocaleString()} units
        </h4>
      </div>

      {/* Trade table */}
      <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">

        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border)] p-5">
          <div>
            <h4 className="font-semibold text-[var(--foreground)]">
              Execution Records
            </h4>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Search and filter simulated executions.
            </p>
          </div>

          <span className="text-xs text-[var(--muted)]">
            {filteredTrades.length} records found
          </span>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 border-b border-[var(--border)] p-5 sm:flex-row">

          <div className="relative flex-1">
            <Search
              size={17}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
            />

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search trade ID or symbol..."
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] py-3 pl-10 pr-4 text-sm text-[var(--foreground)] outline-none focus:border-blue-500"
            />
          </div>

          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-3 text-sm text-[var(--foreground)] outline-none"
          >
            <option value="ALL">All Symbols</option>
            <option value="AAPL">AAPL</option>
            <option value="MSFT">MSFT</option>
            <option value="GOOGL">GOOGL</option>
          </select>

          <select
            value={side}
            onChange={(event) => setSide(event.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] px-4 py-3 text-sm text-[var(--foreground)] outline-none"
          >
            <option value="ALL">All Sides</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-secondary)] text-xs text-[var(--muted)]">
              <tr>
                <th className="px-5 py-4">TRADE ID</th>
                <th className="px-5 py-4">TIME</th>
                <th className="px-5 py-4">SYMBOL</th>
                <th className="px-5 py-4">SIDE</th>
                <th className="px-5 py-4">PRICE</th>
                <th className="px-5 py-4">QUANTITY</th>
              </tr>
            </thead>

            <tbody>
              {filteredTrades.map((trade) => (
                <tr
                  key={trade.id}
                  className="border-t border-[var(--border)] transition hover:bg-[var(--surface-secondary)]"
                >
                  <td className="whitespace-nowrap px-5 py-4 font-semibold text-[var(--foreground)]">
                    {trade.id}
                  </td>

                  <td className="whitespace-nowrap px-5 py-4 text-[var(--muted)]">
                    {trade.time}
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
                        ? <ArrowUpRight size={16} />
                        : <ArrowDownRight size={16} />}
                      {trade.side}
                    </span>
                  </td>

                  <td className="px-5 py-4 font-medium text-[var(--foreground)]">
                    {trade.price.toFixed(2)}
                  </td>

                  <td className="px-5 py-4 text-[var(--foreground)]">
                    {trade.quantity.toLocaleString()}
                  </td>
                </tr>
              ))}

              {filteredTrades.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-12 text-center text-[var(--muted)]"
                  >
                    No matching trade records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  )
}
