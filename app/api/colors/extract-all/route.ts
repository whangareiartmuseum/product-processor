import { NextRequest, NextResponse } from 'next/server'
import { runPythonScript } from '@/api_utils/pythonRunner'

export async function POST(request: NextRequest) {
  try {
    const result = await runPythonScript({
      scriptName: 'process_all_colors.py',
      args: ['--all']
    })
    
    return NextResponse.json({
      success: result.success,
      logs: result.logs,
      error: result.error,
      summary: {
        message: 'Color extraction for all products completed',
        processType: 'all_products'
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