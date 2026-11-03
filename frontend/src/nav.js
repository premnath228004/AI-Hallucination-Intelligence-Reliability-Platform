import { ClipboardCheck, Database, Download, FlaskConical, LayoutDashboard, Search, ShieldCheck } from 'lucide-react'

// ready: false shows a "Soon" tag in the sidebar until the page is really built.
export const NAV = [
  {
    to: '/', label: 'Overview', icon: LayoutDashboard, ready: true,
    description: 'System status and key reliability metrics.',
    endpoints: ['GET /api/health', 'GET /api/db-info'],
  },
  {
    to: '/experiments', label: 'Experiment Studio', icon: FlaskConical, ready: false,
    description: 'Run experiments and compare Basic prompting, Improved prompting and RAG.',
    endpoints: ['POST /api/experiments', 'GET /api/experiments', 'GET /api/experiments/{id}/responses'],
  },
  {
    to: '/evaluation', label: 'Evaluation Center', icon: ClipboardCheck, ready: false,
    description: 'Evaluation results, review queue and manual review.',
    endpoints: [
      'POST /api/experiments/{id}/evaluate', 'GET /api/experiments/{id}/evaluations',
      'POST /api/evaluations/review', 'GET /api/experiments/{id}/summary',
    ],
  },
  {
    to: '/rag', label: 'RAG Inspector', icon: Search, ready: false,
    description: 'Retrieved chunks, relevance scores and evidence for RAG answers.',
    endpoints: ['GET /api/experiments/{id}/rag-inspection', 'GET /api/retrieval/search', 'GET /api/retrieval/evaluate'],
  },
  {
    to: '/checker', label: 'Answer Checker', icon: ShieldCheck, ready: false,
    description: 'Check an answer against evidence and see which sentences need review.',
    endpoints: ['POST /api/check'],
  },
  {
    to: '/warehouse', label: 'Data Warehouse', icon: Database, ready: false,
    description: 'Warehouse tables, ETL runs and reconciliation.',
    endpoints: ['POST /api/warehouse/refresh', 'GET /api/warehouse/runs', 'GET /api/warehouse/summary'],
  },
  {
    to: '/export', label: 'Export Center', icon: Download, ready: false,
    description: 'CSV exports for Power BI.',
    endpoints: ['POST /api/export/run', 'GET /api/export/manifest'],
  },
]