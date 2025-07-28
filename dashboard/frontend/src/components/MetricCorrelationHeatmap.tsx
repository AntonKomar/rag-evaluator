import React from 'react'

interface MetricCorrelationHeatmapProps {
  correlationData: {
    metrics: string[]
    correlationMatrix: number[][]
  }
}

const MetricCorrelationHeatmap: React.FC<MetricCorrelationHeatmapProps> = ({ correlationData }) => {
  const getCorrelationColor = (value: number): string => {
  if (value < -0.8) return 'bg-purple-800 text-white'
  if (value < -0.6) return 'bg-purple-600 text-white'
  if (value < -0.4) return 'bg-purple-400 text-white'
  if (value < -0.2) return 'bg-purple-200 text-gray-800'
  if (value < -0.05) return 'bg-purple-50 text-gray-800'
  if (value < 0.05) return 'bg-gray-100 text-gray-800'
  if (value < 0.2) return 'bg-emerald-50 text-gray-800'
  if (value < 0.4) return 'bg-emerald-200 text-gray-800'
  if (value < 0.6) return 'bg-emerald-400 text-gray-800'
  if (value < 0.8) return 'bg-emerald-600 text-white'
  return 'bg-emerald-800 text-white'
}


  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Metric Correlations</h2>
      <div className="overflow-x-auto">
        <table className="text-xs">
          <thead>
            <tr>
              <th className="px-2 py-1 text-left text-xs font-medium">Metric</th>
              {correlationData.metrics.map((metric) => (
                <th key={metric} className="px-2 py-1 text-center text-xs font-medium">
                  {metric.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {correlationData.metrics.map((metric1, i) => (
              <tr key={metric1}>
                <td className="px-2 py-1 font-medium capitalize text-xs">{metric1.replace(/_/g, ' ')}</td>
                {correlationData.metrics.map((metric2, j) => {
                  const value = correlationData.correlationMatrix[i][j]
                  const color = getCorrelationColor(value)
                  
                  return (
                    <td key={metric2} className="px-2 py-1 text-center">
                      <div className={`${color} rounded px-1 py-0.5 text-xs font-medium`}>
                        {value.toFixed(2)}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default MetricCorrelationHeatmap