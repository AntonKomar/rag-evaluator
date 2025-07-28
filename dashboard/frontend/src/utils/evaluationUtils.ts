import { IndividualScore, RETRIEVAL_METRICS, GENERATION_METRICS, SYSTEM_METRICS } from '../types'

export const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

export const getScoreBarColor = (score: number): string => {
  if (score >= 0.8) return 'bg-green-500'
  if (score >= 0.6) return 'bg-yellow-500'
  return 'bg-red-500'
}

export const calculateCorrelationMatrix = (allIndividualScores: IndividualScore[]) => {
  // Group scores by metric
  const metricScores: Record<string, number[]> = {}
  allIndividualScores.forEach(score => {
    if (!metricScores[score.metric_id]) {
      metricScores[score.metric_id] = []
    }
    metricScores[score.metric_id].push(score.score)
  })
  
  const metrics = Object.keys(metricScores)
  const correlationMatrix: number[][] = []
  
  // Calculate simplified Pearson correlation
  metrics.forEach((metric1, i) => {
    correlationMatrix[i] = []
    metrics.forEach((metric2, j) => {
      if (i === j) {
        correlationMatrix[i][j] = 1
      } else {
        const scores1 = metricScores[metric1]
        const scores2 = metricScores[metric2]
        const minLength = Math.min(scores1.length, scores2.length)
        
        if (minLength > 1) {
          const mean1 = scores1.slice(0, minLength).reduce((a, b) => a + b, 0) / minLength
          const mean2 = scores2.slice(0, minLength).reduce((a, b) => a + b, 0) / minLength
          
          let numerator = 0
          let denominator1 = 0
          let denominator2 = 0
          
          for (let k = 0; k < minLength; k++) {
            const diff1 = scores1[k] - mean1
            const diff2 = scores2[k] - mean2
            numerator += diff1 * diff2
            denominator1 += diff1 * diff1
            denominator2 += diff2 * diff2
          }
          
          const correlation = denominator1 && denominator2 
            ? numerator / Math.sqrt(denominator1 * denominator2)
            : 0
          correlationMatrix[i][j] = correlation
        } else {
          correlationMatrix[i][j] = 0
        }
      }
    })
  })
  
  return { metrics, correlationMatrix }
}

export const calculateComponentAverages = (metricsSummary: Record<string, any>) => {
  const retrievalMetrics = [...RETRIEVAL_METRICS]
  const generationMetrics = [...GENERATION_METRICS]
  const systemMetrics = [...SYSTEM_METRICS]
  
  let retrievalSum = 0
  let retrievalCount = 0
  let generationSum = 0
  let generationCount = 0
  let systemSum = 0
  let systemCount = 0
  
  Object.entries(metricsSummary).forEach(([metric, data]) => {
    if (retrievalMetrics.includes(metric as any)) {
      retrievalSum += data.average_score
      retrievalCount++
    } else if (generationMetrics.includes(metric as any)) {
      generationSum += data.average_score
      generationCount++
    } else if (systemMetrics.includes(metric as any)) {
      systemSum += data.average_score
      systemCount++
    }
  })
  
  const retrievalAvg = retrievalCount > 0 ? (retrievalSum / retrievalCount) * 100 : 0
  const generationAvg = generationCount > 0 ? (generationSum / generationCount) * 100 : 0
  const systemAvg = systemCount > 0 ? (systemSum / systemCount) * 100 : 0
  
  const overallSystemAvg = (retrievalAvg + generationAvg + systemAvg) / 3
  
  return {
    retrievalAvg,
    generationAvg,
    systemAvg,
    overallSystemAvg
  }
}