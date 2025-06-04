import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { input } = body
    
    if (!input) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Product ID or handle is required'
        },
        { status: 400 }
      )
    }
    
    // Check if we're on Vercel
    if (process.env.VERCEL_URL) {
      // Call the Python serverless function
      const pythonUrl = `https://${process.env.VERCEL_URL}/api/python/colors-single`
      
      const response = await fetch(pythonUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input })
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
        scriptName: 'process_single_product.py',
        args: [input]
      })
      
      return NextResponse.json({
        success: result.success,
        logs: result.logs,
        error: result.error,
        summary: {
          message: `Color extraction for product "${input}" completed`,
          processType: 'single_product',
          productId: input
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