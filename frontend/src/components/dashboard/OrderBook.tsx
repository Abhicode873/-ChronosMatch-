
import { useState } from 'react'
import { BookOpen, ChevronDown, Activity } from 'lucide-react'

type OrderLevel = {
  price: number
  quantity: number
}

const marketData: Record<
  string,
  { bids: OrderLevel[]; asks: OrderLevel[] }
> = {
  AAPL: {
    bids: [
      { price: 100.24, quantity: 450 },
      { price: 100.23, quantity: 380 },
      { price: 100.22, quantity: 620 },
      { price: 100.21, quantity: 290 },
      { price: 100.20, quantity: 510 },
    ],
    asks: [
      { price: 100.26, quantity: 320 },
      { price: 100.27, quantity: 560 },
      { price: 100.28, quantity: 410 },
      { price: 100.29, quantity: 700 },
      { price: 100.30, quantity: 350 },
    ],
  },
  MSFT: {
    bids: [
      { price: 400.45, quantity: 320 },
      { price: 400.40, quantity: 450 },
      { price: 400.35, quantity: 280 },
      { price: 400.30, quantity: 610 },
      { price: 400.25, quantity: 390 },
    ],
    asks: [
      { price: 400.55, quantity: 420 },
      { price: 400.60, quantity: 350 },
      { price: 400.65, quantity: 580 },
      { price: 400.70, quantity: 300 },
      { price: 400.75, quantity: 490 },
    ],
  },
  GOOGL: {
    bids: [
      { price: 150.70, quantity: 500 },
      { price: 150.65, quantity: 340 },
      { price: 150.60, quantity: 620 },
      { price: 150.55, quantity: 410 },
      { price: 150.50, quantity: 280 },
    ],
    asks: [
      { price: 150.80, quantity: 390 },
      { price: 150.85, quantity: 520 },
      { price: 150.90, quantity: 300 },
      { price: 150.95, quantity: 650 },
      { price: 151.00, quantity: 440 },
    ],
  },
}

export default function OrderBook() {
  const [symbol, setSymbol] = useState('AAPL')

  const { bids, asks } = marketData[symbol]

  const bestBid = Math.max(...bids.map((level) => level.price))
  const bestAsk = Math.min(...asks.map((level) => level.price))
  const spread = bestAsk - bestBid

  const bidTotal = bids.reduce((sum, level) => sum + level.quantity, 0)
  const askTotal = asks.reduce((sum, level) => sum + level.quantity, 0)

  const maxQuantity = Math.max(
    ...bids.map((level) => level.quantity),
    ...asks.map((level) => level.quantity),
  )

  const renderLevels = (
    levels: OrderLevel[],
    side: 'BUY' | 'SELL',
  ) => {
    let cumulative = 0

    return levels.map((level) => {
      cumulative += level.quantity

      const percentage = (level.quantity / maxQuantity) * 100

      return (
        <div
          key={level.price}
          className="relative grid grid-cols-3 items-center border-b border-[var(--border)] px-3 py-3 text-xs sm:text-sm"
        >
          <div
            className={`absolute inset-y-0 ${
              side === 'BUY'
                ? 'right-0 bg-emerald-500/10'
                : 'left-0 bg-rose-500/10'
            }`}
            style={{ width: `${percentage}%` }}
          />

          <span
            className={`relative z-10 font-semibold ${
              side === 'BUY'
                ? 'text-emerald-500'
                : 'text-rose-500'
            }`}
          >
            {level.price.toFixed(2)}
          </span>

          <span className="relative z-10 text-right text-[var(--foreground)]">
            {level.quantity.toLocaleString()}
          </span>

          <span className="relative z-10 text-right text-[var(--muted)]">
            {cumulative.toLocaleString()}
          </span>
        </div>
      )
    })
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
            View simulated buy and sell liquidity.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-600 dark:text-amber-400">
          <Activity size={15} />
          DEMO DATA · NOT LIVE
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
            <option value="AAPL">AAPL</option>
            <option value="MSFT">MSFT</option>
            <option value="GOOGL">GOOGL</option>
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
            {bestBid.toFixed(2)}
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Highest BUY price
          </p>
        </div>

        <div className="rounded-2xl border border-blue-500/20 bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Bid-Ask Spread</p>
          <h4 className="mt-2 text-2xl font-bold text-[var(--foreground)]">
            {spread.toFixed(2)}
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Absolute price difference
          </p>
        </div>

        <div className="rounded-2xl border border-rose-500/20 bg-[var(--surface)] p-5">
          <p className="text-xs text-[var(--muted)]">Best Ask</p>
          <h4 className="mt-2 text-2xl font-bold text-rose-500">
            {bestAsk.toFixed(2)}
          </h4>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Lowest SELL price
          </p>
        </div>
      </div>

      {/* Order book tables */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">

        {/* Bids */}
        <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="flex items-center justify-between border-b border-[var(--border)] p-5">
            <div>
              <h4 className="font-semibold text-emerald-500">
                BUY ORDERS · BIDS
              </h4>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {bidTotal.toLocaleString()} total quantity
              </p>
            </div>

            <span className="rounded-lg bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-500">
              BUY
            </span>
          </div>

          <div className="grid grid-cols-3 bg-[var(--surface-secondary)] px-3 py-3 text-xs font-medium text-[var(--muted)]">
            <span>PRICE</span>
            <span className="text-right">QUANTITY</span>
            <span className="text-right">TOTAL</span>
          </div>

          {renderLevels(bids, 'BUY')}
        </div>

        {/* Asks */}
        <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="flex items-center justify-between border-b border-[var(--border)] p-5">
            <div>
              <h4 className="font-semibold text-rose-500">
                SELL ORDERS · ASKS
              </h4>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {askTotal.toLocaleString()} total quantity
              </p>
            </div>

            <span className="rounded-lg bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-500">
              SELL
            </span>
          </div>

          <div className="grid grid-cols-3 bg-[var(--surface-secondary)] px-3 py-3 text-xs font-medium text-[var(--muted)]">
            <span>PRICE</span>
            <span className="text-right">QUANTITY</span>
            <span className="text-right">TOTAL</span>
          </div>

          {renderLevels(asks, 'SELL')}
        </div>
      </div>

      {/* Liquidity distribution */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
        <h4 className="font-semibold text-[var(--foreground)]">
          Order Book Liquidity
        </h4>

        <p className="mt-1 text-xs text-[var(--muted)]">
          Quantity distribution across displayed price levels.
        </p>

        <div className="mt-5 flex h-4 overflow-hidden rounded-full bg-[var(--surface-secondary)]">
          <div
            className="bg-emerald-500 transition-all"
            style={{
              width: `${(bidTotal / (bidTotal + askTotal)) * 100}%`,
            }}
          />

          <div
            className="bg-rose-500 transition-all"
            style={{
              width: `${(askTotal / (bidTotal + askTotal)) * 100}%`,
            }}
          />
        </div>

        <div className="mt-4 flex flex-wrap justify-between gap-3 text-xs">
          <span className="text-emerald-500">
            BUY: {bidTotal.toLocaleString()} units
          </span>

          <span className="text-rose-500">
            SELL: {askTotal.toLocaleString()} units
          </span>
        </div>
      </div>

    </div>
  )
}
