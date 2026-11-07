import { lazy, Suspense, useState } from 'react'
import Sidebar, {
  type DashboardPage,
} from './components/layout/Sidebar'
import Topbar from './components/layout/Topbar'
import { useTheme } from './hooks/useTheme'

const Overview = lazy(() => import('./components/dashboard/Overview'))
const OrderBook = lazy(() => import('./components/dashboard/OrderBook'))
const TradeHistory = lazy(() => import('./components/dashboard/TradeHistory'))
const Performance = lazy(() => import('./components/dashboard/Performance'))
const Simulator = lazy(() => import('./components/dashboard/Simulator'))

const pageDetails: Record<
  DashboardPage,
  { title: string; description: string }
> = {
  overview: {
    title: 'Overview',
    description: 'Monitor your ChronosMatch trading system.',
  },
  'order-book': {
    title: 'Order Book',
    description: 'Explore simulated bids, asks and market depth.',
  },
  trades: {
    title: 'Trade History',
    description: 'Review executed orders and trade activity.',
  },
  performance: {
    title: 'Performance',
    description: 'Analyze matching engine and pipeline performance.',
  },
  simulator: {
    title: 'Market Simulator',
    description: 'Configure and monitor simulated market activity.',
  },
}

export default function App() {
  const [activePage, setActivePage] =
    useState<DashboardPage>('overview')

  const { theme, toggleTheme } = useTheme()

  const currentPage = pageDetails[activePage]

  return (
    <div className="flex min-h-screen bg-[var(--background)]">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
      />

      <main className="min-w-0 flex-1">
        <Topbar
          title={currentPage.title}
          description={currentPage.description}
          theme={theme}
          onThemeToggle={toggleTheme}
        />

        <section className="p-8">
          <Suspense
            fallback={
              <div className="flex min-h-64 items-center justify-center text-[var(--muted)]">
                Loading dashboard...
              </div>
            }
          >
            {activePage === 'overview' && <Overview />}
            {activePage === 'order-book' && <OrderBook />}
            {activePage === 'trades' && <TradeHistory />}
            {activePage === 'performance' && <Performance />}
            {activePage === 'simulator' && <Simulator />}
          </Suspense>
        </section>
      </main>
    </div>
  )
}