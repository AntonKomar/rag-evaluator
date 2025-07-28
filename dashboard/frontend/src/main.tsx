import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import './style.css'

// Import views
import EvaluationDetail from './views/EvaluationDetail'
import QuestionsList from './views/QuestionsList'
import QuestionsDetail from './views/QuestionsDetail'
import EvaluationsList from './views/EvaluationList'

ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<EvaluationsList />} />
          <Route path="evaluation/:id" element={<EvaluationDetail />} />
          <Route path="questions" element={<QuestionsList />} />
          <Route path="questions/:id" element={<QuestionsDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)