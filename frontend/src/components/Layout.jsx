import { useEffect, useState } from 'react'
import {
  NavLink,
  Outlet,
  useLocation,
} from 'react-router-dom'

import {
  Activity,
  BrainCircuit,
  ChevronRight,
  Menu,
  ShieldCheck,
  X,
} from 'lucide-react'

import { api } from '../api/client'
import { NAV } from '../nav'
import { Badge } from './ui'

export default function Layout() {
  const [health, setHealth] = useState({ state: 'loading' })
  const [mobileOpen, setMobileOpen] = useState(false)

  const location = useLocation()

  useEffect(() => {
    let active = true

    const load = () => {
      api.get('/api/health')
        .then((r) => {
          if (active) {
            setHealth({ state: 'ok', data: r.data })
          }
        })
        .catch(() => {
          if (active) {
            setHealth({ state: 'error' })
          }
        })
    }

    load()

    const timer = setInterval(load, 30000)

    return () => {
      active = false
      clearInterval(timer)
    }
  }, [])

  const currentPage =
    NAV.find((item) => item.to === location.pathname) || NAV[0]

  const renderSidebarContent = () => (
    <>
      <div className="flex items-center gap-3 border-b border-white/10 px-6 py-6">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500 text-white shadow-lg shadow-blue-900/30">
          <BrainCircuit size={25} />
        </div>

        <div>
          <h1 className="text-sm font-bold tracking-wide text-white">
            HALLUCINATION
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Intelligence Platform
          </p>
        </div>
      </div>

      <div className="px-5 pb-2 pt-7">
        <p className="text-[10px] font-bold uppercase tracking-[2px] text-slate-500">
          Workspace
        </p>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-950/30'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <item.icon size={19} />

            <span className="flex-1 font-medium">
              {item.label}
            </span>

            {!item.ready && (
              <span className="rounded-md border border-amber-400/20 bg-amber-400/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-amber-300">
                Pending
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-xl bg-white/5 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <ShieldCheck size={16} className="text-teal-400" />
            AI Reliability System
          </div>

          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            Intelligent evaluation and reliability analytics for AI-generated responses.
          </p>
        </div>

        <p className="mt-4 text-center text-[10px] text-slate-500">
          MCA Data Science Project
        </p>
      </div>
    </>
  )

  return (
    <div className="flex min-h-screen bg-[#F5F7FB]">

      {/* Desktop Sidebar */}
      <aside className="hidden w-[265px] shrink-0 flex-col bg-[#101B35] text-white md:flex">
        {renderSidebarContent()}
      </aside>

      {/* Mobile Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-slate-950/60"
            onClick={() => setMobileOpen(false)}
          />

          <aside className="absolute inset-y-0 left-0 flex w-[280px] flex-col bg-[#101B35]">
            <div className="flex justify-end p-3">
              <button
                onClick={() => setMobileOpen(false)}
                className="rounded-lg p-2 text-white hover:bg-white/10"
              >
                <X size={20} />
              </button>
            </div>

            {renderSidebarContent()}
          </aside>
        </div>
      )}

      {/* Main Workspace */}
      <div className="flex min-w-0 flex-1 flex-col">

        {/* Header */}
        <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur-xl md:px-8">

          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="rounded-lg border border-slate-200 p-2 text-slate-600 md:hidden"
            >
              <Menu size={20} />
            </button>

            <div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                Workspace
                <ChevronRight size={13} />
                <span className="font-medium text-slate-600">
                  {currentPage.label}
                </span>
              </div>

              <h2 className="mt-1 text-lg font-bold text-slate-900">
                {currentPage.label}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">

            <div className="hidden items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 sm:flex">
              <Activity size={15} className="text-slate-500" />
              <span className="text-xs font-medium text-slate-600">
                System Status
              </span>
            </div>

            {health.state === 'ok' && (
              <Badge tone="green">Backend Online</Badge>
            )}

            {health.state === 'error' && (
              <Badge tone="red">Backend Offline</Badge>
            )}

            {health.state === 'loading' && (
              <Badge>Connecting</Badge>
            )}

          </div>
        </header>

        {/* Page Content */}
        <main className="w-full flex-1 overflow-y-auto p-5 md:p-8">
          <div className="mx-auto max-w-[1600px]">
            <Outlet />
          </div>
        </main>

      </div>
    </div>
  )
}