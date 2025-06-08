import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

export async function POST(request: Request) {
  try {
    const { productId } = await request.json();
    
    if (!productId) {
      return NextResponse.json({ error: 'Product ID is required' }, { status: 400 });
    }

    // Update the posted products file
    const postedFile = path.join(process.cwd(), 'python_scripts', 'posted_products.json');
    
    let posted = [];
    try {
      const data = await fs.readFile(postedFile, 'utf-8');
      posted = JSON.parse(data);
    } catch (error) {
      // File doesn't exist yet, that's okay
    }

    if (!posted.includes(productId.toString())) {
      posted.push(productId.toString());
      await fs.writeFile(postedFile, JSON.stringify(posted, null, 2));
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error marking product as posted:', error);
    return NextResponse.json({ error: 'Failed to mark product as posted' }, { status: 500 });
  }
} 