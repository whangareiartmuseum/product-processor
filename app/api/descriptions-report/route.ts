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

    let output = ''
    let errorOutput = ''
    let report: any = null

    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString()
      output += text
      console.log(text)
      
      // Try to extract the report data from the output
      const lines = output.split('\n')
      for (const line of lines) {
        if (line.includes('Report saved to:')) {
          // Extract the filename and try to read it
          const match = line.match(/Report saved to: (.+)/)
          if (match) {
            try {
              // Since we can't read from /tmp in some environments, 
              // we'll parse the summary from the console output
              const summaryMatch = output.match(/Total products: (\d+)/);
              const missingMatch = output.match(/Missing descriptions: (\d+) \(([\d.]+)%\)/);
              const haveMatch = output.match(/Have descriptions: (\d+)/);
              
              if (summaryMatch && missingMatch) {
                report = {
                  success: true,
                  summary: {
                    total_products: parseInt(summaryMatch[1]),
                    missing_descriptions: parseInt(missingMatch[1]),
                    have_descriptions: parseInt(haveMatch?.[1] || '0'),
                    missing_percentage: parseFloat(missingMatch[2])
                  },
                  logs: output.split('\n').filter(line => line.trim())
                }
              }
            } catch (e) {
              console.error('Error parsing report:', e)
            }
          }
        }
      }
    })

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString()
      console.error(data.toString())
    })

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        resolve(NextResponse.json({
          success: false,
          error: 'Failed to generate missing descriptions report',
          details: errorOutput || 'Unknown error occurred',
          logs: output.split('\n').filter(line => line.trim())
        }, { status: 500 }))
      } else {
        if (report) {
          resolve(NextResponse.json(report))
        } else {
          // Fallback: return the logs if we couldn't parse the report
          resolve(NextResponse.json({
            success: true,
            logs: output.split('\n').filter(line => line.trim()),
            rawOutput: output
          }))
        }
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