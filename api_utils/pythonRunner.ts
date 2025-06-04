import { spawn } from 'child_process'
import path from 'path'

interface PythonRunnerOptions {
  scriptName: string
  args?: string[]
  env?: Record<string, string>
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
        logs,
        error: `Failed to start process: ${err.message}`
      })
    })
  })
} 