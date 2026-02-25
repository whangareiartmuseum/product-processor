'use client'

import { useState } from 'react'

interface Process {
  id: string
  title: string
  description: string
  icon: string
  endpoint: string
  requiresInput?: boolean
  streaming?: boolean
}

interface ProcessPanelProps {
  process: Process
  isActive: boolean
  onSelect: () => void
  onRun: (process: Process, params: any) => void
  isProcessing: boolean
}

export function ProcessPanel({
  process,
  isActive,
  onSelect,
  onRun,
  isProcessing
}: ProcessPanelProps) {
  const [inputValue, setInputValue] = useState('')

  const handleRun = () => {
    const params = process.requiresInput ? { input: inputValue } : {}
    onRun(process, params)
  }

  return (
    <div
      className={`rounded-lg border-2 p-6 cursor-pointer transition-all ${
        isActive
          ? 'border-blue-500 bg-blue-50 shadow-lg'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start space-x-4">
        <span className="text-3xl">{process.icon}</span>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800">
            {process.title}
          </h3>
          <p className="text-sm text-gray-600 mt-1">{process.description}</p>
          
          {isActive && process.requiresInput && (
            <div className="mt-4" onClick={(e) => e.stopPropagation()}>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter product ID or handle"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
          
          {isActive && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleRun()
              }}
              disabled={isProcessing || (process.requiresInput && !inputValue)}
              className={`mt-4 px-6 py-2 rounded-md font-medium transition-colors ${
                isProcessing || (process.requiresInput && !inputValue)
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {isProcessing ? 'Processing...' : 'Run Process'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
} 