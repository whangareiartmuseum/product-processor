import { NextRequest, NextResponse } from 'next/server'
import { runPythonScript } from '@/api_utils/pythonRunner'

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