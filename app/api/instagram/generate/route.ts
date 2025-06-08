import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST() {
  return new Promise<NextResponse>((resolve) => {
    const scriptPath = path.join(process.cwd(), 'python_scripts', 'generate_instagram_post.py');
    const pythonProcess = spawn('python3', [scriptPath]);

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorString += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error('Python script error:', errorString);
        resolve(NextResponse.json({ error: 'Failed to generate Instagram post' }, { status: 500 }));
        return;
      }

      try {
        const result = JSON.parse(dataString);
        resolve(NextResponse.json(result));
      } catch (error) {
        console.error('Failed to parse Python output:', dataString);
        resolve(NextResponse.json({ error: 'Failed to parse response' }, { status: 500 }));
      }
    });
  });
} 