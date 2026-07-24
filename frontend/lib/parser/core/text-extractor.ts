/**
 * PDF Text Extraction with Spatial Data
 * Preserves position information for semantic analysis
 */

// PDF.js will be loaded dynamically
let pdfjsLib: any = null;

async function getPdfJs() {
    if (!pdfjsLib) {
        // Use legacy build for Node.js, standard build for browser
        if (typeof window === 'undefined') {
            // Node.js environment - use legacy build
            pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');
        } else {
            // Browser environment - use standard build
            pdfjsLib = await import('pdfjs-dist');
            pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.mjs';
        }
    }
    return pdfjsLib;
}

export interface TextItem {
    text: string;
    x: number;           // X coordinate
    y: number;           // Y coordinate (top of page = 0)
    width: number;
    height: number;
    fontSize: number;
    fontName: string;
}

export interface TextLine {
    y: number;
    items: TextItem[];
    text: string;        // Combined text of line
}

export interface PageData {
    pageNumber: number;
    width: number;
    height: number;
    items: TextItem[];
    lines: TextLine[];
    fullText: string;
}

export interface DocumentData {
    pages: PageData[];
    fullText: string;
    totalPages: number;
}

/**
 * Extract text with position data from PDF
 */
export async function extractTextWithPositions(file: File): Promise<DocumentData> {
    console.warn('[TEXT EXTRACTOR] Loading PDF...');
    
    const pdfjs = await getPdfJs();
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise;
    
    console.warn('[TEXT EXTRACTOR] Pages:', pdf.numPages);
    
    const pages: PageData[] = [];
    let fullText = '';
    
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const viewport = page.getViewport({ scale: 1.0 });
        const textContent = await page.getTextContent();
        
        // Extract items with position data
        const items: TextItem[] = textContent.items.map((item: any) => ({
            text: item.str,
            x: item.transform[4],
            y: viewport.height - item.transform[5], // Flip Y coordinate (PDF origin is bottom-left)
            width: item.width,
            height: item.height,
            fontSize: item.transform[0],
            fontName: item.fontName
        }));
        
        // Group items into lines based on Y position
        const lines = groupIntoLines(items);
        
        // Build page text
        const pageText = lines.map(line => line.text).join('\n');
        fullText += pageText + '\n\n';
        
        pages.push({
            pageNumber: pageNum,
            width: viewport.width,
            height: viewport.height,
            items,
            lines,
            fullText: pageText
        });
        
        console.warn(`[TEXT EXTRACTOR] Page ${pageNum}: ${items.length} items, ${lines.length} lines`);
    }
    
    return {
        pages,
        fullText,
        totalPages: pdf.numPages
    };
}

/**
 * Group text items into lines based on Y position
 */
function groupIntoLines(items: TextItem[], yTolerance: number = 5): TextLine[] {
    if (items.length === 0) return [];
    
    // Sort by Y position first, then X
    const sorted = [...items].sort((a, b) => {
        if (Math.abs(a.y - b.y) > yTolerance) {
            return a.y - b.y;
        }
        return a.x - b.x;
    });
    
    const lines: TextLine[] = [];
    let currentLine: TextItem[] = [sorted[0]];
    let currentY = sorted[0].y;
    
    for (let i = 1; i < sorted.length; i++) {
        const item = sorted[i];
        
        // Same line if Y position is within tolerance
        if (Math.abs(item.y - currentY) <= yTolerance) {
            currentLine.push(item);
        } else {
            // New line
            lines.push({
                y: currentY,
                items: currentLine,
                text: currentLine.map(i => i.text).join(' ')
            });
            currentLine = [item];
            currentY = item.y;
        }
    }
    
    // Add last line
    if (currentLine.length > 0) {
        lines.push({
            y: currentY,
            items: currentLine,
            text: currentLine.map(i => i.text).join(' ')
        });
    }
    
    return lines;
}

/**
 * Simple text extraction (fallback)
 */
export async function extractSimpleText(file: File): Promise<string> {
    const data = await extractTextWithPositions(file);
    return data.fullText;
}
