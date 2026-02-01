import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import WorkflowPage from './pages/WorkflowPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/workflow/:id" element={<WorkflowPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
