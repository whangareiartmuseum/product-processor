'use client'

interface ResultsPanelProps {
  results: any
  isProcessing: boolean
}

export function ResultsPanel({ results, isProcessing }: ResultsPanelProps) {
  if (isProcessing) {
    return (
      <div className="bg-white rounded-lg border-2 border-gray-200 p-8">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="text-gray-600">Processing... This may take a few minutes.</p>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="bg-white rounded-lg border-2 border-gray-200 p-8">
        <div className="text-center text-gray-500">
          <p className="text-lg">No results yet</p>
          <p className="text-sm mt-2">Select and run a process to see results here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-6 max-h-[600px] overflow-y-auto">
      <div className="space-y-4">
        {results.success && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <p className="text-green-800 font-medium">✅ Process completed successfully</p>
          </div>
        )}
        
        {results.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800 font-medium">❌ Error occurred</p>
            <p className="text-red-600 text-sm mt-1">{results.error}</p>
          </div>
        )}
        
        {results.summary && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
            <pre className="text-sm text-blue-800 whitespace-pre-wrap">
              {JSON.stringify(results.summary, null, 2)}
            </pre>
          </div>
        )}
        
        {results.logs && results.logs.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Process Logs</h4>
            <div className="space-y-1 max-h-[300px] overflow-y-auto">
              {results.logs.map((log: string, index: number) => (
                <p key={index} className="text-sm text-gray-700 font-mono">
                  {log}
                </p>
              ))}
            </div>
          </div>
        )}
        
        {results.data && (
          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Detailed Results</h4>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(results.data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
} 