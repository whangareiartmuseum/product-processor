import { spawn } from 'child_process'
import path from 'path'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

interface PythonRunnerOptions {
  scriptName: string
  args?: string[]
  env?: Record<string, string>
}

async function checkPythonAvailable(): Promise<boolean> {
  try {
    await execAsync('python3 --version')
    return true
  } catch {
    try {
      await execAsync('python --version')
      return true
    } catch {
      return false
    }
  }
}

export async function runPythonScript({
  scriptName,
  args = [],
  env = {}
}: PythonRunnerOptions): Promise<{
  success: boolean
  logs: string[]
  error?: string
  data?: any
}> {
  // Check if Python is available
  const pythonAvailable = await checkPythonAvailable()
  
  if (!pythonAvailable) {
    return {
      success: false,
      logs: [
        'Python is not available in this environment.',
        'This is a known limitation when running on Vercel.',
        '',
        'To use this feature:',
        '1. Run the application locally with "npm run dev"',
        '2. Make sure Python 3 and all dependencies are installed',
        '3. Or deploy to a platform that supports Python',
        '',
        'See README.md for deployment alternatives.'
      ],
      error: 'Python runtime not available on Vercel serverless platform'
    }
  }

  return new Promise((resolve) => {
    const logs: string[] = []
    const scriptPath = path.join(process.cwd(), 'python_scripts', scriptName)
    
    // Merge environment variables
    const processEnv = {
      ...process.env,
      SHOPIFY_SHOP_URL: process.env.SHOPIFY_SHOP_URL,
      SHOPIFY_ACCESS_TOKEN: process.env.SHOPIFY_ACCESS_TOKEN,
      OPENAI_API_KEY: process.env.OPENAI_API_KEY,
      ...env
    }
    
    const pythonProcess = spawn('python3', [scriptPath, ...args], {
      env: processEnv
    })
    
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString()
      logs.push(output)
      console.log('Python output:', output)
    })
    
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString()
      logs.push(`ERROR: ${error}`)
      console.error('Python error:', error)
    })
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve({
          success: true,
          logs,
          data: { processedSuccessfully: true }
        })
      } else {
        resolve({
          success: false,
          logs,
          error: `Process exited with code ${code}`
        })
      }
    })
    
    pythonProcess.on('error', (err) => {
      resolve({
        success: false,
        logs: [
          'Failed to start Python process.',
          'Make sure Python 3 is installed and available in PATH.',
          `Error: ${err.message}`
        ],
        error: `Failed to start process: ${err.message}`
      })
    })
  })
} 