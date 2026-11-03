import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Check,
  CircleAlert,
  Database,
  Download,
  FileCheck2,
  LoaderCircle,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { api, errorMessage } from '../api/client'
import { Badge, Card, EmptyState, ErrorBox, PageHeader, Spinner } from '../components/ui'

const inputClass = 'mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100'
const labelClass = 'text-xs font-semibold uppercase tracking-wide text-slate-500'
const primaryButton = 'inline-flex items-center justify-center gap-2 rounded-xl bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50'
const secondaryButton = 'inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-50'

function ActionButton({ children, busy, className = secondaryButton, ...props }) {
  return (
    <button className={className} disabled={busy || props.disabled} {...props}>
      {busy ? <LoaderCircle size={16} className="animate-spin" /> : null}
      {children}
    </button>
  )
}

function SelectField({ label, value, onChange, children, ...props }) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      <select className={inputClass} value={value} onChange={onChange} {...props}>
        {children}
      </select>
    </label>
  )
}

function TextField({ label, ...props }) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      <input className={inputClass} {...props} />
    </label>
  )
}

function Notice({ tone = 'blue', children }) {
  const styles = {
    blue: 'border-blue-100 bg-blue-50 text-blue-900',
    amber: 'border-amber-200 bg-amber-50 text-amber-900',
    green: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  }
  return <div className={`rounded-xl border px-4 py-3 text-sm leading-6 ${styles[tone]}`}>{children}</div>
}

function Percent({ value }) {
  return value == null ? '—' : `${Math.round(value * 100)}%`
}

function usePageData(loader, dependencies = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await loader()
      setData(result)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let active = true
    loader()
      .then((result) => {
        if (active) setData(result)
      })
      .catch((requestError) => {
        if (active) setError(errorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  // The caller supplies stable scalar dependencies.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  return { data, setData, loading, error, reload }
}

function ExperimentOption({ experiment }) {
  return (
    <option value={experiment.id}>
      #{experiment.id} · {experiment.name} · {experiment.status}
    </option>
  )
}

export function ExperimentStudio() {
  const datasets = usePageData(async () => {
    const [datasetResponse, experimentResponse, documentResponse] = await Promise.all([
      api.get('/api/datasets'),
      api.get('/api/experiments'),
      api.get('/api/documents'),
    ])
    return {
      datasets: datasetResponse.data,
      experiments: experimentResponse.data,
      documents: documentResponse.data,
    }
  })
  const [datasetId, setDatasetId] = useState('')
  const [name, setName] = useState('')
  const [mode, setMode] = useState('demo')
  const [busy, setBusy] = useState('')
  const [actionError, setActionError] = useState('')
  const [created, setCreated] = useState(null)

  const selectedDatasetId = datasetId || String(datasets.data?.datasets?.[0]?.id || '')

  const loadSample = async (endpoint, action) => {
    setBusy(action)
    setActionError('')
    try {
      await api.post(endpoint)
      await datasets.reload()
    } catch (error) {
      setActionError(errorMessage(error))
    } finally {
      setBusy('')
    }
  }

  const run = async (event) => {
    event.preventDefault()
    setBusy('run')
    setActionError('')
    setCreated(null)
    try {
      const response = await api.post('/api/experiments', {
        dataset_id: Number(selectedDatasetId),
        name: name.trim() || null,
        execution_mode: mode,
      })
      setCreated(response.data)
      setName('')
      await datasets.reload()
    } catch (error) {
      setActionError(errorMessage(error))
    } finally {
      setBusy('')
    }
  }

  const ready = Boolean(datasets.data?.datasets?.length && datasets.data?.documents?.length)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Experiment Studio"
        description="Run the same benchmark through basic, improved, and retrieval-augmented strategies."
        actions={<ActionButton onClick={datasets.reload} busy={datasets.loading}><RefreshCw size={16} />Refresh</ActionButton>}
      />
      {datasets.error && <ErrorBox message={datasets.error} onRetry={datasets.reload} />}
      {actionError && <ErrorBox message={actionError} />}
      {created && (
        <Notice tone="green">
          Experiment #{created.id} finished with status <strong>{created.status}</strong> and {created.response_count} responses.
        </Notice>
      )}

      <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <Card title="Prepare a run" description="The sample benchmark and evidence corpus are used only when you choose to load them.">
          {!ready && (
            <div className="mb-5 grid gap-3 sm:grid-cols-2">
              {!datasets.data?.datasets?.length && (
                <div className="rounded-xl border border-dashed border-slate-300 p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><BookOpen size={17} />Benchmark dataset</div>
                  <p className="mt-1 text-xs leading-5 text-slate-500">Load the bundled sample questions.</p>
                  <ActionButton className={`${secondaryButton} mt-3`} busy={busy === 'dataset'} onClick={() => loadSample('/api/datasets/load-sample', 'dataset')}>Load sample</ActionButton>
                </div>
              )}
              {!datasets.data?.documents?.length && (
                <div className="rounded-xl border border-dashed border-slate-300 p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><Database size={17} />Evidence corpus</div>
                  <p className="mt-1 text-xs leading-5 text-slate-500">Load the bundled pilot corpus required for retrieval.</p>
                  <ActionButton className={`${secondaryButton} mt-3`} busy={busy === 'documents'} onClick={() => loadSample('/api/documents/load-sample', 'documents')}>Load corpus</ActionButton>
                </div>
              )}
            </div>
          )}
          {ready && (
            <Notice tone="green">
              Ready to run with {datasets.data.datasets.length} dataset(s) and {datasets.data.documents.length} evidence document(s).
            </Notice>
          )}
          <form onSubmit={run} className="mt-5 space-y-4">
            <SelectField label="Benchmark dataset" value={selectedDatasetId} onChange={(event) => setDatasetId(event.target.value)} disabled={!datasets.data?.datasets?.length}>
              {datasets.data?.datasets?.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name} · {dataset.version} ({dataset.question_count} questions)</option>)}
              {!datasets.data?.datasets?.length && <option value="">Load a sample dataset first</option>}
            </SelectField>
            <div className="grid gap-4 sm:grid-cols-2">
              <SelectField label="Execution mode" value={mode} onChange={(event) => setMode(event.target.value)}>
                <option value="demo">Demo fixtures</option>
                <option value="local_llm">Local LLM</option>
                <option value="external_api">External API</option>
              </SelectField>
              <TextField label="Run name (optional)" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Pilot comparison" maxLength={200} />
            </div>
            {mode !== 'demo' && <Notice tone="amber">This run requires a configured model provider. Provider credentials and availability are checked by the backend.</Notice>}
            <ActionButton type="submit" className={primaryButton} busy={busy === 'run'} disabled={!ready || !selectedDatasetId}><Play size={16} />Run experiment</ActionButton>
          </form>
        </Card>

        <Card title="Recent experiments" description="Runs are stored in the project database and can be evaluated or inspected below.">
          {datasets.loading && <Spinner label="Loading experiments..." />}
          {!datasets.loading && !datasets.data?.experiments?.length && <EmptyState title="No experiments yet" description="Prepare a run to compare answer strategies." />}
          <div className="space-y-3">
            {datasets.data?.experiments?.slice(0, 8).map((experiment) => (
              <div key={experiment.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-4">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-slate-800">{experiment.name}</div>
                  <div className="mt-1 text-xs text-slate-500">{experiment.execution_mode} · {experiment.model_name} · {experiment.response_count} responses</div>
                </div>
                <Badge tone={experiment.status === 'completed' ? 'green' : 'amber'}>#{experiment.id} {experiment.status}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
      <Card title="What this run measures" description="All three strategies run against the same questions. The RAG strategy stores its retrieved chunks for later inspection.">
        <div className="grid gap-3 md:grid-cols-3">
          {[
            ['Basic', 'Direct answer generation with the baseline prompt.'],
            ['Improved', 'A more careful instruction set, including abstention behavior.'],
            ['RAG', 'Retrieval-augmented answer strategy plus stored evidence matches.'],
          ].map(([title, detail]) => <div key={title} className="rounded-xl bg-slate-50 p-4"><div className="text-sm font-bold text-slate-800">{title}</div><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div>)}
        </div>
        <p className="mt-4 text-xs leading-5 text-slate-500">Demo mode returns simulated fixture outputs; it does not call a real language model. RAG retrieval is performed, but demo answers are not generated from retrieved chunks.</p>
      </Card>
    </div>
  )
}

function ReviewItem({ item, onSaved }) {
  const [verdict, setVerdict] = useState(item.human_verdict || item.reference_verdict || 'incorrect')
  const [note, setNote] = useState(item.human_note || '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved(false)
    try {
      await api.post('/api/evaluations/review', {
        response_id: item.response_id,
        verdict,
        note: note.trim() || null,
      })
      setSaved(true)
      onSaved()
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{item.question_external_id} · {item.strategy} strategy</div>
          <h3 className="mt-2 text-sm font-semibold leading-6 text-slate-900">{item.question_text}</h3>
        </div>
        <Badge tone={item.needs_review && !item.human_verdict ? 'amber' : item.human_verdict ? 'teal' : 'slate'}>
          {item.human_verdict ? 'Human reviewed' : item.reference_verdict || 'Not evaluated'}
        </Badge>
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl bg-slate-50 p-4"><div className="text-[11px] font-bold uppercase tracking-wide text-slate-400">Model answer</div><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{item.answer_text || 'No answer was produced.'}</p></div>
        <div className="rounded-xl bg-blue-50/60 p-4"><div className="text-[11px] font-bold uppercase tracking-wide text-blue-500">Reference answer</div><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{item.reference_answer || 'No reference answer provided.'}</p></div>
      </div>
      {item.reference_explanation && <p className="mt-3 text-xs leading-5 text-slate-500">{item.reference_explanation}</p>}
      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_1.5fr_auto] sm:items-end">
        <SelectField label="Human verdict" value={verdict} onChange={(event) => setVerdict(event.target.value)}>
          <option value="correct">Correct</option>
          <option value="correct_abstention">Correct abstention</option>
          <option value="incorrect">Incorrect</option>
          <option value="incorrect_abstention">Incorrect abstention</option>
          <option value="failure_to_abstain">Failure to abstain</option>
        </SelectField>
        <TextField label="Review note (optional)" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add context for this decision" />
        <ActionButton className={primaryButton} busy={busy} onClick={save}><Check size={16} />Save review</ActionButton>
      </div>
      {saved && <p className="mt-3 text-xs font-medium text-emerald-700">Review saved.</p>}
      {error && <p className="mt-3 text-xs text-red-700">{error}</p>}
    </article>
  )
}

export function EvaluationCenter() {
  const experiments = usePageData(async () => (await api.get('/api/experiments')).data)
  const [experimentId, setExperimentId] = useState('')
  const [reviewOnly, setReviewOnly] = useState(false)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState('')
  const [toast, setToast] = useState('')
  const selectedExperimentId = experimentId || String(experiments.data?.[0]?.id || '')
  const summary = usePageData(async () => {
    if (!selectedExperimentId) return null
    const [summaryResponse, evaluationResponse] = await Promise.all([
      api.get(`/api/experiments/${selectedExperimentId}/summary`),
      api.get(`/api/experiments/${selectedExperimentId}/evaluations`, { params: { needs_review_only: reviewOnly } }),
    ])
    return { summary: summaryResponse.data, evaluations: evaluationResponse.data }
  }, [selectedExperimentId, reviewOnly])

  const evaluate = async () => {
    setBusy(true)
    setActionError('')
    setToast('')
    try {
      const response = await api.post(`/api/experiments/${selectedExperimentId}/evaluate`)
      setToast(`Evaluation complete: ${response.data.inserted} new, ${response.data.skipped_existing} already evaluated.`)
      await summary.reload()
    } catch (error) {
      setActionError(errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  const strategyEntries = Object.entries(summary.data?.summary?.strategies || {})

  return (
    <div className="space-y-6">
      <PageHeader title="Evaluation Center" description="Review reference-based scores, understand uncertainty, and record human verdicts." actions={<ActionButton onClick={summary.reload} busy={summary.loading}><RefreshCw size={16} />Refresh</ActionButton>} />
      {experiments.error && <ErrorBox message={experiments.error} onRetry={experiments.reload} />}
      {actionError && <ErrorBox message={actionError} />}
      {toast && <Notice tone="green">{toast}</Notice>}
      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-[240px] flex-1">
            <SelectField label="Experiment" value={selectedExperimentId} onChange={(event) => setExperimentId(event.target.value)}>
              {experiments.data?.map((experiment) => <ExperimentOption key={experiment.id} experiment={experiment} />)}
              {!experiments.data?.length && <option value="">Run an experiment first</option>}
            </SelectField>
          </div>
          <ActionButton className={primaryButton} busy={busy} disabled={!selectedExperimentId} onClick={evaluate}><Sparkles size={16} />Run reference evaluation</ActionButton>
          <label className="flex items-center gap-2 rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm font-medium text-slate-600">
            <input type="checkbox" checked={reviewOnly} onChange={(event) => setReviewOnly(event.target.checked)} className="accent-blue-700" />
            Needs review only
          </label>
        </div>
      </Card>
      {summary.loading && selectedExperimentId && <Spinner label="Loading evaluation results..." />}
      {summary.error && <ErrorBox message={summary.error} onRetry={summary.reload} />}
      {strategyEntries.length > 0 && (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            {strategyEntries.map(([strategy, stats]) => (
              <Card key={strategy} className="relative overflow-hidden">
                <div className="flex items-start justify-between"><div><div className="text-xs font-bold uppercase tracking-wider text-slate-400">{strategy} strategy</div><div className="mt-3 text-3xl font-bold tracking-tight text-slate-900"><Percent value={stats.accuracy_provisional} /></div><div className="mt-1 text-xs text-slate-500">Provisional accuracy · {stats.evaluated}/{stats.responses} evaluated</div></div><div className="rounded-xl bg-blue-50 p-3 text-blue-700"><Activity size={20} /></div></div>
                {stats.accuracy_95ci_wilson && <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-600" style={{ width: `${(stats.accuracy_provisional || 0) * 100}%` }} /></div>}
                <div className="mt-3 flex justify-between text-xs text-slate-500"><span>{stats.pending_manual_review} pending review</span><span>{stats.human_reviewed} human reviewed</span></div>
              </Card>
            ))}
          </section>
          {summary.data.summary.limitations?.length > 0 && (
            <Notice tone="amber"><strong>Interpret results carefully.</strong> {summary.data.summary.limitations.join(' ')}</Notice>
          )}
        </>
      )}
      <section className="space-y-4">
        {!summary.loading && !summary.error && selectedExperimentId && summary.data?.evaluations?.items?.length === 0 && <Card><EmptyState title="No responses to show" description="Run the reference evaluator or turn off the review-only filter." /></Card>}
        {summary.data?.evaluations?.items?.map((item) => <ReviewItem key={`${item.response_id}-${item.human_verdict || item.reference_verdict || 'pending'}`} item={item} onSaved={summary.reload} />)}
      </section>
      {!experiments.loading && !experiments.data?.length && <Card><EmptyState title="No experiments available" description="Create an experiment in Experiment Studio before evaluating responses." /></Card>}
    </div>
  )
}

export function RagInspector() {
  const initial = usePageData(async () => {
    const [experimentResponse, datasetResponse, documentResponse] = await Promise.all([
      api.get('/api/experiments'),
      api.get('/api/datasets'),
      api.get('/api/documents'),
    ])
    return { experiments: experimentResponse.data, datasets: datasetResponse.data, documents: documentResponse.data }
  })
  const [experimentId, setExperimentId] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [retrievalEval, setRetrievalEval] = useState(null)
  const [inspection, setInspection] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const selectedExperimentId = experimentId || String(initial.data?.experiments?.[0]?.id || '')
  const selectedDatasetId = datasetId || String(initial.data?.datasets?.[0]?.id || '')

  useEffect(() => {
    if (!selectedExperimentId) return
    let active = true
    api.get(`/api/experiments/${selectedExperimentId}/rag-inspection`)
      .then((response) => { if (active) setInspection(response.data) })
      .catch((requestError) => { if (active) setError(errorMessage(requestError)) })
    return () => { active = false }
  }, [selectedExperimentId])

  const runSearch = async (event) => {
    event.preventDefault()
    setBusy('search')
    setError('')
    try {
      const response = await api.get('/api/retrieval/search', { params: { q: query, k: 5 } })
      setSearchResults(response.data)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy('')
    }
  }

  const runRetrievalEval = async () => {
    setBusy('evaluate')
    setError('')
    try {
      const response = await api.get('/api/retrieval/evaluate', { params: { dataset_id: selectedDatasetId, k: 5 } })
      setRetrievalEval(response.data)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy('')
    }
  }

  const loadCorpus = async () => {
    setBusy('corpus')
    setError('')
    try {
      await api.post('/api/documents/load-sample')
      await initial.reload()
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy('')
    }
  }

  const documents = initial.data?.documents || []
  return (
    <div className="space-y-6">
      <PageHeader title="RAG Inspector" description="Search the evidence corpus, evaluate retrieval quality, and inspect chunks stored with RAG responses." actions={<ActionButton onClick={initial.reload} busy={initial.loading}><RefreshCw size={16} />Refresh</ActionButton>} />
      {initial.error && <ErrorBox message={initial.error} onRetry={initial.reload} />}
      {error && <ErrorBox message={error} />}
      {!documents.length && !initial.loading && <Notice tone="amber">The evidence corpus is empty. Load the bundled corpus to enable retrieval tools.<div><ActionButton className={`${secondaryButton} mt-3`} busy={busy === 'corpus'} onClick={loadCorpus}>Load sample corpus</ActionButton></div></Notice>}
      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="Live evidence search" description="Try the lexical retriever against the currently loaded corpus.">
          <form onSubmit={runSearch} className="flex flex-col gap-3 sm:flex-row">
            <input className={inputClass.replace('mt-1.5 ', '')} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask a question to retrieve matching passages" required />
            <ActionButton className={primaryButton} type="submit" busy={busy === 'search'}><Search size={16} />Search</ActionButton>
          </form>
          {searchResults && <div className="mt-4 space-y-3">{searchResults.results.map((result) => <div key={`${result.doc_key}-${result.chunk_index}`} className="rounded-xl border border-slate-100 p-4"><div className="flex items-center justify-between gap-3 text-xs"><span className="font-bold text-slate-700">{result.doc_key} · chunk {result.chunk_index}</span><Badge tone="teal">Score {Number(result.score).toFixed(3)}</Badge></div><p className="mt-2 text-sm leading-6 text-slate-600">{result.text}</p></div>)}</div>}
        </Card>
        <Card title="Retrieval benchmark" description="Measure hit rate and reciprocal rank on author-labelled relevant documents.">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[220px] flex-1"><SelectField label="Dataset" value={selectedDatasetId} onChange={(event) => setDatasetId(event.target.value)}>{initial.data?.datasets?.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name} · {dataset.version}</option>)}{!initial.data?.datasets?.length && <option value="">No datasets loaded</option>}</SelectField></div>
            <ActionButton className={secondaryButton} busy={busy === 'evaluate'} disabled={!selectedDatasetId} onClick={runRetrievalEval}><Activity size={16} />Evaluate retrieval</ActionButton>
          </div>
          {retrievalEval && <div className="mt-4 grid grid-cols-2 gap-3"><div className="rounded-xl bg-blue-50 p-4"><div className="text-xs text-blue-700">Hit rate @ {retrievalEval.k}</div><div className="mt-1 text-2xl font-bold text-blue-950"><Percent value={retrievalEval.hit_rate_at_k} /></div></div><div className="rounded-xl bg-violet-50 p-4"><div className="text-xs text-violet-700">MRR @ {retrievalEval.k}</div><div className="mt-1 text-2xl font-bold text-violet-950"><Percent value={retrievalEval.mrr_at_k} /></div></div><p className="col-span-2 text-xs leading-5 text-slate-500">{retrievalEval.questions_with_relevant_docs} labelled questions · {retrievalEval.retriever}</p></div>}
        </Card>
      </div>
      <Card title="Stored RAG response inspection" description="Retrieval traces are available for experiments that completed with the RAG strategy.">
        <SelectField label="Experiment" value={selectedExperimentId} onChange={(event) => { setExperimentId(event.target.value); setInspection(null) }}>
          {initial.data?.experiments?.map((experiment) => <ExperimentOption key={experiment.id} experiment={experiment} />)}
          {!initial.data?.experiments?.length && <option value="">No experiments loaded</option>}
        </SelectField>
        {inspection?.answer_note && <div className="mt-4"><Notice tone="amber">{inspection.answer_note}</Notice></div>}
        {inspection?.items?.length ? <div className="mt-4 space-y-4">{inspection.items.map((item) => <article key={item.response_id} className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><Badge tone={item.retrieval_hit ? 'green' : item.retrieval_hit === false ? 'amber' : 'slate'}>{item.retrieval_hit == null ? 'Unlabelled' : item.retrieval_hit ? 'Evidence retrieved' : 'No labelled evidence hit'}</Badge><span className="text-xs text-slate-400">{item.question_external_id}</span></div><h3 className="mt-3 text-sm font-semibold leading-6 text-slate-800">{item.question_text}</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{item.answer_text || 'No answer.'}</p>{item.diagnostic_hint && <div className="mt-3"><Notice tone="amber">{item.diagnostic_hint}</Notice></div>}<div className="mt-3 grid gap-2 md:grid-cols-2">{item.retrieved.map((result) => <div key={`${result.rank}-${result.doc_key}`} className="rounded-lg bg-slate-50 p-3"><div className="text-xs font-bold text-slate-600">#{result.rank} {result.doc_key} · {Number(result.score).toFixed(3)}</div><p className="mt-1 text-xs leading-5 text-slate-500">{result.text}</p></div>)}</div></article>)}</div> : <div className="mt-3"><EmptyState title="No RAG traces found" description="Choose a completed experiment with stored RAG responses." /></div>}
        {inspection?.limitations?.length > 0 && <p className="mt-4 text-xs leading-5 text-slate-500">{inspection.limitations.join(' ')}</p>}
      </Card>
    </div>
  )
}

export function AnswerChecker() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [evidence, setEvidence] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const check = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const response = await api.post('/api/check', {
        question: question.trim(),
        answer: answer.trim(),
        evidence: evidence.trim() || null,
      })
      setResult(response.data)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  const signalTone = result?.evidence_check?.signal === 'no_issue_detected' ? 'green' : result?.evidence_check?.signal === 'review_needed' ? 'amber' : 'blue'
  return (
    <div className="space-y-6">
      <PageHeader title="Answer Checker" description="Compare an answer with supplied evidence and, when available, a matching benchmark reference." />
      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <Card title="Check an answer" description="Paste evidence for a focused check, or leave it blank to search the loaded corpus.">
          <form onSubmit={check} className="space-y-4">
            <label className="block"><span className={labelClass}>Question</span><textarea className={`${inputClass} min-h-24 resize-y`} value={question} onChange={(event) => setQuestion(event.target.value)} required maxLength={2000} placeholder="What are you trying to answer?" /></label>
            <label className="block"><span className={labelClass}>Answer to check</span><textarea className={`${inputClass} min-h-32 resize-y`} value={answer} onChange={(event) => setAnswer(event.target.value)} required maxLength={5000} placeholder="Paste the generated answer..." /></label>
            <label className="block"><span className={labelClass}>Evidence (optional)</span><textarea className={`${inputClass} min-h-32 resize-y`} value={evidence} onChange={(event) => setEvidence(event.target.value)} maxLength={10000} placeholder="Paste trusted source text. If empty, the loaded corpus is used." /></label>
            <div className="flex items-start gap-2 text-xs leading-5 text-slate-500"><CircleAlert size={15} className="mt-0.5 shrink-0 text-amber-600" />This is a lexical overlap heuristic, not a semantic fact-checker. Treat flags as review candidates.</div>
            <ActionButton className={primaryButton} type="submit" busy={busy}><ShieldCheck size={16} />Check answer</ActionButton>
          </form>
        </Card>
        <div className="space-y-5">
          {error && <ErrorBox message={error} />}
          {!result && <Card><EmptyState title="Your analysis will appear here" description="Submit a question and answer to see claim-level evidence signals." /></Card>}
          {result && <>
            <Card title="Analysis result" description={`Evidence source: ${result.mode}${result.retriever ? ` · ${result.retriever}` : ''}`}>
              <div className="flex flex-wrap items-center justify-between gap-3"><Badge tone={signalTone}>{result.evidence_check.signal.replaceAll('_', ' ')}</Badge><span className="text-xs text-slate-500">{result.evidence_check.claims.length} claim(s) assessed</span></div>
              {result.reference_check && <div className="mt-4 rounded-xl border border-slate-100 p-4"><div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><FileCheck2 size={17} className="text-blue-700" />Benchmark reference</div><p className="mt-2 text-sm leading-6 text-slate-600">{result.reference_check.note || result.reference_check.explanation}</p>{result.reference_check.verdict && <div className="mt-2"><Badge tone={result.reference_check.needs_review ? 'amber' : 'teal'}>{result.reference_check.verdict}</Badge></div>}</div>}
            </Card>
            <Card title="Claim-level evidence">
              <div className="space-y-3">{result.evidence_check.claims.map((claim, index) => <div key={`${claim.sentence}-${index}`} className="rounded-xl border border-slate-100 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><Badge tone={claim.label === 'supported' ? 'green' : claim.label === 'abstention' ? 'slate' : 'amber'}>{claim.label.replaceAll('_', ' ')}</Badge>{claim.support_score != null && <span className="text-xs font-medium text-slate-500">Support score {claim.support_score}</span>}</div><p className="mt-3 text-sm font-medium leading-6 text-slate-800">{claim.sentence}</p><p className="mt-2 text-xs leading-5 text-slate-500">{claim.explanation}</p>{claim.best_passage && <blockquote className="mt-3 border-l-2 border-blue-300 pl-3 text-xs leading-5 text-slate-600">{claim.best_passage.text}<span className="mt-1 block font-semibold text-slate-400">{claim.best_passage.source}</span></blockquote>}</div>)}</div>
            </Card>
            {result.limitations?.length > 0 && <Notice tone="amber">{result.limitations.join(' ')}</Notice>}
          </>}
        </div>
      </div>
    </div>
  )
}

export function DataWarehouse() {
  const warehouse = usePageData(async () => {
    const [summary, runs] = await Promise.all([api.get('/api/warehouse/summary'), api.get('/api/warehouse/runs')])
    return { summary: summary.data, runs: runs.data }
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [latestRun, setLatestRun] = useState(null)

  const refresh = async () => {
    setBusy(true)
    setError('')
    setLatestRun(null)
    try {
      const response = await api.post('/api/warehouse/refresh')
      setLatestRun(response.data)
      await warehouse.reload()
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  const counts = Object.entries(warehouse.data?.summary?.table_row_counts || {})
  return (
    <div className="space-y-6">
      <PageHeader title="Data Warehouse" description="Refresh analytical tables from operational data and verify recent ETL runs." actions={<ActionButton className={primaryButton} onClick={refresh} busy={busy}><RefreshCw size={16} />Refresh warehouse</ActionButton>} />
      {warehouse.error && <ErrorBox message={warehouse.error} onRetry={warehouse.reload} />}
      {error && <ErrorBox message={error} />}
      {latestRun && <Notice tone={latestRun.status === 'success' ? 'green' : 'amber'}>ETL run {latestRun.status}. {latestRun.message || latestRun.error_message || ''}</Notice>}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {counts.map(([table, count]) => <Card key={table}><div className="flex items-center justify-between"><Database className="text-blue-700" size={19} /><Badge tone="slate">Warehouse</Badge></div><div className="mt-4 break-all text-xs font-semibold text-slate-500">{table}</div><div className="mt-1 text-3xl font-bold text-slate-900">{count}</div><div className="mt-1 text-xs text-slate-400">rows</div></Card>)}
      </section>
      {warehouse.data?.summary?.note && <Notice tone="amber">{warehouse.data.summary.note}</Notice>}
      <Card title="Evaluation fact table" description="Correct counts are grouped by experiment and answer strategy.">
        {warehouse.data?.summary?.correct_by_experiment_and_strategy?.length ? <div className="overflow-x-auto"><table className="w-full min-w-[600px] text-left text-sm"><thead><tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400"><th className="py-3 pr-4">Experiment</th><th className="py-3 pr-4">Mode</th><th className="py-3 pr-4">Strategy</th><th className="py-3 pr-4">Responses</th><th className="py-3">Correct</th></tr></thead><tbody>{warehouse.data.summary.correct_by_experiment_and_strategy.map((row) => <tr key={`${row.experiment_id}-${row.strategy}`} className="border-b border-slate-50 last:border-0"><td className="py-3 pr-4">#{row.experiment_id}</td><td className="py-3 pr-4">{row.execution_mode}</td><td className="py-3 pr-4 font-medium">{row.strategy}</td><td className="py-3 pr-4">{row.responses}</td><td className="py-3">{row.correct}</td></tr>)}</tbody></table></div> : <EmptyState title="No fact rows yet" description="Run experiments, evaluate their responses, then refresh the warehouse." />}
      </Card>
      <Card title="Recent ETL runs" description="The latest 20 runs, including reconciliation status.">
        {warehouse.data?.runs?.length ? <div className="space-y-2">{warehouse.data.runs.map((run) => <div key={run.run_id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-4"><div><div className="text-sm font-semibold text-slate-800">Run #{run.run_id}</div><div className="mt-1 text-xs text-slate-500">{new Date(run.started_at).toLocaleString()} {run.rejected_count != null ? `· ${run.rejected_count} rejected` : ''}</div></div><div className="flex items-center gap-2"><Badge tone={run.reconciliation_passed === false ? 'red' : run.status === 'success' ? 'green' : 'amber'}>{run.reconciliation_passed === false ? 'Reconciliation failed' : run.status}</Badge><ArrowUpRight size={16} className="text-slate-300" /></div></div>)}</div> : <EmptyState title="No ETL runs recorded" description="Refresh the warehouse to create the first run." />}
      </Card>
    </div>
  )
}

export function ExportCenter() {
  const manifest = usePageData(async () => {
    try {
      return (await api.get('/api/export/manifest')).data
    } catch (requestError) {
      if (requestError?.response?.status === 404) return null
      throw requestError
    }
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const exportNow = async () => {
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const response = await api.post('/api/export/run')
      setResult(response.data)
      manifest.setData(response.data)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  const current = result || manifest.data
  return (
    <div className="space-y-6">
      <PageHeader title="Export Center" description="Generate integrity-checked CSV snapshots for analytics tools such as Power BI." actions={<div className="flex flex-wrap gap-2"><Link className={secondaryButton} to="/analytics">Open analytics report</Link><ActionButton className={primaryButton} onClick={exportNow} busy={busy}><Download size={16} />Generate exports</ActionButton></div>} />
      {manifest.error && !current && <ErrorBox message={manifest.error} onRetry={manifest.reload} />}
      {error && <ErrorBox message={error} />}
      {!current ? <Card><EmptyState title="No export manifest found" description="Run a successful warehouse ETL, then generate the CSV exports." /></Card> : <>
        <div className="grid gap-4 sm:grid-cols-3">
          <Card><div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Warehouse run</div><div className="mt-2 text-3xl font-bold text-slate-900">#{current.warehouse_run_id}</div></Card>
          <Card><div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Exported files</div><div className="mt-2 text-3xl font-bold text-slate-900">{current.files?.length || 0}</div></Card>
          <Card><div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Integrity</div><div className="mt-2"><Badge tone={current.all_integrity_ok ? 'green' : 'red'}>{current.all_integrity_ok ? 'All checks passed' : 'Check failed'}</Badge></div></Card>
        </div>
        <Card title="Export manifest" description={`Generated ${current.exported_at_utc || 'previously'} UTC. The manifest contains checksums and row reconciliation.`}>
          <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead><tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400"><th className="py-3 pr-4">File</th><th className="py-3 pr-4">Rows</th><th className="py-3 pr-4">Integrity</th><th className="py-3">SHA-256</th></tr></thead><tbody>{current.files?.map((file) => <tr key={file.file} className="border-b border-slate-50 last:border-0"><td className="py-3 pr-4 font-semibold text-slate-800">{file.file}</td><td className="py-3 pr-4">{file.rows_in_csv} / {file.rows_in_database}</td><td className="py-3 pr-4"><Badge tone={file.integrity_ok ? 'green' : 'red'}>{file.integrity_ok ? 'Verified' : 'Mismatch'}</Badge></td><td className="max-w-[200px] truncate py-3 font-mono text-[11px] text-slate-500" title={file.sha256}>{file.sha256}</td></tr>)}</tbody></table></div>
          {current.note && <p className="mt-4 text-xs leading-5 text-slate-500">{current.note}</p>}
        </Card>
      </>}
    </div>
  )
}
