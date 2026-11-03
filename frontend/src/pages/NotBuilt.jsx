import { useLocation } from 'react-router-dom'
import { Card, EmptyState, PageHeader } from '../components/ui'
import { NAV } from '../nav'

export default function NotBuilt() {
  const { pathname } = useLocation()
  const item = NAV.find((n) => n.to === pathname)

  if (!item) return <PageHeader title="Page not found" description="This address does not exist." />

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