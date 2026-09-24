import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

/**
 * GET /api/diagnostic-signatures
 * 
 * Serves the local diagnostic signatures store.
 * This provides the frontend with failure signature data
 * that would otherwise require a backend endpoint.
 */
export async function GET() {
  try {
    const signaturesPath = path.join(process.cwd(), 'runtime', 'generated', 'diagnostic-signatures.json');
    
    if (!fs.existsSync(signaturesPath)) {
      return NextResponse.json(
        { signatures: [], index: {} },
        { status: 200 }
      );
    }
    
    const data = JSON.parse(fs.readFileSync(signaturesPath, 'utf8'));
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to serve diagnostic signatures:', error);
    return NextResponse.json(
      { signatures: [], index: {} },
      { status: 200 }
    );
  }
}
