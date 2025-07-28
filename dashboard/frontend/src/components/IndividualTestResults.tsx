import React from 'react'
import { IndividualScore } from '../types'

interface IndividualTestResultsProps {
  scores: IndividualScore[]
}

const IndividualTestResults: React.FC<IndividualTestResultsProps> = ({ scores }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const scoresByQuery = scores.reduce((acc, score) => {
    const key = `${score.query}_${score.question_type}`;
    if (!acc[key]) {
      acc[key] = {
        query: score.query,
        question_type: score.question_type,
        generated_answer: score.generated_answer,
        metrics: []
      };
    }
    acc[key].metrics.push({
      metric_id: score.metric_id,
      score: score.score
    });
    return acc;
  }, {} as Record<string, { 
    query: string; 
    question_type: string; 
    generated_answer: string;
    metrics: Array<{ metric_id: string; score: number }> 
  }>);

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Individual Test Case Results</h2>
      <div className="space-y-6">
        {Object.values(scoresByQuery).map((questionGroup, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="mb-3">
              <h4 className="text-sm font-medium text-gray-900">
                Question {index + 1}
              </h4>
              <p className="text-sm text-gray-600 mt-1">
                <span className="font-medium text-gray-900 mr-1">Query:</span>
                {questionGroup.query}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                <span className="font-medium text-gray-900 mr-1">Generated Answer:</span>
                {questionGroup.generated_answer}
              </p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 mt-2">
                {questionGroup.question_type}
              </span>
            </div>
            
            <div className="ml-4 space-y-2">
              {questionGroup.metrics.map((metric, metricIndex) => (
                <div key={metricIndex} className="flex items-center py-1 hover:bg-gray-50 rounded">
                  <span className="text-sm text-gray-600 flex-shrink-0">
                    {metric.metric_id}
                  </span>
                  <div className="flex-grow mx-2 border-b border-dotted border-gray-300"></div>
                  <span className={`text-sm font-medium flex-shrink-0 ${getScoreColor(metric.score)}`}>
                    {(metric.score * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default IndividualTestResults