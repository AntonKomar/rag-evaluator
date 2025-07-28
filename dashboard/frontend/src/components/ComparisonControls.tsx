import React from 'react'

interface ComparisonControlsProps {
  availableEvaluations: Array<{id: string, filename: string, timestamp: string}>
  currentId: string
  selectedComparisons: string[]
  showComparison: boolean
  onToggleComparison: () => void
  onSelectionChange: (evalId: string, checked: boolean) => void
}

const ComparisonControls: React.FC<ComparisonControlsProps> = ({
  availableEvaluations,
  currentId,
  selectedComparisons,
  showComparison,
  onToggleComparison,
  onSelectionChange
}) => {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Compare with Other Evaluations</h2>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">Select up to 2 evaluations to compare</p>
          <button
            onClick={onToggleComparison}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              showComparison 
                ? 'bg-indigo-600 text-white hover:bg-indigo-700' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {showComparison ? 'Hide Comparison' : 'Show Comparison'}
          </button>
        </div>
        
        {showComparison && (
          <div className="space-y-2">
            {availableEvaluations.filter(e => e.id !== currentId).map((evalItem) => (
              <label key={evalItem.id} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedComparisons.includes(evalItem.id)}
                  onChange={(e) => onSelectionChange(evalItem.id, e.target.checked)}
                  disabled={!selectedComparisons.includes(evalItem.id) && selectedComparisons.length >= 2}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  {evalItem.id} - {new Date(evalItem.timestamp).toLocaleDateString()}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ComparisonControls