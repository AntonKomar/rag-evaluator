import React from 'react'
import { Radar } from 'react-chartjs-2'
import { ChartOptions } from 'chart.js'
import { GoalStatistic } from '../types'

interface GoalRadarChartProps {
  goals: GoalStatistic[]
}

const GoalRadarChart: React.FC<GoalRadarChartProps> = ({ goals }) => {
  const data = {
    labels: goals.map(g => g.name),
    datasets: [{
      label: 'Goal Performance',
      data: goals.map(g => g.score * 100),
      backgroundColor: 'rgba(99, 102, 241, 0.2)',
      borderColor: 'rgb(99, 102, 241)',
      borderWidth: 2,
      pointBackgroundColor: 'rgb(99, 102, 241)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgb(99, 102, 241)'
    }]
  }

  const options: ChartOptions<'radar'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value) => `${value}%`
        }
      }
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Goal Attainment Profile</h2>
      <div className="h-64">
        <Radar data={data} options={options} />
      </div>
    </div>
  )
}

export default GoalRadarChart