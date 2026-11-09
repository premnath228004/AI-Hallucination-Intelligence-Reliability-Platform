import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clipboard,
  Download,
  FilterX,
  Link2,
  Printer,
  RefreshCw,
  Share2,
  Sparkles,
} from 'lucide-react'
import { api, errorMessage } from '../api/client'
import { Badge, Card, EmptyState, ErrorBox, PageHeader, Spinner } from '../components/ui'

const COLORS = ['#2563eb', '#8b5cf6', '#14b8a6', '#f59e0b', '#ef4444', '#64748b']
const buttonClass = 'inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-50'
const selectClass = 'mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100'

function formatPercent(value) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`
}

function formatNumber(value) {
  return value == null ? '—' : Number(value).toLocaleString()
}

function wilsonInterval(correct, total) {
  if (!total) return null
  const z = 1.96
  const proportion = correct / total
  const denominator = 1 + (z * z) / total
  const center = (proportion + (z * z) / (2 * total)) / denominator
  const margin = (z * Math.sqrt((proportion * (1 - proportion) + (z * z) / (4 * total)) / total)) / denominator
  return [Math.max(0, center - margin), Math.min(1, center + margin)]
}

function accuracyWithInterval(accuracy, correct, total) {
  const interval = wilsonInterval(correct, total)
  return interval
    ? `${formatPercent(accuracy)} (95% Wilson CI ${formatPercent(interval[0])}–${formatPercent(interval[1])})`
    : formatPercent(accuracy)
}

function Metric({ label, value, note, icon: Icon, tone = 'blue' }) {
  const tones = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    violet: 'bg-violet-50 text-violet-700',
  }
  return (
    <Card className="h-full">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{value}</div>
          <div className="mt-1 text-xs text-slate-500">{note}</div>
        </div>
        <div className={`rounded-xl p-3 ${tones[tone]}`}><Icon size={20} /></div>
      </div>
    </Card>
  )
}

function Slicer({ label, value, onChange, children }) {
  return (
    <label className="block min-w-0">
      <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</span>
      <select className={selectClass} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">All</option>
        {children}
      </select>
    </label>
  )
}

function HorizontalBars({ items, labelKey, valueKey, formatValue, percent = false }) {
  const max = Math.max(...items.map((item) => Number(item[valueKey]) || 0), percent ? 1 : 0)
  if (!items.length) return <EmptyState title="No chart data" />
  return (
    <div className="space-y-5 py-2">
      {items.map((item, index) => {
        const value = Number(item[valueKey]) || 0
        const width = max > 0 ? Math.max((value / max) * 100, value > 0 ? 2 : 0) : 0
        return (
          <div key={item[labelKey]}>
            <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
              <span className="truncate font-medium text-slate-700">{item[labelKey]}</span>
              <span className="shrink-0 text-xs font-semibold tabular-nums text-slate-500">{formatValue(value, item)}</span>
            </div>
            <div
              className="h-3 overflow-hidden rounded-full bg-slate-100"
              role="img"
              aria-label={`${item[labelKey]}: ${formatValue(value, item)}`}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${width}%`, backgroundColor: COLORS[index % COLORS.length] }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function AnalyticsReport() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [note, setNote] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  const selected = useMemo(() => ({
    dataset_id: searchParams.get('dataset') || '',
    experiment_id: searchParams.get('experiment') || '',
    strategy: searchParams.get('strategy') || '',
    verdict_group: searchParams.get('verdict') || '',
    execution_mode: searchParams.get('mode') || '',
  }), [searchParams])

  const load = async () => {
    setLoading(true)
    setError('')
    setReport(null)
    try {
      const params = Object.fromEntries(
        Object.entries(selected).filter(([, value]) => value !== ''),
      )
      const response = await api.get('/api/warehouse/report', { params })
      setReport(response.data)
      setLastUpdated(new Date())
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  // Slicer selections are the complete set of report query dependencies.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected.dataset_id, selected.experiment_id, selected.strategy, selected.verdict_group, selected.execution_mode])

  const updateSlicer = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next, { replace: true })
  }

  const metrics = report?.metrics
  const insights = useMemo(() => {
    if (!metrics || metrics.total_responses === 0) return []
    const findings = []
    const strategy = [...(report.by_strategy || [])]
      .filter((item) => item.accuracy != null)
      .sort((left, right) => right.accuracy - left.accuracy)[0]
    if (strategy) {
      findings.push(`${strategy.label} has the highest measured provisional accuracy at ${accuracyWithInterval(strategy.accuracy, strategy.correct, strategy.responses)} (${strategy.correct}/${strategy.responses} responses).`)
    }
    findings.push(`${metrics.needs_review} response(s) are flagged for review; ${metrics.human_reviewed} have a recorded human verdict.`)
    findings.push(`${formatPercent(metrics.simulated_share)} of the selected responses are simulated. ${metrics.simulated_responses ? 'Do not interpret these as real model outputs.' : 'The selection contains no simulated responses.'}`)
    if (metrics.retrieval_measured > 0) {
      findings.push(`Retrieval hit rate is ${formatPercent(metrics.retrieval_hit_rate)} across ${metrics.retrieval_measured} labelled retrieval(s).`)
    }
    const commonVerdict = report.by_verdict?.[0]
    if (commonVerdict) findings.push(`Most common verdict group: ${commonVerdict.verdict_group} (${commonVerdict.responses} response(s)).`)
    return findings
  }, [metrics, report])

  const selectedLabels = useMemo(() => {
    if (!report) return []
    const labels = []
    const dataset = report.filters.datasets.find((item) => String(item.id) === selected.dataset_id)
    const experiment = report.filters.experiments.find((item) => String(item.id) === selected.experiment_id)
    const strategy = report.filters.strategies.find((item) => item.name === selected.strategy)
    if (dataset) labels.push(`Dataset: ${dataset.name} ${dataset.version}`)
    if (experiment) labels.push(`Experiment: ${experiment.name} (#${experiment.id})`)
    if (strategy) labels.push(`Strategy: ${strategy.label}`)
    if (selected.verdict_group) labels.push(`Verdict: ${selected.verdict_group}`)
    if (selected.execution_mode) labels.push(`Execution mode: ${selected.execution_mode}`)
    return labels
  }, [report, selected])

  const shareUrl = `${window.location.origin}${window.location.pathname}${searchParams.toString() ? `?${searchParams}` : ''}`
  const shareText = useMemo(() => [
    'AI reliability dashboard review',
    selectedLabels.length ? selectedLabels.join('\n') : 'Filters: All data',
    '',
    ...insights.map((item) => `• ${item}`),
    note.trim() ? `\nAnalyst note: ${note.trim()}` : '',
    `\nDashboard link: ${shareUrl}`,
    '\nNote: accuracy is provisional; demo outputs are simulated.',
  ].join('\n'), [selectedLabels, insights, note, shareUrl])

  const copyText = async (text, successMessage) => {
    setFeedback('')
    try {
      await navigator.clipboard.writeText(text)
      setFeedback(successMessage)
    } catch {
      setFeedback('Clipboard access is unavailable in this browser. You can copy the dashboard URL from the address bar.')
    }
  }

  const share = async () => {
    setFeedback('')
    try {
      if (navigator.share) {
        await navigator.share({ title: 'AI reliability dashboard review', text: shareText, url: shareUrl })
        setFeedback('Dashboard review shared.')
      } else {
        await copyText(shareUrl, 'Filtered dashboard link copied.')
      }
    } catch (shareError) {
      if (shareError?.name !== 'AbortError') setFeedback('Could not open the share dialog. Copy the dashboard link instead.')
    }
  }

  const downloadReview = () => {
    const blob = new Blob([shareText], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'ai-reliability-dashboard-review.txt'
    anchor.click()
    URL.revokeObjectURL(url)
    setFeedback('Dashboard review downloaded.')
  }

  const clearFilters = () => {
    setSearchParams({}, { replace: true })
    setNote('')
  }

  const filters = report?.filters
  const strategyChart = report?.by_strategy || []
  const verdictChart = report?.by_verdict || []
  const questions = report?.questions_to_review || []
  const denominator = metrics?.retrieval_measured || 0

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="Analytics & Shareable Reports"
        description="Slice warehouse results, see a generated interpretation, and share the exact filtered review with collaborators."
        actions={(
          <div className="flex flex-wrap gap-2 print:hidden">
            <button type="button" className={buttonClass} onClick={load} disabled={loading}><RefreshCw size={16} />Refresh</button>
            <button type="button" className={buttonClass} onClick={share}><Share2 size={16} />Share review</button>
          </div>
        )}
      />

      <Card className="print:hidden">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Report slicers</h2>
            <p className="mt-1 text-xs text-slate-500">Selections are encoded in the URL, so the link opens this same filtered view.</p>
          </div>
          <button type="button" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-700" onClick={clearFilters}><FilterX size={15} />Clear all</button>
        </div>
        {filters ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <Slicer label="Dataset" value={selected.dataset_id} onChange={(value) => updateSlicer('dataset', value)}>
              {filters.datasets.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}
            </Slicer>
            <Slicer label="Experiment" value={selected.experiment_id} onChange={(value) => updateSlicer('experiment', value)}>
              {filters.experiments.map((item) => <option key={item.id} value={item.id}>#{item.id} · {item.name}</option>)}
            </Slicer>
            <Slicer label="Strategy" value={selected.strategy} onChange={(value) => updateSlicer('strategy', value)}>
              {filters.strategies.map((item) => <option key={item.name} value={item.name}>{item.label}</option>)}
            </Slicer>
            <Slicer label="Verdict group" value={selected.verdict_group} onChange={(value) => updateSlicer('verdict', value)}>
              {filters.verdict_groups.map((item) => <option key={item} value={item}>{item}</option>)}
            </Slicer>
            <Slicer label="Execution mode" value={selected.execution_mode} onChange={(value) => updateSlicer('mode', value)}>
              {filters.execution_modes.map((item) => <option key={item} value={item}>{item}</option>)}
            </Slicer>
          </div>
        ) : null}
      </Card>

      {error && <ErrorBox message={error} onRetry={load} />}
      {loading && !report && <Spinner label="Loading warehouse analytics..." />}

      {report && metrics?.total_responses === 0 && (
        <Card>
          <EmptyState title="No warehouse results for these filters" description="Refresh the warehouse after evaluating an experiment, or clear the report slicers." />
          <div className="mt-3 text-center"><Link to="/warehouse" className="text-sm font-semibold text-blue-700 hover:text-blue-900">Open Data Warehouse →</Link></div>
        </Card>
      )}

      {report && metrics?.total_responses > 0 && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
            <div className="flex flex-wrap gap-2">
              {selectedLabels.length ? selectedLabels.map((label) => <Badge key={label} tone="teal">{label}</Badge>) : <Badge>All warehouse results</Badge>}
            </div>
            <span>{report.last_etl_run ? `Warehouse run #${report.last_etl_run.run_id} · ${report.last_etl_run.status}` : 'No ETL run recorded'}{lastUpdated ? ` · loaded ${lastUpdated.toLocaleTimeString()}` : ''}</span>
          </div>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <Metric label="Responses" value={formatNumber(metrics.total_responses)} note="Filtered warehouse rows" icon={Activity} />
            <Metric label="Provisional accuracy" value={formatPercent(metrics.accuracy_provisional)} note={`${metrics.correct_responses} marked correct · 95% Wilson CI ${wilsonInterval(metrics.correct_responses, metrics.total_responses)?.map(formatPercent).join('–') || '—'}`} icon={CheckCircle2} tone="green" />
            <Metric label="Needs review" value={formatNumber(metrics.needs_review)} note={`${formatNumber(metrics.human_reviewed)} human-reviewed`} icon={AlertTriangle} tone="amber" />
            <Metric label="Simulated share" value={formatPercent(metrics.simulated_share)} note={`${formatNumber(metrics.simulated_responses)} simulated responses`} icon={Sparkles} tone="violet" />
            <Metric label="Retrieval hit rate" value={formatPercent(metrics.retrieval_hit_rate)} note={`${denominator} labelled RAG retrievals`} icon={Link2} />
          </section>

          <section className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
            <Card title="Strategy comparison" description="Provisional accuracy for the current slicer selection.">
              <div className="min-h-[280px]">
                <HorizontalBars items={strategyChart} labelKey="label" valueKey="accuracy" formatValue={(value, item) => accuracyWithInterval(value, item.correct, item.responses)} percent />
              </div>
              <p className="text-xs text-slate-500">14 questions per strategy, no significance claimed.</p>
            </Card>
            <Card title="Verdict distribution" description="Count of response rows by final verdict group.">
              <div className="min-h-[280px]">
                <HorizontalBars items={verdictChart} labelKey="verdict_group" valueKey="responses" formatValue={formatNumber} />
              </div>
            </Card>
          </section>

          <section className="grid gap-5 xl:grid-cols-[1fr_0.85fr]">
            <Card title="Rule-based summary (not AI-generated)" description="A concise interpretation of the current selection—review before sharing.">
              <ul className="space-y-3">
                {insights.map((insight) => <li key={insight} className="flex gap-2.5 text-sm leading-6 text-slate-700"><Sparkles size={16} className="mt-1 shrink-0 text-blue-600" />{insight}</li>)}
              </ul>
              <label className="mt-5 block">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Your dashboard review note</span>
                <textarea className="mt-1.5 min-h-24 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add context or an interpretation before sharing..." />
              </label>
              <div className="mt-4 flex flex-wrap gap-2 print:hidden">
                <button type="button" className={buttonClass} onClick={() => copyText(shareText, 'Insight summary copied with the selected slicers and dashboard link.')}><Clipboard size={16} />Copy insight summary</button>
                <button type="button" className={buttonClass} onClick={downloadReview}><Download size={16} />Download review</button>
                <button type="button" className={buttonClass} onClick={() => window.print()}><Printer size={16} />Print / Save PDF</button>
              </div>
              <p className="mt-3 text-xs leading-5 text-slate-400 print:hidden">A shared URL contains filter selections, not report data or access permissions. Your recipient must be able to open this app address; a localhost link works only on your computer.</p>
              {feedback && <p role="status" className="mt-3 text-xs font-medium text-emerald-700">{feedback}</p>}
            </Card>
            <Card title="Questions to review" description="Questions with the highest number of incorrect responses under the current filters.">
              {questions.length ? (
                <div className="space-y-3">
                  {questions.map((item) => (
                    <div key={item.external_id} className="rounded-xl border border-slate-100 p-3.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-slate-500">{item.external_id}{item.category ? ` · ${item.category}` : ''}</span>
                        <Badge tone={item.needs_review ? 'amber' : 'slate'}>{item.incorrect_responses} incorrect · {item.needs_review} pending</Badge>
                      </div>
                      <p className="mt-2 text-sm leading-5 text-slate-700">{item.question_text}</p>
                    </div>
                  ))}
                </div>
              ) : <EmptyState title="No question-level rows" description="This selection has no questions to report." />}
            </Card>
          </section>

          <Card className="border-amber-200 bg-amber-50/60">
            <h2 className="text-sm font-bold text-amber-950">Interpretation and freshness</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-xs leading-5 text-amber-900">
              {report.limitations.map((item) => <li key={item}>{item}</li>)}
            </ul>
            {report.last_etl_run?.status !== 'success' && <p className="mt-3 text-xs font-semibold text-amber-950">The latest warehouse run is not successful. Refresh ETL in Data Warehouse before sharing this report.</p>}
          </Card>
        </>
      )}
    </div>
  )
}
