import React, { useState, useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Bar, Doughnut, Radar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  RadialLinearScale,
  PointElement,
  LineElement
} from 'chart.js'
import type { IndividualScore } from '../types'

import {
  OverallScoreCard,
  GoalsPerformance,
  GoalRadarChart,
  MetricsSummaryChart,
  MetricDistributionChart,
  MetricCorrelationHeatmap,
  ComparisonControls,
  TimeSeriesChart,
  RetrievalGenerationScatter,
  IndividualTestResults
} from '../components'

import { 
  getScoreColor, 
  calculateCorrelationMatrix,
  calculateComponentAverages 
} from '../utils/evaluationUtils'

import { useComparisonData, useEvaluationDetail } from '../hooks/useApi'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  PointElement,
  LineElement
)

const EvaluationDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  const { evaluation, statistics, availableEvaluations, loading, error } = useEvaluationDetail(id)
  
  const [selectedComparisons, setSelectedComparisons] = useState<string[]>([])
  const [showComparison, setShowComparison] = useState(false)
  
  const { comparisonData } = useComparisonData(selectedComparisons)

  const hasIndividualScores = useMemo(() => {
    if (!evaluation) return false
    return evaluation.goals.some(goal => 
      goal.questions.some(q => 
        q.metrics.some(m => m.individual_scores && m.individual_scores.length > 0)
      )
    )
  }, [evaluation])

  const allIndividualScores = useMemo(() => {
    if (!evaluation) return []
    const scores: IndividualScore[] = []
    evaluation.goals.forEach(goal => {
      goal.questions.forEach(question => {
        question.metrics.forEach(metric => {
          if (metric.individual_scores) {
            scores.push(...metric.individual_scores.map(score => ({
              ...score,
              metric_id: metric.id
            })))
          }
        })
      })
    })
    return scores
  }, [evaluation])

  const questionTypesChartData = useMemo(() => {
    if (!statistics) return { labels: [], datasets: [] }
    
    const labels = Object.keys(statistics.question_types_performance)
    const data = labels.map(key => statistics.question_types_performance[key].average)
    
    return {
      labels,
      datasets: [{
        data,
        backgroundColor: [
          'rgba(99, 102, 241, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(236, 72, 153, 0.8)',
          'rgba(248, 113, 113, 0.8)',
          'rgba(251, 146, 60, 0.8)'
        ]
      }]
    }
  }, [statistics])

  const chartOptions: ChartOptions<'bar'> = {
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
          label: (context) => `${context.dataset.label}: ${(context.parsed.y).toFixed(1)}%`
        }
      }
    }
  }

  const doughnutOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => `${context.label}: ${(Number(context.parsed) * 100).toFixed(1)}%`
        }
      },
      legend: {
        position: 'right'
      }
    }
  }

  // Chart options for Test Case Score Distribution
  const scoreDistributionOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Percentage of Test Cases (%)'
        },
        ticks: {
          callback: (value) => `${value}%`
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

  // Metric Correlation Heatmap data
  const correlationData = useMemo(() => {
    if (!evaluation || !allIndividualScores.length) return null
    return calculateCorrelationMatrix(allIndividualScores)
  }, [evaluation, allIndividualScores])

  // Test Case Score Distribution (Histogram)
  const scoreDistributionData = useMemo(() => {
    if (!allIndividualScores.length) return { labels: [], datasets: [] }
    
    const bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    const binLabels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    
    const testCaseAverages: Record<string, { sum: number; count: number }> = {}
    
    allIndividualScores.forEach(score => {
      const testCaseKey = `${score.query}_${score.question_type}`
      
      if (!testCaseAverages[testCaseKey]) {
        testCaseAverages[testCaseKey] = { sum: 0, count: 0 }
      }
      
      testCaseAverages[testCaseKey].sum += score.score
      testCaseAverages[testCaseKey].count += 1
    })
    
    const binCounts = new Array(bins.length - 1).fill(0)
    const totalTestCases = Object.keys(testCaseAverages).length
    
    Object.values(testCaseAverages).forEach(({ sum, count }) => {
      const averageScore = sum / count
      
      for (let i = 0; i < bins.length - 1; i++) {
        if (averageScore >= bins[i] && averageScore < bins[i + 1]) {
          binCounts[i]++
          break
        }
      }
    })
    
    const percentages = binCounts.map(count => 
      totalTestCases > 0 ? (count / totalTestCases) * 100 : 0
    )
    
    return {
      labels: binLabels,
      datasets: [{
        label: 'Percentage of Test Cases',
        data: percentages,
        backgroundColor: 'rgba(99, 102, 241, 0.8)',
        borderColor: 'rgb(99, 102, 241)',
        borderWidth: 1
      }]
    }
  }, [allIndividualScores])

  // Retrieval vs Generation Scatter Plot data
  const scatterData = useMemo(() => {
    if (!allIndividualScores.length) return { datasets: [] }
    
    const queryScores: Record<string, Record<string, number>> = {}
    
    allIndividualScores.forEach(score => {
      const key = `${score.query}_${score.question_type}`
      if (!queryScores[key]) {
        queryScores[key] = {}
      }
      queryScores[key][score.metric_id] = score.score
    })
    
    const points: Array<{x: number, y: number}> = []
    Object.values(queryScores).forEach(scores => {
      const retrieval = scores.context_precision || scores.context_relevance || 
                       scores.context_recall || scores.context_entities_recall || 
                       scores.semantic_diversity || 0 
      const generation = scores.faithfulness || scores.answer_relevance || 
                        scores.answer_completeness || scores.factual_consistency ||
                        scores.bertscore || scores.attribution_score || 
                        scores.self_consistency || 0
      
      if (retrieval !== undefined && generation !== undefined && (retrieval > 0 || generation > 0)) {
        points.push({ x: retrieval * 100, y: generation * 100 })
      }
    })
    
    return {
      datasets: [{
        label: 'Test Cases',
        data: points,
        backgroundColor: 'rgba(99, 102, 241, 0.6)',
        borderColor: 'rgb(99, 102, 241)',
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    }
  }, [allIndividualScores])

  // Metric Heatmap by Question Type
  const metricTypeHeatmapData = useMemo(() => {
    if (!statistics || !Object.keys(statistics.question_types_performance).length || !allIndividualScores.length) return null
    
    const questionTypes = Object.keys(statistics.question_types_performance)
    const metrics = Object.keys(statistics.metrics_summary)
    
    // Group individual scores by metric and question type
    const scoresByMetricAndType: Record<string, Record<string, number[]>> = {}
    
    allIndividualScores.forEach(score => {
      if (!scoresByMetricAndType[score.metric_id]) {
        scoresByMetricAndType[score.metric_id] = {}
      }
      if (!scoresByMetricAndType[score.metric_id][score.question_type]) {
        scoresByMetricAndType[score.metric_id][score.question_type] = []
      }
      scoresByMetricAndType[score.metric_id][score.question_type].push(score.score)
    })
    
    // Calculate average for each metric-question type combination
    const heatmapData: number[][] = []
    
    questionTypes.forEach((type, i) => {
      heatmapData[i] = []
      metrics.forEach((metric, j) => {
        const scores = scoresByMetricAndType[metric]?.[type]
        if (scores && scores.length > 0) {
          heatmapData[i][j] = scores.reduce((sum, s) => sum + s, 0) / scores.length
        } else {
          heatmapData[i][j] = statistics.metrics_summary[metric]?.average_score || 0
        }
      })
    })
    
    if (statistics.metric_question_type_performance) {
      questionTypes.forEach((type, i) => {
        metrics.forEach((metric, j) => {
          const performance = statistics.metric_question_type_performance?.[metric]?.[type]
          if (performance) {
            heatmapData[i][j] = performance.average
          }
        })
      })
    }
    
    return { questionTypes, metrics, heatmapData }
  }, [statistics, allIndividualScores])


  const getHeatmapColor = (value: number) => {
    if (value >= 0.8) return 'bg-green-500 text-white'
    if (value >= 0.6) return 'bg-green-300 text-gray-800'
    if (value >= 0.4) return 'bg-yellow-300 text-gray-800'
    if (value >= 0.2) return 'bg-orange-300 text-gray-800'
    return 'bg-red-300 text-gray-800'
  }


  // Multi-Evaluation Heatmap Data
  const multiEvaluationHeatmapData = useMemo(() => {
    if (!showComparison || selectedComparisons.length === 0) return null
    
    const evaluations = []
    
    if (statistics && Object.keys(statistics.question_types_performance).length > 0) {
      const questionTypes = Object.keys(statistics.question_types_performance)
      const metrics = Object.keys(statistics.metrics_summary)
      
      const heatmapData: number[][] = []
      
      questionTypes.forEach((type, i) => {
        heatmapData[i] = []
        metrics.forEach((metric, j) => {
          if (statistics.metric_question_type_performance?.[metric]?.[type]) {
            heatmapData[i][j] = statistics.metric_question_type_performance[metric][type].average
          } else {
            // Fallback to overall metric average
            heatmapData[i][j] = statistics.metrics_summary[metric]?.average_score || 0
          }
        })
      })
      
      evaluations.push({
        id: id!,
        name: `Current (${id})`,
        questionTypes,
        metrics,
        heatmapData
      })
    }
    
    // Add comparison evaluations
    selectedComparisons.forEach(compId => {
      const compStats = comparisonData[compId]?.statistics
      if (compStats && Object.keys(compStats.question_types_performance).length > 0) {
        const questionTypes = Object.keys(compStats.question_types_performance)
        const metrics = Object.keys(compStats.metrics_summary)
        
        const heatmapData: number[][] = []
        
        questionTypes.forEach((type, i) => {
          heatmapData[i] = []
          metrics.forEach((metric, j) => {
            if (compStats.metric_question_type_performance?.[metric]?.[type]) {
              heatmapData[i][j] = compStats.metric_question_type_performance[metric][type].average
            } else {
              heatmapData[i][j] = compStats.metrics_summary[metric]?.average_score || 0
            }
          })
        })
        
        evaluations.push({
          id: compId,
          name: compId,
          questionTypes,
          metrics,
          heatmapData
        })
      }
    })
    
    return evaluations.length > 1 ? evaluations : null
  }, [showComparison, selectedComparisons, statistics, comparisonData, id])


  // Component-Wise Score Comparison
  const componentComparisonData = useMemo(() => {
    if (!statistics) return { labels: [], datasets: [] }
    
    const { retrievalAvg, generationAvg, overallSystemAvg } = calculateComponentAverages(statistics.metrics_summary)
    
    return {
      labels: ['Retrieval', 'Generation', 'Overall System'],
      datasets: [{
        label: 'Component Performance',
        data: [retrievalAvg, generationAvg, overallSystemAvg],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(99, 102, 241, 0.8)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(139, 92, 246)',
          'rgb(99, 102, 241)'
        ],
        borderWidth: 1
      }]
    }
  }, [statistics])



   // Multi-Evaluation Component Comparison
  const multiComponentComparisonData = useMemo(() => {
    if (!showComparison || selectedComparisons.length === 0) return null
    
    const datasets = []
    const colors = [
      { bg: 'rgba(59, 130, 246, 0.8)', border: 'rgb(59, 130, 246)' },
      { bg: 'rgba(139, 92, 246, 0.8)', border: 'rgb(139, 92, 246)' },
      { bg: 'rgba(16, 185, 129, 0.8)', border: 'rgb(16, 185, 129)' },
      { bg: 'rgba(245, 158, 11, 0.8)', border: 'rgb(245, 158, 11)' },
      { bg: 'rgba(239, 68, 68, 0.8)', border: 'rgb(239, 68, 68)' }
    ]
    
    // Add current evaluation
    const currentComponents = calculateComponentAverages(statistics.metrics_summary)
    datasets.push({
      label: `Current (${id})`,
      data: [
        currentComponents.retrievalAvg,
        currentComponents.generationAvg,
        currentComponents.overallSystemAvg
      ],
      backgroundColor: colors[0].bg,
      borderColor: colors[0].border,
      borderWidth: 1
    })
    
    // Add comparison evaluations
    selectedComparisons.forEach((compId, index) => {
      const compStats = comparisonData[compId]?.statistics
      if (compStats?.metrics_summary) {
        const components = calculateComponentAverages(compStats.metrics_summary)
        datasets.push({
          label: compId,
          data: [
            components.retrievalAvg,
            components.generationAvg,
            components.overallSystemAvg
          ],
          backgroundColor: colors[(index + 1) % colors.length].bg,
          borderColor: colors[(index + 1) % colors.length].border,
          borderWidth: 1
        })
      }
    })
    
    return {
      labels: ['Retrieval', 'Generation', 'Overall System'],
      datasets
    }
  }, [showComparison, selectedComparisons, statistics, comparisonData, id])



  // Time-Series Performance Trend
  const timeSeriesData = useMemo(() => {
    if (!showComparison || selectedComparisons.length === 0) return null
    
    const currentEvalInfo = availableEvaluations.find(e => e.id === id) || 
      { id, timestamp: new Date().toISOString(), filename: id }
    
    const allEvaluations = [
      { id, timestamp: currentEvalInfo.timestamp, data: statistics },
      ...selectedComparisons.map(compId => ({
        id: compId,
        timestamp: availableEvaluations.find(e => e.id === compId)?.timestamp || '',
        data: comparisonData[compId]?.statistics
      }))
    ].filter(e => e.data).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    
    if (allEvaluations.length < 2) return null
    
    const labels = allEvaluations.map(e => new Date(e.timestamp).toLocaleDateString())
    const goalNames = statistics?.goals.map(g => g.name) || []
    
    const datasets = goalNames.map((goalName, index) => ({
      label: goalName,
      data: allEvaluations.map(e => {
        const goal = e.data?.goals.find(g => g.name === goalName)
        return goal ? goal.score * 100 : 0
      }),
      borderColor: [
        'rgb(99, 102, 241)',
        'rgb(59, 130, 246)',
        'rgb(139, 92, 246)',
        'rgb(236, 72, 153)',
        'rgb(248, 113, 113)'
      ][index % 5],
      backgroundColor: 'transparent',
      tension: 0.1
    }))
    
    return { labels, datasets }
  }, [showComparison, selectedComparisons, comparisonData, statistics, id, availableEvaluations])

  // Run Comparison Radar Chart
  const runComparisonRadarData = useMemo(() => {
    if (!showComparison || selectedComparisons.length === 0 || !statistics) return null
    
    const labels = statistics.goals.map(g => g.name)
    
    const currentDataset = {
      label: `Current (${id})`,
      data: statistics.goals.map(g => g.score * 100),
      backgroundColor: 'rgba(79, 70, 229, 0.2)',
      borderColor: 'rgb(79, 70, 229)',
      borderWidth: 2
    }
    
    const comparisonDatasets = selectedComparisons.slice(0, 2)
      .map((compId, index) => {
        const compStats = comparisonData[compId]?.statistics
        if (!compStats) return null
        
        const colors = [
          { bg: 'rgba(251, 146, 60, 0.2)', border: 'rgb(251, 146, 60)' },
          { bg: 'rgba(14, 165, 233, 0.2)', border: 'rgb(14, 165, 233)' }
        ]
        
        return {
          label: compId,
          data: labels.map(goalName => {
            const goal = compStats.goals.find(g => g.name === goalName)
            return goal ? goal.score * 100 : 0
          }),
          backgroundColor: colors[index].bg,
          borderColor: colors[index].border,
          borderWidth: 2
        }
      })
      .filter((dataset): dataset is NonNullable<typeof dataset> => dataset !== null)
    
    const datasets = [currentDataset, ...comparisonDatasets]
    
    return { labels, datasets }
  }, [showComparison, selectedComparisons, comparisonData, statistics, id])

  const radarOptions: ChartOptions<'radar'> = {
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

  const handleComparisonToggle = () => setShowComparison(!showComparison)
  
  const handleSelectionChange = (evalId: string, checked: boolean) => {
    if (checked) {
      if (selectedComparisons.length < 2) {
        setSelectedComparisons([...selectedComparisons, evalId])
      }
    } else {
      setSelectedComparisons(selectedComparisons.filter(id => id !== evalId))
    }
  }

  if (loading) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    )
  }

  if (!evaluation || !statistics) {
    return null
  }

  return (
    <div className="max-w-[82rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link to="/" className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
          ← Back to Evaluations
        </Link>
        <h1 className="mt-2 text-3xl font-bold text-gray-900">Evaluation Details</h1>
      </div>

      <div className="space-y-6">
        {/* Overall Score Card */}
        <OverallScoreCard score={evaluation.overall_score} />

        {/* Goals Performance */}
        <GoalsPerformance goals={statistics.goals} />

        {/* Goal Attainment Radar Chart */}
        <GoalRadarChart goals={statistics.goals} />

        {/* Metrics Summary Chart */}
        <MetricsSummaryChart metricsSummary={statistics.metrics_summary} />

        {/* Question Types Performance */}
        {Object.keys(statistics.question_types_performance).length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance by Question Type</h2>
            <div className="h-64">
              <Doughnut data={questionTypesChartData} options={doughnutOptions} />
            </div>
          </div>
        )}

        {/* Metric Score Distribution */}
        <MetricDistributionChart metricsSummary={statistics.metrics_summary} />

        {/* Metric Correlation Heatmap */}
        {correlationData && <MetricCorrelationHeatmap correlationData={correlationData} />}

        {/* Test Case Score Distribution Histogram */}
        {allIndividualScores.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Case Score Distribution</h2>
            <div className="h-64">
              <Bar 
                data={scoreDistributionData} 
                options={scoreDistributionOptions}
              />
            </div>
          </div>
        )}

        {/* Retrieval vs Generation Scatter Plot */}
        {scatterData.datasets[0].data.length > 0 && (
          <RetrievalGenerationScatter data={scatterData} />
        )}

        {/* Metric Heatmap by Question Type */}
        {metricTypeHeatmapData && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Heatmap by Question Type</h2>
            <div className="overflow-x-auto">
              <table className="text-xs">
                <thead>
                  <tr>
                    <th className="px-2 py-1 text-left text-xs font-medium">Question Type</th>
                    {metricTypeHeatmapData.metrics.map((metric) => (
                      <th key={metric} className="px-2 py-1 text-center text-xs font-medium">
                        {metric.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metricTypeHeatmapData.questionTypes.map((type, i) => (
                    <tr key={type}>
                      <td className="px-2 py-1 font-medium capitalize text-xs">{type.replace(/_/g, ' ')}</td>
                      {metricTypeHeatmapData.metrics.map((metric, j) => {
                        const value = metricTypeHeatmapData.heatmapData[i][j]
                        const percentage = value * 100
                        const color = getHeatmapColor(value)
                        
                        return (
                          <td key={metric} className="px-2 py-1 text-center">
                            <div className={`${color} rounded px-1 py-0.5 text-xs font-medium`}>
                              {percentage.toFixed(0)}%
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
        )}

        {/* Component-Wise Score Comparison */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Performance Comparison</h2>
          <div className="h-64">
            <Bar 
              data={componentComparisonData} 
              options={{
                ...chartOptions,
                scales: {
                  ...chartOptions.scales,
                  y: {
                    beginAtZero: true,
                    max: 100, // Changed from 1 to 100 since data is already in percentage format
                    ticks: {
                      callback: (value) => `${Number(value).toFixed(0)}%`
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* Comparison Controls */}
        <ComparisonControls
          availableEvaluations={availableEvaluations}
          currentId={id!}
          selectedComparisons={selectedComparisons}
          showComparison={showComparison}
          onToggleComparison={handleComparisonToggle}
          onSelectionChange={handleSelectionChange}
        />

        {/* Time-Series Performance Trend */}
        {showComparison && timeSeriesData && (
          <TimeSeriesChart data={timeSeriesData} />
        )}

        {/* Run Comparison Radar Chart */}
        {showComparison && runComparisonRadarData && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Multi-Run Goal Comparison</h2>
            <div className="h-64">
              <Radar data={runComparisonRadarData} options={radarOptions} />
            </div>
          </div>
        )}

         {/* Multi-Evaluation Component Comparison */}
        {showComparison && multiComponentComparisonData && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Performance Comparison</h2>
            <div className="h-64">
              <Bar 
                data={multiComponentComparisonData} 
                options={{
                  ...chartOptions,
                  plugins: {
                    ...chartOptions.plugins,
                    title: {
                      display: false
                    },
                    legend: {
                      display: true,
                      position: 'top' as const
                    }
                  },
                  scales: {
                    ...chartOptions.scales,
                    y: {
                      beginAtZero: true,
                      max: 100,
                      ticks: {
                        callback: (value) => `${Number(value).toFixed(0)}%`
                      }
                    }
                  }
                }}
              />
            </div>
          </div>
        )}

        {/* Multi-Evaluation Performance Heatmap by Question Type */}
        {showComparison && multiEvaluationHeatmapData && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Performance Heatmap by Question Type - Comparison
            </h2>
            <div className="space-y-6">
              {multiEvaluationHeatmapData.map((evalData) => (
                <div key={evalData.id} className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-800 mb-3 text-sm">
                    {evalData.name}
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="text-xs w-full">
                      <thead>
                        <tr>
                          <th className="px-2 py-1 text-left text-xs font-medium">
                            Question Type
                          </th>
                          {evalData.metrics.map((metric) => (
                            <th key={metric} className="px-2 py-1 text-center text-xs font-medium">
                              {metric.replace(/_/g, ' ')}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {evalData.questionTypes.map((type, i) => (
                          <tr key={type}>
                            <td className="px-2 py-1 font-medium capitalize text-xs">
                              {type.replace(/_/g, ' ')}
                            </td>
                            {evalData.metrics.map((metric, j) => {
                              const value = evalData.heatmapData[i][j]
                              const percentage = value * 100
                              const color = getHeatmapColor(value)
                              
                              return (
                                <td key={metric} className="px-2 py-1 text-center">
                                  <div 
                                    className={`${color} rounded px-1 py-0.5 text-xs font-medium`}
                                    title={`${metric}: ${percentage.toFixed(1)}%`}
                                  >
                                    {percentage.toFixed(0)}%
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
              ))}
            </div>
            
            {/* Legend */}
            <div className="mt-4 flex items-center gap-4 text-xs text-gray-600">
              <span className="font-medium">Score Range:</span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                80-100%
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-green-300 rounded"></div>
                60-79%
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-yellow-300 rounded"></div>
                40-59%
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-orange-300 rounded"></div>
                20-39%
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-red-300 rounded"></div>
                0-19%
              </span>
            </div>
          </div>
        )}

        {/* Heatmap Difference View */}
        {showComparison && multiEvaluationHeatmapData && multiEvaluationHeatmapData.length === 2 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Performance Difference: {multiEvaluationHeatmapData[1].name} vs {multiEvaluationHeatmapData[0].name}
            </h2>
            <div className="overflow-x-auto">
              <table className="text-xs">
                <thead>
                  <tr>
                    <th className="px-2 py-1 text-left text-xs font-medium">Question Type</th>
                    {multiEvaluationHeatmapData[0].metrics.map((metric) => (
                      <th key={metric} className="px-2 py-1 text-center text-xs font-medium">
                        {metric.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {multiEvaluationHeatmapData[0].questionTypes.map((type, i) => (
                    <tr key={type}>
                      <td className="px-2 py-1 font-medium capitalize text-xs">
                        {type.replace(/_/g, ' ')}
                      </td>
                      {multiEvaluationHeatmapData[0].metrics.map((metric, j) => {
                        const value1 = multiEvaluationHeatmapData[0].heatmapData[i][j]
                        const value2 = multiEvaluationHeatmapData[1].heatmapData[i][j]
                        const diff = value2 - value1
                        const diffPercent = diff * 100
                        
                        return (
                          <td key={metric} className="px-2 py-1 text-center">
                            <span 
                              className={`font-medium ${
                                diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-500'
                              }`}
                            >
                              {diff > 0 ? '+' : ''}{diffPercent.toFixed(1)}%
                            </span>
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Historical Comparison Table */}
        {showComparison && selectedComparisons.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Numerical Comparison</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-900">Metric</th>
                    <th className="px-4 py-2 text-center font-medium text-gray-900">
                      Current ({id})
                    </th>
                    {selectedComparisons.map((compId) => (
                      <th key={compId} className="px-4 py-2 text-center font-medium text-gray-900">
                        {compId}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr>
                    <td className="px-4 py-2 font-medium">Overall Score</td>
                    <td className={`px-4 py-2 text-center ${getScoreColor(evaluation.overall_score)}`}>
                      {(evaluation.overall_score * 100).toFixed(1)}%
                    </td>
                    {selectedComparisons.map((compId) => {
                      const compEval = comparisonData[compId]?.evaluation
                      return (
                        <td key={compId} className={`px-4 py-2 text-center ${compEval ? getScoreColor(compEval.overall_score) : ''}`}>
                          {compEval ? `${(compEval.overall_score * 100).toFixed(1)}%` : '-'}
                        </td>
                      )
                    })}
                  </tr>
                  {statistics?.goals.map((goal) => (
                    <tr key={goal.name}>
                      <td className="px-4 py-2 pl-8">{goal.name}</td>
                      <td className={`px-4 py-2 text-center ${getScoreColor(goal.score)}`}>
                        {(goal.score * 100).toFixed(1)}%
                      </td>
                      {selectedComparisons.map((compId) => {
                        const compGoal = comparisonData[compId]?.statistics?.goals.find(g => g.name === goal.name)
                        return (
                          <td key={compId} className={`px-4 py-2 text-center ${compGoal ? getScoreColor(compGoal.score) : ''}`}>
                            {compGoal ? `${(compGoal.score * 100).toFixed(1)}%` : '-'}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Detailed Results */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Results</h2>
          <div className="space-y-6">
            {evaluation.goals.map((goal) => (
              <div key={goal.name}>
                <h3 className="font-medium text-gray-900 mb-3">{goal.name}</h3>
                <div className="space-y-4 ml-4">
                  {goal.questions.map((question, qIndex) => (
                    <div key={qIndex} className="border-l-2 border-gray-200 pl-4">
                      <p className="text-sm font-medium text-gray-700">{question.text}</p>
                      <div className="mt-2 space-y-1">
                        {question.metrics.map((metric) => (
                          <div key={metric.id} className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">{metric.id}</span>
                            <span className={`font-medium ${getScoreColor(metric.value)}`}>
                              {(metric.value * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Individual Scores (if available) */}
        {hasIndividualScores && <IndividualTestResults scores={allIndividualScores} />}
      </div>
    </div>
  )
}

export default EvaluationDetailView