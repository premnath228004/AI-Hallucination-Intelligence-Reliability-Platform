import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import NotBuilt from './pages/NotBuilt'
import { NAV } from './nav'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        {NAV.filter((item) => item.to !== '/').map((item) => (
          <Route key={item.to} path={item.to.slice(1)} element={<NotBuilt />} />
        ))}
        <Route path="*" element={<NotBuilt />} />
      </Route>
    </Routes>
  )
}