'use client'

import { useState } from 'react'
import { ProcessPanel } from '@/components/ProcessPanel'
import { ResultsPanel } from '@/components/ResultsPanel'

export default function Home() {
  const [activeProcess, setActiveProcess] = useState<string | null>(null)
  const [results, setResults] = useState<any>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  // Check if we're on Vercel
  const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')

  const processes = [
    {
      id: 'extract-all',
      title: 'Extract Colors - All Products',
      description: 'Extract and update colors for all products in your store',
      icon: '🎨',
      endpoint: isVercel ? '/api/colors-all' : '/api/colors/extract-all'
    },
    {
      id: 'extract-missing',
      title: 'Extract Colors - Missing Only',
      description: 'Update products that are missing color metadata',
      icon: '🔍',
      endpoint: isVercel ? '/api/colors-missing' : '/api/colors/extract-missing'
    },
    {
      id: 'extract-single',
      title: 'Process Single Product',
      description: 'Extract colors from a specific product',
      icon: '📦',
      endpoint: isVercel ? '/api/colors-single' : '/api/colors/extract-single',
      requiresInput: true
    },
    {
      id: 'contrast-report',
      title: 'Color Contrast Report',
      description: 'Generate a report of color contrast issues',
      icon: '📊',
      endpoint: isVercel ? '/api/colors-report' : '/api/colors/contrast-report'
    },
    {
      id: 'recommendations',
      title: 'Product Recommendations',
      description: 'Generate AI-powered product recommendations',
      icon: '🤖',
      endpoint: isVercel ? '/api/recommendations' : '/api/recommendations/generate'
    },
    {
      id: 'inspect-metafields',
      title: 'Inspect Metafields',
      description: 'View color metafields for the first 10 products',
      icon: '🔎',
      endpoint: isVercel ? '/api/metafields-inspect' : '/api/metafields/inspect'
    },
    {
      id: 'clear-metafields',
      title: 'Clear Metafields',
      description: 'Clear unwanted metafields from products',
      icon: '🧹',
      endpoint: '/api/metafields/clear'
    },
    {
      id: 'cleanup-metafields',
      title: 'Delete Metafields',
      description: 'Permanently delete unwanted metafields',
      icon: '🗑️',
      endpoint: '/api/metafields/cleanup'
    }
  ]

  const runProcess = async (endpoint: string, params: any) => {
    try {
      setIsProcessing(true)
      setResults(null)

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Process failed')
      }

      setResults(data)
    } catch (error: any) {
      setResults({
        success: false,
        error: error.message || 'An unexpected error occurred'
      })
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            Product Processor
          </h1>
          <p className="text-xl text-gray-600">
            Manage colors, recommendations, and metadata for your Shopify products
          </p>
          {isVercel && (
            <p className="text-sm text-blue-600 mt-2">
              Running on Vercel with Python Serverless Functions
            </p>
          )}
        </header>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">
              Available Processes
            </h2>
            {processes.map((process) => (
              <ProcessPanel
                key={process.id}
                process={process}
                isActive={activeProcess === process.id}
                onSelect={() => setActiveProcess(process.id)}
                onRun={(params: any) => {
                  const currentProcess = processes.find(p => p.id === activeProcess)
                  if (currentProcess) {
                    runProcess(currentProcess.endpoint, params)
                  }
                }}
                isProcessing={isProcessing && activeProcess === process.id}
              />
            ))}
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">
              Results
            </h2>
            <ResultsPanel results={results} isProcessing={isProcessing} />
          </div>
        </div>
      </div>
    </main>
  )
}
