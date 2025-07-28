import { useState, useEffect, useCallback } from 'react'
import axios, { AxiosError } from 'axios'
import { apiClient } from '../utils/api'
import type { EvaluationDetail, Statistics, Evaluation } from '../types'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

interface UseApiOptions {
  immediate?: boolean
}

export function useApi<T>(
  url: string, 
  options: UseApiOptions = { immediate: true }
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: options.immediate ?? true,
    error: null
  })

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    
    try {
      const response = await axios.get<T>(url)
      setState({ data: response.data, loading: false, error: null })
    } catch (err) {
      const error = err as AxiosError
      setState({ 
        data: null, 
        loading: false, 
        error: error.message || 'An error occurred' 
      })
    }
  }, [url])

  useEffect(() => {
    if (options.immediate) {
      fetchData()
    }
  }, [fetchData, options.immediate])

  return { ...state, refetch: fetchData }
}

export function useEvaluationDetail(id: string | undefined) {
  const [evaluation, setEvaluation] = useState<EvaluationDetail | null>(null)
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [availableEvaluations, setAvailableEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!id) {
        setError('No evaluation ID provided')
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)

        const [evalResponse, statsResponse, evaluationsResponse] = await Promise.all([
          apiClient.evaluations.get(id),
          apiClient.evaluations.statistics(id),
          apiClient.evaluations.list()
        ])

        setEvaluation(evalResponse.data)
        setStatistics(statsResponse.data)
        setAvailableEvaluations(evaluationsResponse.data)
      } catch (err) {
        const error = err as AxiosError
        setError(error.message || 'Failed to load evaluation details')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  return {
    evaluation,
    statistics,
    availableEvaluations,
    loading,
    error
  }
}

export function useComparisonData(selectedComparisons: string[]) {
  const [comparisonData, setComparisonData] = useState<Record<string, {
    evaluation: EvaluationDetail, 
    statistics: Statistics
  }>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadComparisonData = useCallback(async () => {
    if (selectedComparisons.length === 0) return

    setLoading(true)
    setError(null)

    try {
      const newData: Record<string, {evaluation: EvaluationDetail, statistics: Statistics}> = {}
      
      for (const compId of selectedComparisons) {
        if (!comparisonData[compId]) {
          const data = await apiClient.evaluations.getComparisonData('', compId)
          newData[compId] = data
        }
      }
      
      if (Object.keys(newData).length > 0) {
        setComparisonData(prev => ({ ...prev, ...newData }))
      }
    } catch (err) {
      const error = err as AxiosError
      setError(error.message || 'Failed to load comparison data')
      console.error(`Failed to load comparison data:`, err)
    } finally {
      setLoading(false)
    }
  }, [selectedComparisons, comparisonData])

  useEffect(() => {
    loadComparisonData()
  }, [selectedComparisons])

  return { comparisonData, loading, error }
}