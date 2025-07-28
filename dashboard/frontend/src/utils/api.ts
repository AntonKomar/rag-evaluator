import axios, { AxiosInstance } from 'axios'
import type { Evaluation, EvaluationDetail, Statistics, QuestionSet, TestCase } from '../types'

export const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  }
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.message)
    } else {
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const apiClient = {
  evaluations: {
    list: () => api.get<Evaluation[]>('/api/evaluations'),
    get: (id: string) => api.get<EvaluationDetail>(`/api/evaluations/${id}`),
    statistics: (id: string) => api.get<Statistics>(`/api/statistics/${id}`),
    getComparisonData: async (evalId: string, compId: string) => {
      const [evalResponse, statsResponse] = await Promise.all([
        api.get<EvaluationDetail>(`/api/evaluations/${compId}`),
        api.get<Statistics>(`/api/statistics/${compId}`)
      ])
      return {
        evaluation: evalResponse.data,
        statistics: statsResponse.data
      }
    }
  },
  questions: {
    list: () => api.get<QuestionSet[]>('/api/questions'),
    get: (id: string) => api.get<TestCase[]>(`/api/questions/${id}`)
  }
}

export const formatDate = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString()
}

export const formatFileSize = (bytes: number): string => {
  const kb = bytes / 1024
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
}