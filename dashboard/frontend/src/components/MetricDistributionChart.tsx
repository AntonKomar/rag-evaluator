import React from 'react'
import { Bar } from 'react-chartjs-2'
import { ChartOptions } from 'chart.js'
import { MetricSummary } from '../types'

interface MetricDistributionChartProps {
  metricsSummary: Record<string, MetricSummary>
}

const MetricDistributionChart: React.FC<MetricDistributionChartProps> = ({ metricsSummary }) => {
  const labels = Object.keys(metricsSummary)
  const minValues = labels.map(key => metricsSummary[key].min_score)
  const avgValues = labels.map(key => metricsSummary[key].average_score)
  const maxValues = labels.map(key => metricsSummary[key].max_score)
  
  const data = {
    labels,
    datasets: [
      {
        label: 'Min Score',
        data: minValues,
        backgroundColor: 'rgba(248, 113, 113, 0.6)',
        borderColor: 'rgb(248, 113, 113)',
        borderWidth: 1
      },
      {
        label: 'Average Score',
        data: avgValues,
        backgroundColor: 'rgba(99, 102, 241, 0.8)',
        borderColor: 'rgb(99, 102, 241)',
        borderWidth: 1
      },
      {
        label: 'Max Score',
        data: maxValues,
        backgroundColor: 'rgba(34, 197, 94, 0.6)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 1
      }
    ]
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
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Metric Score Distribution</h2>
      <div className="h-64">
        <Bar data={data} options={options} />
      </div>
    </div>
  )
}

export default MetricDistributionChart