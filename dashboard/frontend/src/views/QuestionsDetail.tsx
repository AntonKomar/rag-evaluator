import React, { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { TestCase } from '../types'
import { API_BASE } from '../utils/api'
import { useApi } from '../hooks/useApi'

const QuestionsDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [selectedType, setSelectedType] = useState<string>('')
  
  const { data: questions, loading, error } = useApi<TestCase[]>(
    `${API_BASE}/api/questions/${id}`
  )

  const typeCounts = useMemo(() => {
    if (!questions) return {}
    const counts: Record<string, number> = {}
    questions.forEach(q => {
      const type = q.question_type || 'unknown'
      counts[type] = (counts[type] || 0) + 1
    })
    return counts
  }, [questions])

  const filteredQuestions = useMemo(() => {
    if (!questions) return []
    if (!selectedType) return questions
    return questions.filter(q => q.question_type === selectedType)
  }, [questions, selectedType])

  if (loading) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    )
  }

  if (!questions) {
    return null
  }

  return (
    <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link to="/questions" className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
          ← Back to Questions
        </Link>
        <h1 className="mt-2 text-3xl font-bold text-gray-900">Question Set Details</h1>
      </div>

      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(typeCounts).map(([type, count]) => (
              <div key={type} className="text-center">
                <p className="text-2xl font-bold text-indigo-600">{count}</p>
                <p className="text-sm text-gray-500 capitalize">{type}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Questions List */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Questions</h2>
          
          {/* Filter by type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Type</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">All Types</option>
              {Object.keys(typeCounts).map((type) => (
                <option key={type} value={type}>
                  {type} ({typeCounts[type]})
                </option>
              ))}
            </select>
          </div>

          {/* Questions */}
          <div className="space-y-4">
            {filteredQuestions.map((question, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 mb-2">
                      {question.question_type}
                    </span>
                    <h3 className="text-sm font-medium text-gray-900 mb-2">{question.question}</h3>
                    <div className="bg-gray-50 rounded p-3 mb-2">
                      <p className="text-sm text-gray-700">
                        <span className="font-medium">Ground Truth:</span> {question.ground_truth}
                      </p>
                    </div>
                    {question.entities && question.entities.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {question.entities.map((entity, entityIndex) => (
                          <span
                            key={entityIndex}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                          >
                            {entity}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="ml-4 text-sm text-gray-500">#{index + 1}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default QuestionsDetail