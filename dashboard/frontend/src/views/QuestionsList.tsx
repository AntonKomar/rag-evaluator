import React from 'react'
import { useNavigate } from 'react-router-dom'
import { DocumentTextIcon } from '@heroicons/react/24/outline'
import type { QuestionSet } from '../types'
import { API_BASE, formatDate } from '../utils/api'
import { useApi } from '../hooks/useApi'

const QuestionsList: React.FC = () => {
  const navigate = useNavigate()
  const { data: questionSets, loading, error } = useApi<QuestionSet[]>(
    `${API_BASE}/api/questions`
  )

  const navigateToDetail = (id: string) => {
    navigate(`/questions/${id}`)
  }

  if (loading) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mt-8 flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mt-8 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-semibold text-gray-900">Test Questions</h1>
          <p className="mt-2 text-sm text-gray-700">
            Generated test cases for RAG evaluation
          </p>
        </div>
      </div>

      {questionSets && questionSets.length > 0 ? (
        <div className="mt-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {questionSets.map((set) => (
              <div
                key={set.id}
                className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigateToDetail(set.id)}
              >
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <DocumentTextIcon className="h-8 w-8 text-indigo-600" />
                    </div>
                    <div className="ml-4 flex-1">
                      <h3 className="text-lg font-medium text-gray-900">{set.id}</h3>
                      <p className="text-sm text-gray-500">{formatDate(set.timestamp)}</p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">Total Questions</span>
                      <span className="text-sm font-semibold text-gray-900">{set.total_questions}</span>
                    </div>
                    <div className="mt-2 space-y-1">
                      {Object.entries(set.question_types).map(([type, count]) => (
                        <div
                          key={type}
                          className="flex items-center justify-between text-xs"
                        >
                          <span className="text-gray-500 capitalize">{type}</span>
                          <span className="text-gray-700">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-8 text-center">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No question sets</h3>
          <p className="mt-1 text-sm text-gray-500">
            Generate test questions to see them here
          </p>
        </div>
      )}
    </div>
  )
}

export default QuestionsList