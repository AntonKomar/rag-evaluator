export interface Evaluation {
  id: string
  filename: string
  timestamp: string
  size: number
}
  
export interface EvaluationDetail {
  overall_score: number
  goals: Goal[]
}

export interface Goal {
  name: string
  score: number
  weight: number
  questions: Question[]
}

export interface Question {
  text: string
  score: number
  weight: number
  metrics: Metric[]
}

export interface Metric {
  id: string
  value: number
  weight: number
  individual_scores?: IndividualScore[]
}

export interface IndividualScore {
  metric_id: string
  query: string
  generated_answer: string
  question_type: string
  score: number
}

export interface Statistics {
  overall_score: number
  goals: GoalStatistic[]
  metrics_summary: Record<string, MetricSummary>
  question_types_performance: Record<string, QuestionTypePerformance>
  metric_question_type_performance?: Record<string, Record<string, MetricQuestionTypePerformance>>  // NEW
}

export interface MetricQuestionTypePerformance {
  average: number
  count: number
}

export interface GoalStatistic {
  name: string
  score: number
  weight: number
  questions_count: number
}

export interface MetricSummary {
  average_score: number
  min_score: number
  max_score: number
  count: number
  std_dev?: number
}

export interface QuestionTypePerformance {
  average: number
  count: number
  min?: number
  max?: number
}

export interface QuestionSet {
  id: string
  filename: string
  total_questions: number
  question_types: Record<string, number>
  timestamp: string
}

export interface TestCase {
  question: string
  ground_truth: string
  question_type: string
  entities?: string[]
}

export const RETRIEVAL_METRICS = [
  'context_precision',
  'context_relevance', 
  'context_recall',
  'context_entities_recall',
  'semantic_diversity'
] as const

export const GENERATION_METRICS = [
  'faithfulness',
  'answer_relevance',
  'answer_completeness',
  'factual_consistency',
  'bertscore',
  'attribution_score',
  'self_consistency'
] as const

export const SYSTEM_METRICS = [
  'answer_correctness',
  'multi_hop_reasoning',
  'context_utilization'
] as const

export type RetrievalMetric = typeof RETRIEVAL_METRICS[number]
export type GenerationMetric = typeof GENERATION_METRICS[number]
export type SystemMetric = typeof SYSTEM_METRICS[number]
export type MetricId = RetrievalMetric | GenerationMetric | SystemMetric