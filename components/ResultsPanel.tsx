'use client'

import { InstagramPostDisplay } from './InstagramPostDisplay'

interface ResultsPanelProps {
  results: any
  isProcessing: boolean
  logs?: string[]
  onStop?: () => void
  activeProcessId?: string
  onRunProcess?: (endpoint: string, params: any) => void
}

export function ResultsPanel({ results, isProcessing, logs = [], onStop, activeProcessId, onRunProcess }: ResultsPanelProps) {
  // Get process-specific information
  const getProcessInfo = (processId: string | undefined) => {
    switch (processId) {
      case 'extract-all':
        return {
          title: 'Extracting Colors for All Products',
          steps: [
            '📡 Connecting to Shopify API',
            '📥 Fetching all products from your store',
            '🔍 Analyzing which products have images',
            '🎨 For each product:',
            '   • Downloading product image',
            '   • Extracting dominant color',
            '   • Generating complementary color',
            '   • Calculating text color with proper contrast',
            '   • Updating product metafields'
          ],
          estimate: 'This typically takes 30-60 seconds per 100 products'
        }
      case 'extract-missing':
        return {
          title: 'Updating Products with Missing Colors',
          steps: [
            '📡 Connecting to Shopify API',
            '📥 Fetching all products',
            '🔍 Identifying products missing color data',
            '🎨 Processing only products that need updates',
            '💾 Saving color metafields'
          ],
          estimate: 'This is usually faster as it only processes products that need updates'
        }
      case 'contrast-report':
        return {
          title: 'Generating Color Contrast Report',
          steps: [
            '📡 Connecting to Shopify API',
            '📥 Fetching all products with color data',
            '📊 Calculating contrast ratios',
            '✅ Checking WCAG compliance',
            '📝 Generating detailed report'
          ],
          estimate: 'This typically takes 10-30 seconds'
        }
      case 'recommendations':
        return {
          title: 'Generating AI Product Recommendations',
          steps: [
            '📡 Connecting to Shopify API',
            '📥 Fetching all products',
            '🤖 Generating embeddings with OpenAI',
            '🔍 Finding similar products',
            '✨ Creating personalized recommendations',
            '💾 Saving recommendations to metafields'
          ],
          estimate: 'This can take 2-5 minutes depending on product count'
        }
      case 'missing-descriptions':
        return {
          title: 'Generating Missing Descriptions Report',
          steps: [
            '📡 Connecting to Shopify API',
            '📥 Fetching all products from your store',
            '🔍 Checking each product for descriptions',
            '📝 Identifying products with missing descriptions',
            '📊 Generating summary statistics',
            '📋 Creating detailed report'
          ],
          estimate: 'This typically takes 15-30 seconds for all products'
        }
      case 'instagram-post':
        return {
          title: 'Generating Instagram Post',
          steps: [
            '📡 Connecting to Shopify API',
            '🎲 Selecting random product with colors',
            '🖼️ Creating Instagram-ready image',
            '🤖 Generating AI caption with OpenAI',
            '⏰ Setting post schedule',
            '✨ Preparing preview'
          ],
          estimate: 'This typically takes 20-30 seconds'
        }
      default:
        return {
          title: 'Processing',
          steps: ['Working on your request...'],
          estimate: 'This may take a few moments'
        }
    }
  }

  // Show real-time logs during processing
  if (isProcessing || (!results && logs.length > 0)) {
    const processInfo = getProcessInfo(activeProcessId)
    
    return (
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <div className="space-y-4">
          {isProcessing && (
            <>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <div>
                    <p className="text-gray-800 font-semibold text-lg">{processInfo.title}</p>
                    <p className="text-gray-600 text-sm">{processInfo.estimate}</p>
                  </div>
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
              
              {/* Show what's happening */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h4 className="font-semibold text-blue-900 mb-3">What's happening:</h4>
                <div className="space-y-2">
                  {processInfo.steps.map((step, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <span className="text-blue-600 mt-0.5">
                        {step.startsWith('   ') ? '  ▸' : '•'}
                      </span>
                      <span className="text-sm text-blue-800">{step.replace('   ', '')}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Progress animation */}
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <div className="flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <p className="text-sm text-gray-600">
                    Please wait while we process your request. You'll see detailed results when complete.
                  </p>
                </div>
              </div>
              
              {/* Note about Vercel */}
              <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                <p className="text-xs text-amber-800">
                  <span className="font-semibold">Note:</span> On Vercel, progress updates appear after processing completes. 
                  The process is working in the background and will show all logs when finished.
                </p>
              </div>
            </>
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

  // Handle Instagram post regeneration
  const handleInstagramRegenerate = () => {
    if (onRunProcess) {
      const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
      const endpoint = isVercel ? '/api/instagram-generate' : '/api/instagram/generate'
      onRunProcess(endpoint, {})
    }
  }

  // Handle marking Instagram post as posted
  const handleMarkPosted = async (productId: string) => {
    try {
      await fetch('/api/instagram/mark-posted', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ productId })
      })
    } catch (error) {
      console.error('Failed to mark as posted:', error)
    }
  }

  // Special handling for Instagram posts
  if (results.success && results.image_data && results.caption && activeProcessId === 'instagram-post') {
    return (
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <InstagramPostDisplay
          postData={results}
          onRegenerate={handleInstagramRegenerate}
          onMarkPosted={handleMarkPosted}
        />
      </div>
    )
  }

  // Handle Instagram results
  if (activeProcessId === 'instagram-post' && results.product_id) {
    return (
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6 max-h-[600px] overflow-y-auto">
        <InstagramPostDisplay 
          postData={results}
          onRegenerate={handleInstagramRegenerate}
          onMarkPosted={handleMarkPosted}
        />
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
        
        {/* Special handling for missing descriptions report */}
        {results.products_missing_descriptions && (
          <div className="bg-amber-50 border border-amber-200 rounded-md p-4">
            <h4 className="font-semibold text-amber-900 mb-3">Products Missing Descriptions ({results.products_missing_descriptions.length})</h4>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {results.products_missing_descriptions.slice(0, 20).map((product: any, index: number) => (
                <div key={product.id} className="bg-white border border-amber-300 rounded p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-900">{index + 1}. {product.title}</p>
                      <div className="text-sm text-gray-600 mt-1">
                        <span>ID: {product.id}</span>
                        {product.handle && <span className="ml-3">Handle: {product.handle}</span>}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">
                        {product.product_type && <span>Type: {product.product_type}</span>}
                        {product.vendor && <span className="ml-3">Vendor: {product.vendor}</span>}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 text-right">
                      {product.created_at && <div>Created: {new Date(product.created_at).toLocaleDateString()}</div>}
                      {product.total_inventory !== undefined && <div>Stock: {product.total_inventory}</div>}
                    </div>
                  </div>
                </div>
              ))}
              {results.products_missing_descriptions.length > 20 && (
                <p className="text-sm text-amber-700 italic text-center py-2">
                  ... and {results.products_missing_descriptions.length - 20} more products
                </p>
              )}
            </div>
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