import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export async function POST(request: NextRequest) {
  // Check if we're running on Vercel
  const isVercel = process.env.VERCEL === '1'
  
  if (isVercel) {
    // Cannot run Python scripts directly on Vercel through spawn
    return NextResponse.json({
      success: false,
      error: 'Missing descriptions report must be run through Vercel Python functions. Please check if the Python handler is properly configured.',
      details: 'This feature requires Python serverless function support.'
    }, { status: 501 })
  }

  return new Promise<NextResponse>((resolve) => {
    const scriptPath = path.join(process.cwd(), 'python_scripts', 'missing_descriptions_report.py')
    
    const pythonProcess = spawn('python3', [scriptPath], {
      env: {
        ...process.env,
        PYTHONPATH: process.cwd()
      }
    })

    let dataString = ''
    let errorString = ''

    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString()
    })

    pythonProcess.stderr.on('data', (data) => {
      errorString += data.toString()
      console.error(data.toString())
    })

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error('Python script error:', errorString)
        resolve(NextResponse.json({
          success: false,
          error: 'Failed to generate missing descriptions report',
          details: errorString || 'Unknown error occurred'
        }, { status: 500 }))
        return
      }

      try {
        const result = JSON.parse(dataString)
        
        if (result.error) {
          resolve(NextResponse.json({
            success: false,
            error: result.error
          }, { status: 500 }))
        } else {
          resolve(NextResponse.json({
            success: true,
            ...result
          }))
        }
      } catch (error) {
        console.error('Failed to parse Python output:', error)
        console.error('Raw output:', dataString)
        resolve(NextResponse.json({
          success: false,
          error: 'Failed to parse report data',
          details: 'Invalid JSON output from Python script'
        }, { status: 500 }))
      }
    })

    pythonProcess.on('error', (error) => {
      resolve(NextResponse.json({
        success: false,
        error: 'Failed to run Python script',
        details: error.message
      }, { status: 500 }))
    })
  })
} 