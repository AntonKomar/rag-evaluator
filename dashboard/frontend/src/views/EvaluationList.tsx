// Example: Alternative implementation using custom hook
import React from 'react'
import { Link } from 'react-router-dom'
import { ChartBarIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import type { Evaluation } from '../types'
import { formatDate, formatFileSize, API_BASE } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useApi } from '../hooks/useApi'

const EvaluationsList: React.FC = () => {
  const { data: evaluations, loading, error, refetch } = useApi<Evaluation[]>(
    `${API_BASE}/api/evaluations`
  )


  if (loading) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSpinner size="large" className="mt-8" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mt-8">
          <ErrorAlert 
            title="Failed to load evaluations"
            message={error}
            onRetry={refetch}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-semibold text-gray-900">Evaluation Results</h1>
          <p className="mt-2 text-sm text-gray-700">
            View and analyze all RAG system evaluation results
          </p>
        </div>
      </div>

      {evaluations && evaluations.length > 0 ? (
        <div className="mt-8">
          <div className="overflow-hidden bg-white shadow sm:rounded-md">
            <ul role="list" className="divide-y divide-gray-200">
              {evaluations.map((evaluation) => (
                <li key={evaluation.id}>
                  <Link
                    to={`/evaluation/${evaluation.id}`}
                    className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <ChartBarIcon className="h-12 w-12 text-indigo-600" />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-indigo-600">
                            {evaluation.id}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatDate(evaluation.timestamp)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          {formatFileSize(evaluation.size)}
                        </span>
                        <ChevronRightIcon className="ml-2 h-5 w-5 text-gray-400" />
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <div className="mt-8 text-center">
          <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No evaluations</h3>
          <p className="mt-1 text-sm text-gray-500">
            Run an evaluation to see results here
          </p>
        </div>
      )}
    </div>
  )
}

export default EvaluationsList