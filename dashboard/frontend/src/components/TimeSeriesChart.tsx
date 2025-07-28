import React from 'react'
import { Line } from 'react-chartjs-2'
import { ChartOptions } from 'chart.js'

interface TimeSeriesChartProps {
  data: {
    labels: string[]
    datasets: Array<{
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
      tension: number
    }>
  }
}

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ data }) => {
  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Score (%)'
        }
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`
        }
      }
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Trend Over Time</h2>
      <div className="h-64">
        <Line data={data} options={options} />
      </div>
    </div>
  )
}

export default TimeSeriesChart