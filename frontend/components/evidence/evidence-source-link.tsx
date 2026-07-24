/**
 * Evidence Source Link Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying evidence source information.
 */

'use client';

import { FileText, FileSpreadsheet, FileDigit } from 'lucide-react';
import type { EvidenceSource } from '@/lib/evidence/types';

interface EvidenceSourceLinkProps {
  source: EvidenceSource;
}

/**
 * Evidence Source Link Component
 * Displays source information for an evidence item
 */
export function EvidenceSourceLink({ source }: EvidenceSourceLinkProps) {
  if (!source.file_id && !source.extraction_id && !source.api_endpoint) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      {source.file_id && (
        <>
          {source.row_number !== undefined && (
            <>
              <FileText className="h-3 w-3" />
              <span>
                File: {source.file_id} (Row {source.row_number})
              </span>
            </>
          )}
        </>
      )}
      
      {source.extraction_id && (
        <>
          <FileDigit className="h-3 w-3" />
          <span>Extraction: {source.extraction_id}</span>
        </>
      )}
      
      {source.api_endpoint && (
        <>
          <FileSpreadsheet className="h-3 w-3" />
          <span>API: {source.api_endpoint}</span>
        </>
      )}
    </div>
  );
}