
import { Bell, Moon, Sun,  } from 'lucide-react'

interface TopbarProps {
  title: string
  description: string
  theme: 'dark' | 'light'
  onThemeToggle: () => void
}

export default function Topbar({
  title,
  description,
  theme,
  onThemeToggle,
}: TopbarProps) {
  return (
    <header className="flex min-h-[88px] items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-8 py-4">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-[var(--foreground)]">
          {title}
        </h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {description}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 rounded-full border border-[var(--border)] px-3 py-2 sm:flex">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="text-xs font-medium text-[var(--foreground)]">
            Simulation Mode
          </span>
        </div>

        <button
          onClick={onThemeToggle}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title="Toggle theme"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border)] text-[var(--muted)] transition hover:bg-[var(--surface-secondary)] hover:text-[var(--foreground)]"
        >
          {theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
        </button>

        <button
          aria-label="Notifications"
          title="Notifications"
          className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border)] text-[var(--muted)] transition hover:bg-[var(--surface-secondary)]"
        >
          <Bell size={19} />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-blue-500" />
        </button>

        <div className="flex items-center gap-3 border-l border-[var(--border)] pl-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
            CM
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold text-[var(--foreground)]">
              ChronosMatch
            </p>
            <p className="text-xs text-[var(--muted)]">
              Administrator
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}

