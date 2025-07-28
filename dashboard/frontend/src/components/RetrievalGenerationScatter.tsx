import React from 'react'
import { Scatter } from 'react-chartjs-2'
import { ChartOptions } from 'chart.js'

interface RetrievalGenerationScatterProps {
  data: {
    datasets: Array<{
      label: string
      data: Array<{x: number, y: number}>
      backgroundColor: string
      borderColor: string
      pointRadius: number
      pointHoverRadius: number
    }>
  }
}

const RetrievalGenerationScatter: React.FC<RetrievalGenerationScatterProps> = ({ data }) => {
  const options: ChartOptions<'scatter'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: {
          display: true,
          text: 'Retrieval Score (%)'
        },
        min: 0,
        max: 100
      },
      y: {
        title: {
          display: true,
          text: 'Generation Score (%)'
        },
        min: 0,
        max: 100
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => `Retrieval: ${context.parsed.x.toFixed(1)}%, Generation: ${context.parsed.y.toFixed(1)}%`
        }
      }
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Retrieval vs Generation Performance</h2>
      <div className="h-64">
        <Scatter data={data} options={options} />
      </div>
    </div>
  )
}

export default RetrievalGenerationScatter