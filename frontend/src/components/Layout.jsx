import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { NAV } from '../nav'
import { Badge } from './ui'

export default function Layout() {
  const [health, setHealth] = useState({ state: 'loading' })
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    let active = true
    const load = () =>
      api
        .get('/api/health')
        .then((r) => active && setHealth({ state: 'ok', data: r.data }))
        .catch(() => active && setHealth({ state: 'error' }))
    load()
    const timer = setInterval(load, 30000)
    return () => {
      active = false
      clearInterval(timer)
    }
  }, [])

  const mode = health.state === 'ok' ? health.data.default_execution_mode : null
  const currentPath = NAV.some((n) => n.to === location.pathname) ? location.pathname : '/'

  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 flex-col bg-[#0B1B3A] text-slate-300 md:flex">
        <div className="px-6 py-6">
          <div className="text-base font-semibold text-white">Hallucination</div>
          <div className="text-xs text-slate-400">Reliability Platform</div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  isActive ? 'bg-white/10 text-white' : 'hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <item.icon size={18} />
              <span className="flex-1">{item.label}</span>
              {!item.ready && (
                <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
                  Soon
                </span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="px-6 py-4 text-xs text-slate-400">MCA Major Project</div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-6 py-3">
          <select
            aria-label="Navigate"
            className="rounded-md border border-slate-300 px-2 py-2 text-sm md:hidden"
            value={currentPath}
            onChange={(e) => navigate(e.target.value)}
          >
            {NAV.map((item) => (
              <option key={item.to} value={item.to}>{item.label}</option>
            ))}
          </select>
          <div className="ml-auto flex items-center gap-3">
            {mode === 'demo' && <Badge tone="amber">Demo mode: simulated outputs</Badge>}
            {mode && mode !== 'demo' && <Badge tone="teal">{mode}</Badge>}
            {health.state === 'ok' && <Badge tone="green">Backend online</Badge>}
            {health.state === 'error' && <Badge tone="red">Backend offline</Badge>}
            {health.state === 'loading' && <Badge>Checking backend</Badge>}
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}