
import { useState } from 'react'
import { BookOpen, ChevronDown, Activity } from 'lucide-react'
import type { SimulationResponse } from '../../services/api'

export default function OrderBook() {
  const [simulation] = useState<SimulationResponse | null>(() => {
    try {
      const stored = sessionStorage.getItem(
        'chronosmatch_latest_simulation',
      )

      return stored ? (JSON.parse(stored) as SimulationResponse) : null
    } catch {
      sessionStorage.removeItem('chronosmatch_latest_simulation')
      return null
    }
  })

  const [symbol, setSymbol] = useState(
    () => simulation?.order_books[0]?.symbol ?? 'AAPL',
  )

  const book = simulation?.order_books.find(
    (item) => item.symbol === symbol,
  )

  const hasBid = book?.best_bid !== null && book?.best_bid !== undefined
  const hasAsk = book?.best_ask !== null && book?.best_ask !== undefined

  const spread =
    hasBid && hasAsk
      ? book.best_ask! - book.best_bid!
      : null

  const symbols = simulation?.order_books.map((item) => item.symbol) ?? []

  if (!simulation || !book) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <BookOpen size={22} className="text-blue-500" />
          <h3 className="text-xl font-bold text-[var(--foreground)]">
            Market Order Book
          </h3>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
          <Activity size={32} className="mx-auto text-[var(--muted)]" />
          <h4 className="mt-3 font-semibold text-[var(--foreground)]">
            No simulation data available
          </h4>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Run a simulation first to view actual backend order-book summaries.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BookOpen size={22} className="text-blue-500" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">
              Market Order Book
            </h3>
          </div>

          <p className="mt-1 text-sm text-[var(--muted)]">
            View simulated order-book summaries from the Python backend.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-500">
          <Activity size={15} />
          BACKEND DATA
        </div>
      </div>

      {/* Symbol selector */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <div>
          <p className="text-xs text-[var(--muted)]">
            Selected Instrument
          </p>

          <h4 className="mt-1 text-2xl font-bold text-[var(--foreground)]">
            {symbol}
          </h4>
        </div>

        <div className="relative">
          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            className="appearance-none rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] py-3 pl-4 pr-10 text-sm font-semibold text-[var(--foreground)] outline-none focus:border-blue-500"
          >
            {symbols.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <ChevronDown
            size={16}
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
          />
        </div>
      </div>

      {/* Market summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-emerald-500/20 bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Best Bid</p>

          <h4 className="mt-2 text-2xl font-bold text-emerald-500">
            {hasBid ? book.best_bid!.toLocaleString() : 'N/A'}
          </h4>

          <p className="mt-1 text-xs text-[var(--muted)]">
            Highest BUY price · ticks
          </p>
        </div>

        <div className="rounded-2xl border border-blue-500/20 bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Bid-Ask Spread</p>

          <h4 className="mt-2 text-2xl font-bold text-[var(--foreground)]">
            {spread !== null ? spread.toLocaleString() : 'N/A'}
          </h4>

          <p className="mt-1 text-xs text-[var(--muted)]">
            Difference in price ticks
          </p>
        </div>

        <div className="rounded-2xl border border-rose-500/20 bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Best Ask</p>

          <h4 className="mt-2 text-2xl font-bold text-rose-500">
            {hasAsk ? book.best_ask!.toLocaleString() : 'N/A'}
          </h4>

          <p className="mt-1 text-xs text-[var(--muted)]">
            Lowest SELL price · ticks
          </p>
        </div>
      </div>

      {/* Order book summary */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-[var(--foreground)]">
                Active Orders
              </h4>

              <p className="mt-1 text-xs text-[var(--muted)]">
                Total active orders for {symbol}
              </p>
            </div>

            <span className="rounded-lg bg-blue-500/10 px-3 py-2 text-xs font-semibold text-blue-500">
              LIVE SIMULATION
            </span>
          </div>

          <h3 className="mt-5 text-4xl font-bold text-[var(--foreground)]">
            {book.active_order_count.toLocaleString()}
          </h3>

          <p className="mt-2 text-xs text-[var(--muted)]">
            Reported by the backend matching engine
          </p>
        </div>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <h4 className="font-semibold text-[var(--foreground)]">
            Market Snapshot
          </h4>

          <p className="mt-1 text-xs text-[var(--muted)]">
            Latest available order-book information
          </p>

          <div className="mt-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--muted)]">Instrument</span>
              <span className="font-semibold text-[var(--foreground)]">
                {book.symbol}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--muted)]">Best Bid</span>
              <span className="font-semibold text-emerald-500">
                {hasBid ? book.best_bid!.toLocaleString() : 'N/A'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--muted)]">Best Ask</span>
              <span className="font-semibold text-rose-500">
                {hasAsk ? book.best_ask!.toLocaleString() : 'N/A'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--muted)]">
                Active Orders
              </span>
              <span className="font-semibold text-[var(--foreground)]">
                {book.active_order_count.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Data limitation notice */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <h4 className="font-semibold text-[var(--foreground)]">
          Order Book Depth
        </h4>

        <p className="mt-2 text-sm text-[var(--muted)]">
          The current API provides the best bid, best ask and active order
          count. Individual price levels, bid/ask quantities and cumulative
          liquidity are not yet exposed by the backend.
        </p>
      </div>
    </div>
  )
}
