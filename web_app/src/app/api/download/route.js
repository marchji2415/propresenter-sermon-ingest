import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const filename = searchParams.get('filename') || 'SermonScripture.pro';
    
    if (!id || !/^[a-zA-Z0-9-]+$/.test(id)) {
      return NextResponse.json({ error: 'Invalid task ID' }, { status: 400 });
    }
    
    const filePath = path.join(process.cwd(), 'tmp', id, 'SermonScripture.pro');
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'File not found or expired' }, { status: 404 });
    }
    
    const fileBuffer = fs.readFileSync(filePath);
    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${filename}"`
      }
    });
  } catch (err) {
    console.error('Download error:', err);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
