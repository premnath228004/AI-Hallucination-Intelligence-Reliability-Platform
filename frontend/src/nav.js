import {
  ClipboardCheck,
  ChartNoAxesCombined,
  Database,
  Download,
  FlaskConical,
  LayoutDashboard,
  Search,
  ShieldCheck,
} from 'lucide-react'

export const NAV = [
  {
    to: '/',
    label: 'Overview',
    icon: LayoutDashboard,
    ready: true,
    description: 'System status and reliability metrics.',
  },
  {
    to: '/experiments',
    label: 'Experiment Studio',
    icon: FlaskConical,
    ready: true,
    description: 'Run and compare prompting strategies.',
  },
  {
    to: '/evaluation',
    label: 'Evaluation Center',
    icon: ClipboardCheck,
    ready: true,
    description: 'Evaluate AI responses and factual claims.',
  },
  {
    to: '/rag',
    label: 'RAG Inspector',
    icon: Search,
    ready: true,
    description: 'Inspect retrieved evidence and relevance.',
  },
  {
    to: '/checker',
    label: 'Answer Checker',
    icon: ShieldCheck,
    ready: true,
    description: 'Check answers against supporting evidence.',
  },
  {
    to: '/warehouse',
    label: 'Data Warehouse',
    icon: Database,
    ready: true,
    description: 'Explore analytical tables and ETL workflows.',
  },
  {
    to: '/analytics',
    label: 'Analytics & Reports',
    icon: ChartNoAxesCombined,
    ready: true,
    description: 'Slice warehouse results and share dashboard reviews.',
  },
  {
    to: '/export',
    label: 'Export Center',
    icon: Download,
    ready: true,
    description: 'Prepare analytical data exports.',
  },
]