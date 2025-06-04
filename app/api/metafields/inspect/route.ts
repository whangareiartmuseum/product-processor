import { NextRequest, NextResponse } from 'next/server'
import { runPythonScript } from '@/api_utils/pythonRunner'

export async function POST(request: NextRequest) {
  try {
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