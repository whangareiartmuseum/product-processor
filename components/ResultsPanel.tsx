'use client'

interface ResultsPanelProps {
  results: any
  isProcessing: boolean
  logs?: string[]
  onStop?: () => void
}

export function ResultsPanel({ results, isProcessing, logs = [], onStop }: ResultsPanelProps) {
  // Show real-time logs during processing
  if (isProcessing || (!results && logs.length > 0)) {
    return (
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <div className="space-y-4">
          {isProcessing && (
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <p className="text-gray-700 font-medium">Processing...</p>
              </div>
              {onStop && (
                <button
                  onClick={onStop}
                  className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                >
                  Stop Process
                </button>
              )}
            </div>
          )}
          
          {logs.length > 0 && (
            <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Live Progress</h4>
              <div className="space-y-1 max-h-[400px] overflow-y-auto">
                {logs.map((log: string, index: number) => {
                  // Parse and format special log types
                  const isSuccess = log.includes('✅')
                  const isError = log.includes('❌')
                  const isProgress = log.includes('Processing') || log.includes('Fetching') || log.includes('Found')
                  const isInfo = log.includes('ℹ️') || log.includes('📊')
                  
                  return (
                    <p 
                      key={index} 
                      className={`text-sm font-mono ${
                        isSuccess ? 'text-green-700' : 
                        isError ? 'text-red-700' : 
                        isProgress ? 'text-blue-700 font-semibold' :
                        isInfo ? 'text-indigo-700' :
                        'text-gray-700'
                      }`}
                    >
                      {log}
                    </p>
                  )
                })}
              </div>
            </div>
          )}
          
          {!isProcessing && logs.length === 0 && (
            <p className="text-gray-600 text-center">Waiting for process to start...</p>
          )}
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
        
        {/* Show all logs including those from streaming */}
        {(results.logs || logs).length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Process Logs</h4>
            <div className="space-y-1 max-h-[300px] overflow-y-auto">
              {(results.logs || logs).map((log: string, index: number) => {
                const isSuccess = log.includes('✅')
                const isError = log.includes('❌')
                const isProgress = log.includes('Processing') || log.includes('Fetching') || log.includes('Found')
                const isInfo = log.includes('ℹ️') || log.includes('📊')
                
                return (
                  <p 
                    key={index} 
                    className={`text-sm font-mono ${
                      isSuccess ? 'text-green-700' : 
                      isError ? 'text-red-700' : 
                      isProgress ? 'text-blue-700' :
                      isInfo ? 'text-indigo-700' :
                      'text-gray-700'
                    }`}
                  >
                    {log}
                  </p>
                )
              })}
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