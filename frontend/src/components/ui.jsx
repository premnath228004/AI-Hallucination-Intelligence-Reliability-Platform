import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'

export function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {description && <p className="mt-1 max-w-2xl text-sm text-slate-600">{description}</p>}
      </div>
      {actions}
    </div>
  )
}

export function Card({ title, description, children, className = '' }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
      {description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
      <div className={title ? 'mt-4' : ''}>{children}</div>
    </section>
  )
}

const TONES = {
  slate: 'bg-slate-100 text-slate-700',
  amber: 'bg-amber-100 text-amber-900',
  green: 'bg-emerald-100 text-emerald-800',
  red: 'bg-red-100 text-red-800',
  teal: 'bg-teal-100 text-teal-800',
}

export function Badge({ tone = 'slate', children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${TONES[tone]}`}>
      {children}
    </span>
  )
}

export function Spinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 py-10 text-sm text-slate-600" role="status">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  )
}

export function ErrorBox({ message, onRetry }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <div className="flex-1">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="rounded-md border border-red-300 bg-white px-3 py-1.5 font-medium hover:bg-red-100">
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, description }) {
  return (
    <div className="flex flex-col items-center gap-2 py-10 text-center">
      <Inbox size={28} className="text-slate-400" />
      <div className="font-medium text-slate-900">{title}</div>
      {description && <div className="max-w-md text-sm text-slate-600">{description}</div>}
    </div>
  )
}