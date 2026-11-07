
import {
  Activity,
  ArrowLeftRight,
  BookOpen,
  ChartNoAxesCombined,
  LayoutDashboard,
  Settings2,
  Zap,
} from 'lucide-react'

export type DashboardPage =
  | 'overview'
  | 'order-book'
  | 'trades'
  | 'performance'
  | 'simulator'

interface SidebarProps {
  activePage: DashboardPage
  onNavigate: (page: DashboardPage) => void
}

const navigation = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'order-book', label: 'Order Book', icon: BookOpen },
  { id: 'trades', label: 'Trade History', icon: ArrowLeftRight },
  { id: 'performance', label: 'Performance', icon: ChartNoAxesCombined },
  { id: 'simulator', label: 'Simulator', icon: Activity },
] as const

export default function Sidebar({
  activePage,
  onNavigate,
}: SidebarProps) {
  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)] p-5">

      {/* Brand */}
      <div className="mb-10 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-600/20">
          <Zap size={23} fill="currentColor" />
        </div>

        <div>
          <h1 className="text-lg font-bold tracking-tight text-[var(--foreground)]">
            ChronosMatch
          </h1>
          <p className="text-xs text-[var(--muted)]">
            Trading Intelligence
          </p>
        </div>
      </div>

      {/* Navigation */}
      <div className="mb-3 px-3 text-xs font-semibold uppercase tracking-widest text-[var(--muted)]">
        Workspace
      </div>

      <nav className="flex flex-1 flex-col gap-2">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = activePage === item.id

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-[var(--muted)] hover:bg-[var(--surface-secondary)] hover:text-[var(--foreground)]'
              }`}
            >
              <Icon size={19} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--border)] pt-4">
        <button
          className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-[var(--muted)] transition hover:bg-[var(--surface-secondary)] hover:text-[var(--foreground)]"
          onClick={() => alert('Settings will be available in a future update.')}
        >
          <Settings2 size={19} />
          Settings
        </button>

        <div className="mt-4 rounded-xl bg-[var(--surface-secondary)] p-3">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-xs font-medium text-[var(--foreground)]">
              Simulation Environment
            </span>
          </div>
          <p className="mt-1 pl-4 text-xs text-[var(--muted)]">
            Backend integration pending
          </p>
        </div>
      </div>
    </aside>
  )
}
