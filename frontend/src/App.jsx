import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import NotBuilt from './pages/NotBuilt'
import AnalyticsReport from './pages/AnalyticsReport'
import {
  AnswerChecker,
  DataWarehouse,
  EvaluationCenter,
  ExperimentStudio,
  ExportCenter,
  RagInspector,
} from './pages/Workspace'
import { NAV } from './nav'

const PAGES = {
  '/analytics': AnalyticsReport,
  '/experiments': ExperimentStudio,
  '/evaluation': EvaluationCenter,
  '/rag': RagInspector,
  '/checker': AnswerChecker,
  '/warehouse': DataWarehouse,
  '/export': ExportCenter,
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        {NAV.filter((item) => item.to !== '/').map((item) => {
          const Page = PAGES[item.to]
          return (
            <Route
              key={item.to}
              path={item.to.slice(1)}
              element={Page ? <Page /> : <NotBuilt />}
            />
          )
        })}
        <Route path="*" element={<NotBuilt />} />
      </Route>
    </Routes>
  )
}