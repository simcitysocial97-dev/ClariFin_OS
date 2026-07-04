'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PdfPreviewWithOverlayProps {
  file: File;
  suggestedBboxNorm: number[] | null;
  /** Enable drawing mode to allow user to draw bbox */
  isDrawing?: boolean;
  /** Callback when user draws a new bbox (normalized coordinates) */
  onBboxDrawn?: (bboxNorm: number[]) => void;
  /** Currently drawn bbox (if any) */
  drawnBboxNorm?: number[] | null;
  /** Whether to show the drawn bbox on all pages */
  applyToAllPages?: boolean;
  className?: string;
}

interface PageInfo {
  pageNumber: number;
  width: number;
  height: number;
}

type LoadingState = 'loading' | 'error' | 'success';

interface DrawState {
  isDrawing: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

/**
 * PDF Preview Component with BBox Overlay
 *
 * Renders PDF pages using pdf.js and displays a suggested bounding box overlay.
 * Can also operate in drawing mode to let users draw their own bbox.
 *
 * BBox format: [x0, y0, x1, y1] in normalized coordinates (0-1)
 * where:
 * - x0: left edge
 * - y0: top edge
 * - x1: right edge
 * - y1: bottom edge
 */
export function PdfPreviewWithOverlay({
  file,
  suggestedBboxNorm,
  isDrawing = false,
  onBboxDrawn,
  drawnBboxNorm,
  applyToAllPages = true,
  className,
}: PdfPreviewWithOverlayProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const firstPageRef = useRef<HTMLDivElement>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('loading');
  const [error, setError] = useState<string | null>(null);
  const [pages, setPages] = useState<PageInfo[]>([]);
  const [pdfDoc, setPdfDoc] = useState<unknown>(null);
  const [pageScales, setPageScales] = useState<Map<number, number>>(new Map());
  const renderedPagesRef = useRef<Set<number>>(new Set());

  // Drawing state - only for first page
  const [drawState, setDrawState] = useState<DrawState>({
    isDrawing: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
  });

  // Load PDF document
  useEffect(() => {
    let cancelled = false;
    renderedPagesRef.current.clear();

    async function loadPdf() {
      try {
        setLoadingState('loading');
        setError(null);

        // Check if pdfjsLib is available
        if (typeof window === 'undefined' || !(window as unknown as { pdfjsLib?: unknown }).pdfjsLib) {
          throw new Error('PDF.js library not loaded');
        }

        const pdfjsLib = (window as unknown as { pdfjsLib: { getDocument: (args: { data: ArrayBuffer }) => { promise: Promise<unknown> } } }).pdfjsLib;

        // Read file as ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();

        // Load PDF document
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

        if (cancelled) return;

        setPdfDoc(pdf);

        // Get page info for all pages
        const pageInfos: PageInfo[] = [];
        const numPages = (pdf as { numPages: number }).numPages;

        for (let i = 1; i <= Math.min(numPages, 5); i++) { // Limit to first 5 pages for performance
          const page = await (pdf as { getPage: (pageNum: number) => Promise<{ getViewport: (args: { scale: number }) => { width: number; height: number } }> }).getPage(i);
          const viewport = page.getViewport({ scale: 1 });
          pageInfos.push({
            pageNumber: i,
            width: viewport.width,
            height: viewport.height,
          });
        }

        if (cancelled) return;

        setPages(pageInfos);
        setLoadingState('success');
      } catch (err) {
        if (cancelled) return;
        console.error('Error loading PDF:', err);
        setError(err instanceof Error ? err.message : 'Failed to load PDF');
        setLoadingState('error');
      }
    }

    loadPdf();

    return () => {
      cancelled = true;
    };
  }, [file]);

  // Render a single page to canvas
  const renderPage = useCallback(async (pageNumber: number, canvas: HTMLCanvasElement) => {
    if (!pdfDoc || renderedPagesRef.current.has(pageNumber)) return;

    try {
      const pdf = pdfDoc as { getPage: (pageNum: number) => Promise<{ getViewport: (args: { scale: number }) => { width: number; height: number }; render: (args: { canvasContext: CanvasRenderingContext2D; viewport: { width: number; height: number } }) => { promise: Promise<void> } }> };
      const page = await pdf.getPage(pageNumber);

      // Calculate scale to fit within container (max width 600px)
      const maxWidth = 600;
      const viewport = page.getViewport({ scale: 1 });
      const scale = Math.min(maxWidth / viewport.width, 1.5); // Max 1.5x zoom
      const scaledViewport = page.getViewport({ scale });

      // Store scale for this page
      setPageScales(prev => new Map(prev).set(pageNumber, scale));

      // Set canvas dimensions
      canvas.width = scaledViewport.width;
      canvas.height = scaledViewport.height;

      // Get rendering context
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Render PDF page
      await page.render({
        canvasContext: ctx,
        viewport: scaledViewport,
      }).promise;

      renderedPagesRef.current.add(pageNumber);
    } catch (err) {
      console.error(`Error rendering page ${pageNumber}:`, err);
    }
  }, [pdfDoc]);

  // Render pages when they're mounted
  useEffect(() => {
    if (loadingState !== 'success' || !pdfDoc) return;

    pages.forEach((pageInfo) => {
      const canvas = document.getElementById(`pdf-page-canvas-${pageInfo.pageNumber}`) as HTMLCanvasElement;
      if (canvas) {
        renderPage(pageInfo.pageNumber, canvas);
      }
    });
  }, [loadingState, pdfDoc, pages, renderPage]);

  // Calculate overlay style from normalized bbox
  const getOverlayStyle = (pageWidth: number, pageHeight: number, bboxNorm: number[] | null): React.CSSProperties | undefined => {
    if (!bboxNorm || bboxNorm.length !== 4) return undefined;

    const [x0, y0, x1, y1] = bboxNorm as [number, number, number, number];

    // Convert normalized coordinates to pixels
    const left = x0 * pageWidth;
    const top = y0 * pageHeight;
    const width = (x1 - x0) * pageWidth;
    const height = (y1 - y0) * pageHeight;

    return {
      position: 'absolute' as const,
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`,
      border: '2px dashed rgba(239, 68, 68, 0.8)', // Red-500 with opacity
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
      pointerEvents: 'none' as const,
      zIndex: 10,
    };
  };

  // Get temporary drawing overlay style
  const getDrawingOverlayStyle = (pageWidth: number, pageHeight: number): React.CSSProperties | undefined => {
    if (!drawState.isDrawing && !drawnBboxNorm) return undefined;

    // Use drawn bbox if available and not currently drawing
    if (!drawState.isDrawing && drawnBboxNorm) {
      return getOverlayStyle(pageWidth, pageHeight, drawnBboxNorm);
    }

    // Show temporary rectangle while drawing
    if (!drawState.isDrawing) return undefined;

    const left = Math.min(drawState.startX, drawState.currentX);
    const top = Math.min(drawState.startY, drawState.currentY);
    const width = Math.abs(drawState.currentX - drawState.startX);
    const height = Math.abs(drawState.currentY - drawState.startY);

    return {
      position: 'absolute' as const,
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`,
      border: '2px dashed rgba(34, 197, 94, 0.8)', // Green-500 while drawing
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
      pointerEvents: 'none' as const,
      zIndex: 10,
    };
  };

  // Mouse event handlers for drawing (only on first page)
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDrawing) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setDrawState({
      isDrawing: true,
      startX: x,
      startY: y,
      currentX: x,
      currentY: y,
    });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDrawing || !drawState.isDrawing) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setDrawState(prev => ({
      ...prev,
      currentX: x,
      currentY: y,
    }));
  };

  const handleMouseUp = () => {
    if (!isDrawing || !drawState.isDrawing) return;

    // Calculate normalized bbox
    const firstPage = pages[0];
    if (!firstPage) return;

    const scale = pageScales.get(1) || 1;
    const displayWidth = firstPage.width * scale;
    const displayHeight = firstPage.height * scale;

    // Get rectangle coordinates
    const left = Math.min(drawState.startX, drawState.currentX);
    const top = Math.min(drawState.startY, drawState.currentY);
    const right = Math.max(drawState.startX, drawState.currentX);
    const bottom = Math.max(drawState.startY, drawState.currentY);

    // Convert to normalized coordinates (0-1)
    const x0 = Math.max(0, Math.min(1, left / displayWidth));
    const y0 = Math.max(0, Math.min(1, top / displayHeight));
    const x1 = Math.max(0, Math.min(1, right / displayWidth));
    const y1 = Math.max(0, Math.min(1, bottom / displayHeight));

    // Only save if bbox has meaningful size
    if (x1 - x0 > 0.01 && y1 - y0 > 0.01) {
      const bboxNorm = [x0, y0, x1, y1];
      onBboxDrawn?.(bboxNorm);
    }

    setDrawState({
      isDrawing: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
    });
  };

  const handleMouseLeave = () => {
    if (drawState.isDrawing) {
      setDrawState({
        isDrawing: false,
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0,
      });
    }
  };

  if (loadingState === 'loading') {
    return (
      <Card className={cn('h-full', className)}>
        <CardContent className="flex flex-col items-center justify-center h-96 gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading PDF preview...</p>
        </CardContent>
      </Card>
    );
  }

  if (loadingState === 'error') {
    return (
      <Card className={cn('h-full', className)}>
        <CardContent className="flex flex-col items-center justify-center h-96 gap-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-muted-foreground text-center">
            Failed to load PDF preview<br />
            <span className="text-xs">{error}</span>
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('h-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            PDF Preview
          </CardTitle>
          <div className="flex items-center gap-2">
            {isDrawing && (
              <Badge variant="outline" className="text-xs border-blue-200 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
                Drawing Mode
              </Badge>
            )}
            {suggestedBboxNorm && !isDrawing && (
              <Badge variant="outline" className="text-xs border-orange-200 bg-orange-50 text-orange-700 dark:bg-orange-900/20 dark:text-orange-300">
                Suggested BBox
              </Badge>
            )}
            {drawnBboxNorm && (
              <Badge variant="outline" className="text-xs border-green-200 bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300">
                User BBox
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={containerRef}
          className="space-y-4 max-h-[600px] overflow-y-auto pr-2"
        >
          {pages.map((pageInfo, index) => {
            // Calculate scale for display (same logic as renderPage)
            const maxWidth = 600;
            const scale = Math.min(maxWidth / pageInfo.width, 1.5);
            const displayWidth = pageInfo.width * scale;
            const displayHeight = pageInfo.height * scale;

            const isFirstPage = index === 0;
            const showBboxOverlay = !isDrawing && suggestedBboxNorm && !drawnBboxNorm;
            const showDrawnBbox = (applyToAllPages || isFirstPage) && drawnBboxNorm;

            return (
              <div
                key={pageInfo.pageNumber}
                ref={isFirstPage ? firstPageRef : undefined}
                className={cn(
                  "relative bg-muted rounded-lg overflow-hidden shadow-sm",
                  isDrawing && isFirstPage && "cursor-crosshair"
                )}
                style={{
                  width: displayWidth,
                  height: displayHeight,
                  margin: '0 auto',
                }}
                onMouseDown={isFirstPage ? handleMouseDown : undefined}
                onMouseMove={isFirstPage ? handleMouseMove : undefined}
                onMouseUp={isFirstPage ? handleMouseUp : undefined}
                onMouseLeave={isFirstPage ? handleMouseLeave : undefined}
              >
                {/* Page number badge */}
                <div className="absolute top-2 left-2 z-20 bg-background/80 backdrop-blur-sm px-2 py-0.5 rounded text-xs font-medium">
                  Page {pageInfo.pageNumber}
                </div>

                {/* Drawing instruction for first page */}
                {isDrawing && isFirstPage && (
                  <div className="absolute top-2 right-2 z-20 bg-blue-500 text-white px-2 py-0.5 rounded text-xs">
                    Drag to draw table region
                  </div>
                )}

                {/* PDF Canvas */}
                <canvas
                  id={`pdf-page-canvas-${pageInfo.pageNumber}`}
                  className="block"
                />

                {/* Suggested BBox Overlay (read-only) */}
                {showBboxOverlay && (
                  <div style={getOverlayStyle(displayWidth, displayHeight, suggestedBboxNorm)}>
                    <div className="absolute -top-5 left-0 bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap">
                      Suggested Area
                    </div>
                  </div>
                )}

                {/* User Drawn BBox Overlay */}
                {showDrawnBbox && (
                  <div style={getOverlayStyle(displayWidth, displayHeight, drawnBboxNorm)}>
                    <div className="absolute -top-5 left-0 bg-green-500 text-white text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap">
                      Selected Area
                    </div>
                  </div>
                )}

                {/* Temporary Drawing Overlay (while dragging) */}
                {isDrawing && isFirstPage && drawState.isDrawing && (
                  <div style={getDrawingOverlayStyle(displayWidth, displayHeight)} />
                )}
              </div>
            );
          })}

          {(pdfDoc as { numPages?: number })?.numPages && (pdfDoc as { numPages: number }).numPages > 5 && (
            <p className="text-xs text-muted-foreground text-center py-2">
              Showing first 5 pages of {(pdfDoc as { numPages: number }).numPages}
            </p>
          )}
        </div>

        {!suggestedBboxNorm && !drawnBboxNorm && !isDrawing && (
          <div className="mt-4 p-3 bg-muted/50 rounded-lg text-xs text-muted-foreground text-center">
            No bounding box available. Click &quot;Draw table region&quot; to define one.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
