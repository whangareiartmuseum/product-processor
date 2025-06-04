import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // Check if we're on Vercel
    if (process.env.VERCEL_URL) {
      // Call the Python serverless function
      const pythonUrl = `https://${process.env.VERCEL_URL}/api/python/metafields-inspect`
      
      const response = await fetch(pythonUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (!response.ok) {
        throw new Error(`Python API returned ${response.status}`)
      }
      
      const data = await response.json()
      return NextResponse.json(data)
    } else {
      // In development, use the local Python runner
      const { runPythonScript } = await import('@/api_utils/pythonRunner')
      
      const result = await runPythonScript({
        scriptName: 'inspect_metafields.py'
      })
      
      return NextResponse.json({
        success: result.success,
        logs: result.logs,
        error: result.error,
        summary: {
          message: 'Metafields inspection completed',
          processType: 'inspect_metafields'
        }
      })
    }
  } catch (error: any) {
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Internal server error'
      },
      { status: 500 }
    )
  }
} 