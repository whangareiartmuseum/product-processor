import { NextRequest, NextResponse } from 'next/server'
import { runPythonScript } from '@/api_utils/pythonRunner'

export async function POST(request: NextRequest) {
  try {
    const result = await runPythonScript({
      scriptName: 'process_all_colors.py',
      args: ['--report', '--contrast-type', 'comp_text']
    })
    
    return NextResponse.json({
      success: result.success,
      logs: result.logs,
      error: result.error,
      summary: {
        message: 'Color contrast report generated',
        processType: 'contrast_report',
        reportType: 'complementary_vs_text'
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