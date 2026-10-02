import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

/**
 * GET /api/diagnostic-signatures
 *
 * Serves the local diagnostic signatures store.
 * This provides the frontend with failure signature data
 * that would otherwise require a backend endpoint.
 *
 * M10-A3: the artifact lives at the REPOSITORY ROOT
 * (`runtime/generated/diagnostic-signatures.json`), but this handler resolved it
 * against `process.cwd()`. Under `next dev` / `next start` the server's cwd is
 * `frontend/`, so the path it looked for — `frontend/runtime/generated/
 * diagnostic-signatures.json` — never exists and the handler always returned the
 * empty store even when the artifact was present. Candidates are probed in order
 * so the route works from either the repo root or `frontend/`, which is what
 * makes it independent of how the process was launched.
 */
const SIGNATURE_ARTIFACT_CANDIDATES = [
  path.join('runtime', 'generated', 'diagnostic-signatures.json'),
  path.join('..', 'runtime', 'generated', 'diagnostic-signatures.json'),
];

const EMPTY_STORE = { signatures: [], index: {} } as const;

function readSignatureStore(): unknown {
  for (const candidate of SIGNATURE_ARTIFACT_CANDIDATES) {
    const absolute = path.join(process.cwd(), candidate);
    if (!fs.existsSync(absolute)) continue;
    return JSON.parse(fs.readFileSync(absolute, 'utf8'));
  }
  return null;
}

export async function GET() {
  try {
    const store = readSignatureStore();
    if (store === null) {
      return NextResponse.json(EMPTY_STORE, { status: 200 });
    }

    return NextResponse.json(store);
  } catch (error) {
    console.error('Failed to serve diagnostic signatures:', error);
    return NextResponse.json(EMPTY_STORE, { status: 200 });
  }
}
