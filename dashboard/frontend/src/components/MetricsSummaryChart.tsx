import React from 'react'
import { Bar } from 'react-chartjs-2'
import { ChartOptions } from 'chart.js'
import { MetricSummary } from '../types'

interface MetricsSummaryChartProps {
  metricsSummary: Record<string, MetricSummary>
}

const MetricsSummaryChart: React.FC<MetricsSummaryChartProps> = ({ metricsSummary }) => {
  const labels = Object.keys(metricsSummary)
  const data = labels.map(key => metricsSummary[key].average_score)

  const chartData = {
    labels,
    datasets: [{
      label: 'Average Score',
      data,
      backgroundColor: 'rgba(99, 102, 241, 0.8)',
      borderColor: 'rgb(99, 102, 241)',
      borderWidth: 1
    }]
  }

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        max: 1,
        ticks: {
          callback: (value) => `${(Number(value) * 100).toFixed(0)}%`
        }
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${(context.parsed.y * 100).toFixed(1)}%`
        }
      }
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Metrics Summary</h2>
      <div className="h-64">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  )
}

export default MetricsSummaryChart