import { useEffect, useState } from 'react'
import { api, errorMessage } from '../api/client'
import {
  Activity,
  Database,
  Server,
  Layers3,
  RefreshCw,
  BrainCircuit,
  ShieldCheck,
  ArrowUpRight,
  CheckCircle2,
  HardDrive,
  Table2,
  Zap,
  CircleDot,
  Clock3
} from 'lucide-react'

function MetricCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <div className="group rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
      <div className="flex items-center justify-between">
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}>
          <Icon size={22} />
        </div>
        <ArrowUpRight size={18} className="text-slate-300 transition group-hover:text-blue-600" />
      </div>

      <p className="mt-5 text-sm font-medium text-slate-500">{title}</p>

      <h2 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
        {value}
      </h2>

      <p className="mt-2 text-xs text-slate-400">{subtitle}</p>
    </div>
  )
}

function SectionTitle({ icon: Icon, title, subtitle }) {
  return (
    <div className="mb-5 flex items-center gap-3">
      <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
        <Icon size={20} />
      </div>
      <div>
        <h2 className="font-bold text-slate-900">{title}</h2>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>
    </div>
  )
}

export default function Overview() {
  const [state, setState] = useState({ status: 'loading' })

  const load = async () => {
    setState({ status: 'loading' })

    try {
      const [health, db] = await Promise.all([
        api.get('/api/health'),
        api.get('/api/db-info')
      ])

      setState({
        status: 'ok',
        health: health.data,
        db: db.data
      })
    } catch (error) {
      setState({
        status: 'error',
        message: errorMessage(error)
      })
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (state.status === 'loading') {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <RefreshCw className="mx-auto animate-spin text-blue-600" size={30} />
          <p className="mt-4 text-sm text-slate-500">
            Loading intelligence dashboard...
          </p>
        </div>
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <div className="rounded-2xl border border-red-200 bg-white p-8">
        <h2 className="font-bold text-red-700">Dashboard connection failed</h2>
        <p className="mt-2 text-sm text-slate-500">{state.message}</p>
        <button
          onClick={load}
          className="mt-5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  const { health, db } = state
  const tables = Array.isArray(db?.tables) ? db.tables : []
  const warehouseTables = tables.filter(name => name.startsWith('dw_'))
  const applicationTables = tables.filter(name => !name.startsWith('dw_'))

  return (
    <div className="mx-auto max-w-[1600px] space-y-7 pb-10">

      {/* Heading */}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[2px] text-blue-600">
            <Activity size={15} />
            AI Intelligence Workspace
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Overview
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Your central workspace for AI reliability and system monitoring.
          </p>
        </div>

        <button
          onClick={load}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-700"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Hero */}

      <section className="relative overflow-hidden rounded-2xl bg-[#102344] p-7 text-white shadow-lg md:p-9">
        <div className="absolute -right-16 -top-24 h-80 w-80 rounded-full border-[45px] border-white/[0.04]" />
        <div className="absolute -bottom-40 right-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />

        <div className="relative z-10 flex flex-wrap items-center justify-between gap-8">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[2px] text-blue-300">
              <BrainCircuit size={17} />
              AI Reliability Platform
            </div>

            <h2 className="mt-5 text-2xl font-bold leading-tight md:text-3xl">
              Understand AI.
              <br />
              Measure Reliability.
            </h2>

            <p className="mt-4 max-w-xl text-sm leading-7 text-slate-300">
              Investigate hallucinations, evaluate generated responses,
              and understand the reliability of AI systems through
              evidence-based analysis.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <span className="flex items-center gap-2 rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-xs font-semibold text-emerald-300">
                <CheckCircle2 size={15} />
                System Operational
              </span>

              <span className="flex items-center gap-2 rounded-lg border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-xs font-semibold text-amber-200">
                <Zap size={15} />
                {health.default_execution_mode?.toUpperCase() || 'UNKNOWN'} MODE
              </span>
            </div>
          </div>

          <div className="hidden h-40 w-40 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] md:flex">
            <div className="flex h-28 w-28 items-center justify-center rounded-full border border-blue-300/30 bg-blue-400/10">
              <ShieldCheck size={65} strokeWidth={1.2} className="text-blue-200" />
            </div>
          </div>
        </div>
      </section>

      {/* Metrics */}

      <section>
        <div className="mb-4">
          <h2 className="text-lg font-bold text-slate-900">System Overview</h2>
          <p className="mt-1 text-xs text-slate-400">
            Live information retrieved from your backend.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Backend Status"
            value={health.status?.toUpperCase() || 'UNKNOWN'}
            subtitle="FastAPI service"
            icon={Server}
            color="bg-emerald-50 text-emerald-600"
          />

          <MetricCard
            title="Database Tables"
            value={tables.length}
            subtitle="Total database tables"
            icon={Database}
            color="bg-blue-50 text-blue-600"
          />

          <MetricCard
            title="Warehouse Tables"
            value={warehouseTables.length}
            subtitle="Analytical data warehouse"
            icon={Layers3}
            color="bg-violet-50 text-violet-600"
          />

          <MetricCard
            title="Application Tables"
            value={applicationTables.length}
            subtitle="Operational database"
            icon={Table2}
            color="bg-amber-50 text-amber-600"
          />
        </div>
      </section>

      {/* Infrastructure */}

      <section className="grid gap-5 xl:grid-cols-2">

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <SectionTitle
            icon={Activity}
            title="Infrastructure Health"
            subtitle="Current application status"
          />

          <div className="space-y-1">
            {[
              {
                name: 'Backend API',
                detail: 'FastAPI application',
                status: health.status === 'ok'
              },
              {
                name: 'SQLite Database',
                detail: db.database_file_exists ? 'Database file detected' : 'Database file missing',
                status: Boolean(db.database_file_exists)
              },
              {
                name: 'Execution Environment',
                detail: `Application version ${health.version || 'Unknown'}`,
                status: Boolean(health.default_execution_mode)
              }
            ].map(item => (
              <div key={item.name} className="flex items-center justify-between border-b border-slate-100 py-4 last:border-0">
                <div>
                  <p className="text-sm font-semibold text-slate-700">{item.name}</p>
                  <p className="mt-1 text-xs text-slate-400">{item.detail}</p>
                </div>

                <span className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ${
                  item.status
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-red-50 text-red-700'
                }`}>
                  <CircleDot size={12} />
                  {item.status ? 'Connected' : 'Unavailable'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <SectionTitle
            icon={HardDrive}
            title="Database Information"
            subtitle="SQLite storage infrastructure"
          />

          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Database Location
            </p>
            <p className="mt-2 break-all text-sm font-medium leading-6 text-slate-700">
              {db.database_file || 'Not available'}
            </p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-100 p-4">
              <div className="text-xs text-slate-500">Application</div>
              <div className="mt-2 text-3xl font-bold text-slate-900">
                {applicationTables.length}
              </div>
              <div className="mt-1 text-xs text-slate-400">Tables</div>
            </div>

            <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
              <div className="text-xs text-blue-600">Warehouse</div>
              <div className="mt-2 text-3xl font-bold text-blue-900">
                {warehouseTables.length}
              </div>
              <div className="mt-1 text-xs text-blue-500">Tables</div>
            </div>
          </div>
        </div>

      </section>

      {/* Database Explorer */}

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-6">
          <SectionTitle
            icon={Database}
            title="Database Explorer"
            subtitle="Your project's database structure"
          />

          <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600">
            {tables.length} TABLES
          </span>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-2">

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">
                Application Tables
              </h3>
              <span className="text-xs text-slate-400">
                {applicationTables.length} tables
              </span>
            </div>

            <div className="space-y-2">
              {applicationTables.map(name => (
                <div key={name} className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 transition hover:border-blue-200 hover:bg-blue-50/30">
                  <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
                    <Database size={16} />
                  </div>
                  <span className="text-sm font-medium text-slate-700">{name}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">
                Warehouse Tables
              </h3>
              <span className="text-xs text-slate-400">
                {warehouseTables.length} tables
              </span>
            </div>

            <div className="space-y-2">
              {warehouseTables.map(name => (
                <div key={name} className="flex items-center gap-3 rounded-xl border border-violet-100 bg-violet-50/30 p-3 transition hover:border-violet-300">
                  <div className="rounded-lg bg-violet-100 p-2 text-violet-600">
                    <Layers3 size={16} />
                  </div>
                  <span className="flex-1 text-sm font-medium text-slate-700">{name}</span>
                  <span className="rounded-md bg-violet-100 px-2 py-1 text-[10px] font-bold text-violet-700">
                    DW
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </section>

      {/* Footer */}

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-5 text-xs text-slate-400">
        <p>AI Hallucination Intelligence & Reliability Platform</p>
        <div className="flex items-center gap-2">
          <Clock3 size={14} />
          Version {health.version || 'Unknown'}
        </div>
      </footer>

    </div>
  )
}