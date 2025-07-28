import React from 'react'

interface OverallScoreCardProps {
  score: number
}

const OverallScoreCard: React.FC<OverallScoreCardProps> = ({ score }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Overall Performance</h2>
      <div className="text-center">
        <div className={`text-5xl font-bold ${getScoreColor(score)}`}>
          {(score * 100).toFixed(1)}%
        </div>
        <p className="text-gray-500 mt-2">Overall Score</p>
      </div>
    </div>
  )
}

export default OverallScoreCard