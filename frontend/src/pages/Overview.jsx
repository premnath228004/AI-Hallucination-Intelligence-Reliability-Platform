import { useEffect, useState } from 'react'
import { api, errorMessage } from '../api/client'
import { Badge, Card, ErrorBox, PageHeader, Spinner } from '../components/ui'

function Info({ label, value }) {
  return (
    <Card>
      <div className="text-sm text-slate-600">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
    </Card>
  )
}

export default function Overview() {
  const [state, setState] = useState({ status: 'loading' })

  const load = () => {
    setState({ status: 'loading' })
    Promise.all([api.get('/api/health'), api.get('/api/db-info')])
      .then(([health, db]) => setState({ status: 'ok', health: health.data, db: db.data }))
      .catch((error) => setState({ status: 'error', message: errorMessage(error) }))
  }
  useEffect(load, [])

  return (
    <>
      <PageHeader
        title="Overview"
        description="Live system status from the backend. Reliability KPIs and charts are added in the next step."
      />
      {state.status === 'loading' && <Spinner label="Contacting backend..." />}
      {state.status === 'error' && <ErrorBox message={state.message} onRetry={load} />}
      {state.status === 'ok' && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Info label="Backend status" value={state.health.status} />
            <Info label="Backend version" value={state.health.version} />
            <Info label="Default execution mode" value={state.health.default_execution_mode} />
            <Info label="Database file" value={state.db.database_file_exists ? 'Found' : 'Missing'} />
          </div>
          <Card title="Database tables" description={`${state.db.tables.length} tables in the SQLite database`}>
            <div className="flex flex-wrap gap-2">
              {state.db.tables.map((name) => (
                <Badge key={name} tone={name.startsWith('dw_') ? 'teal' : 'slate'}>{name}</Badge>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">Teal tables belong to the data warehouse (dw_ prefix).</p>
          </Card>
        </div>
      )}
    </>
  )
}