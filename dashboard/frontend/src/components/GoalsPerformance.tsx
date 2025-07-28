import React from 'react'
import { GoalStatistic } from '../types'

interface GoalsPerformanceProps {
  goals: GoalStatistic[]
}

const GoalsPerformance: React.FC<GoalsPerformanceProps> = ({ goals }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBarColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-500'
    if (score >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Goals Performance</h2>
      <div className="space-y-4">
        {goals.map((goal) => (
          <div key={goal.name} className="relative">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">{goal.name}</span>
              <span className={`text-sm font-medium ${getScoreColor(goal.score)}`}>
                {(goal.score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${getScoreBarColor(goal.score)}`}
                style={{ width: `${goal.score * 100}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Weight: {goal.weight} | Questions: {goal.questions_count}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default GoalsPerformance