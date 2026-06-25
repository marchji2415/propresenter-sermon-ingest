import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');
    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 });
    }

    const location = formData.get('location') || 'midtown';
    const translation = formData.get('translation') || '';
    const useAi = formData.get('useAi') === 'true';
    const apiKey = formData.get('apiKey') || '';

    // Create temp directory for this task
    const taskId = crypto.randomUUID();
    const tempDir = path.join(process.cwd(), 'tmp', taskId);
    fs.mkdirSync(tempDir, { recursive: true });

    // Determine input file extension
    const ext = path.extname(file.name) || '.pdf';
    const inputPath = path.join(tempDir, `sermon_notes${ext}`);
    const outputPath = path.join(tempDir, 'SermonScripture.pro');
    const jsonOutPath = path.join(tempDir, 'slide_report.json');

    // Save input file buffer
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    fs.writeFileSync(inputPath, buffer);

    // Call Python script relative to parent directory
    const mainPyPath = path.resolve(process.cwd(), '..', 'main.py');
    
    // Check if ProCore is local (inside sermon_ingest_v6) or in parent of sermon_ingest_v6
    let procorePath = path.resolve(process.cwd(), '..', 'ProCore');
    if (!fs.existsSync(procorePath)) {
      procorePath = path.resolve(process.cwd(), '..', '..', 'ProCore');
    }

    const args = [
      mainPyPath,
      '--input', inputPath,
      '--output', outputPath,
      '--procore', procorePath,
      '--location', location,
      '--json-out', jsonOutPath
    ];

    if (translation) {
      args.push('--translation', translation);
    }
    if (useAi) {
      args.push('--use-ai');
    } else {
      args.push('--no-ai');
    }
    if (apiKey) {
      args.push('--api-key', apiKey);
    }

    const pythonCmd = process.env.PYTHON_PATH || 'python';

    return new Promise((resolve) => {
      execFile(pythonCmd, args, { cwd: path.resolve(process.cwd(), '..') }, (error, stdout, stderr) => {
        if (error) {
          console.error('Python execution error:', error);
          return resolve(NextResponse.json({
            error: 'Failed to run sermon ingestion script.',
            details: stderr || error.message,
            stdout: stdout
          }, { status: 500 }));
        }

        if (!fs.existsSync(jsonOutPath)) {
          return resolve(NextResponse.json({
            error: 'JSON slide report not found. Python script did not generate it.',
            details: stderr,
            stdout: stdout
          }, { status: 500 }));
        }

        try {
          const reportContent = fs.readFileSync(jsonOutPath, 'utf-8');
          const report = JSON.parse(reportContent);
          
          return resolve(NextResponse.json({
            success: true,
            taskId: taskId,
            stdout: stdout,
            report: report
          }));
        } catch (parseErr) {
          return resolve(NextResponse.json({
            error: 'Failed to parse JSON slide report.',
            details: parseErr.message,
            stdout: stdout
          }, { status: 500 }));
        }
      });
    });

  } catch (err) {
    console.error('API route error:', err);
    return NextResponse.json({ error: 'Internal Server Error', details: err.message }, { status: 500 });
  }
}
