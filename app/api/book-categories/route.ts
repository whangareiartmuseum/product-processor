import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // On Vercel, proxy to the Python serverless function
    if (process.env.VERCEL_URL) {
      const pythonUrl = `https://${process.env.VERCEL_URL}/api/book-categories`
      const response = await fetch(pythonUrl, { method: 'POST' })
      if (!response.ok) {
        throw new Error(`Python API returned ${response.status}`)
      }
      const data = await response.json()
      return NextResponse.json(data)
    }

    // Local dev: run Python script directly
    const { runPythonScript } = await import('@/api_utils/pythonRunner')
    const result = await runPythonScript({
      scriptName: 'generate_book_categories.py'
    })

    // Parse RESULT_JSON line from logs if present
    const resultLine = (result.logs || []).find((line: string) => line.startsWith('RESULT_JSON:'))
    let parsed: any = {}
    if (resultLine) {
      try {
        parsed = JSON.parse(resultLine.replace('RESULT_JSON:', '').trim())
      } catch (err) {
        parsed = {}
      }
    }

    return NextResponse.json({
      success: result.success && (parsed.success !== false),
      logs: result.logs,
      error: result.error || parsed.error,
      summary: parsed.summary || { message: 'Book categories generation completed (local)' },
      data: parsed.data
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
