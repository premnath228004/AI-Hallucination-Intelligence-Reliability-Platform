import { Link, useLocation } from 'react-router-dom'
import { Card, EmptyState, PageHeader } from '../components/ui'
import { NAV } from '../nav'

export default function NotBuilt() {
  const { pathname } = useLocation()
  const cleanPath = pathname.replace(/\/+$/, '') || '/'
  const item = NAV.find((n) => n.to === cleanPath)

  if (!item) {
    return (
      <>
        <PageHeader title="Page not found" description={`There is no page at "${pathname}".`} />
        <Link
          to="/"
          className="inline-flex rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800"
        >
          Go to Overview
        </Link>
      </>
    )
  }

  return (
    <>
      <PageHeader title={item.label} description={item.description} />
      <Card>
        <EmptyState
          title="Not built yet"
          description="This page is planned for a later step. The backend already provides these endpoints:"
        />
        <ul className="mx-auto max-w-lg space-y-1 text-center font-mono text-xs text-slate-600">
          {item.endpoints.map((endpoint) => (
            <li key={endpoint}>{endpoint}</li>
          ))}
        </ul>
      </Card>
    </>
  )
}