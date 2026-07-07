/**
 * Table Detection and Extraction
 * Identifies table structures and extracts rows/columns
 */
import type { TextItem, TextLine, PageData } from '../core/text-extractor';

export interface TableColumn {
    name: string;
    xStart: number;
    xEnd: number;
    index: number;
}

export interface TableRow {
    y: number;
    cells: string[];
    rawItems: TextItem[];
}

export interface Table {
    headers: TableColumn[];
    rows: TableRow[];
    startY: number;
    endY: number;
}

/**
 * Detect transaction table in page
 */
export function detectTransactionTable(pageData: PageData): Table | null {
    console.log('[TABLE DETECTOR] Scanning for transaction table...');
    
    // Step 1: Find header row (contains "Date", "Description", "Amount", etc.)
    const headerKeywords = ['date', 'description', 'amount', 'particulars', 'transaction'];
    
    let headerLine: TextLine | null = null;
    for (const line of pageData.lines) {
        const lineLower = line.text.toLowerCase();
        const matchCount = headerKeywords.filter(kw => lineLower.includes(kw)).length;
        
        if (matchCount >= 2) {  // At least 2 keywords = likely header
            headerLine = line;
            console.log('[TABLE DETECTOR] Found header at y:', line.y);
            console.log('[TABLE DETECTOR] Header:', line.text);
            break;
        }
    }
    
    if (!headerLine) {
        console.log('[TABLE DETECTOR] No table header found');
        return null;
    }
    
    // Step 2: Extract column positions from header
    const columns = extractColumns(headerLine);
    console.log('[TABLE DETECTOR] Detected', columns.length, 'columns');
    
    // Step 3: Extract data rows below header
    const dataRows = extractRows(
        pageData.lines.filter(line => line.y > headerLine!.y),
        columns,
        headerLine.y
    );
    
    console.log('[TABLE DETECTOR] Extracted', dataRows.length, 'rows');
    
    return {
        headers: columns,
        rows: dataRows,
        startY: headerLine.y,
        endY: dataRows[dataRows.length - 1]?.y || headerLine.y
    };
}

/**
 * Extract column definitions from header
 */
function extractColumns(headerLine: TextLine): TableColumn[] {
    const columns: TableColumn[] = [];
    
    // Sort items by X position
    const sortedItems = [...headerLine.items].sort((a, b) => a.x - b.x);
    
    sortedItems.forEach((item, index) => {
        columns.push({
            name: item.text,
            xStart: item.x,
            xEnd: sortedItems[index + 1]?.x || item.x + 200,  // Assume 200px width if last column
            index
        });
    });
    
    return columns;
}

/**
 * Extract data rows based on column positions
 */
function extractRows(
    lines: TextLine[],
    columns: TableColumn[],
    headerY: number
): TableRow[] {
    const rows: TableRow[] = [];
    
    for (const line of lines) {
        // Skip if too far from header (likely footer or next section)
        if (line.y - headerY > 500) break;
        
        // Skip if line is too short (likely not a data row)
        if (line.items.length < 2) continue;
        
        // Map items to columns based on X position
        const cells: string[] = new Array(columns.length).fill('');
        
        for (const item of line.items) {
            // Find which column this item belongs to
            const columnIndex = columns.findIndex(col =>
                item.x >= col.xStart && item.x < col.xEnd
            );
            
            if (columnIndex !== -1) {
                cells[columnIndex] += (cells[columnIndex] ? ' ' : '') + item.text;
            }
        }
        
        // Only add row if it has data in multiple columns
        const filledCells = cells.filter(c => c).length;
        if (filledCells >= 2) {
            rows.push({
                y: line.y,
                cells,
                rawItems: line.items
            });
        }
    }
    
    return rows;
}

/**
 * Extract transactions from detected table
 */
export function extractTransactionsFromTable(
    table: Table,
    _bankName: string
): Array<{date: string, description: string, amount: number, type: string}> {
    
    console.log('[TABLE DETECTOR] Extracting transactions from table...');
    
    // Find column indices
    const dateColIndex = table.headers.findIndex(h => 
        /date/i.test(h.name)
    );
    const descColIndex = table.headers.findIndex(h =>
        /description|particulars|transaction/i.test(h.name)
    );
    const amountColIndex = table.headers.findIndex(h =>
        /amount|debit|credit/i.test(h.name)
    );
    
    if (dateColIndex === -1 || descColIndex === -1 || amountColIndex === -1) {
        console.log('[TABLE DETECTOR] Could not identify required columns');
        return [];
    }
    
    console.log('[TABLE DETECTOR] Column mapping:', {
        date: dateColIndex,
        description: descColIndex,
        amount: amountColIndex
    });
    
    const transactions = [];
    
    for (const row of table.rows) {
        const dateStr = row.cells[dateColIndex]?.trim();
        const desc = row.cells[descColIndex]?.trim();
        const amountStr = row.cells[amountColIndex]?.trim();
        
        if (!dateStr || !desc || !amountStr) continue;
        
        // Parse amount
        const amount = parseFloat(amountStr.replace(/[^0-9.]/g, ''));
        if (isNaN(amount) || amount === 0) continue;
        
        // Determine type (credit/debit)
        const type = /cr|credit/i.test(amountStr) ? 'credit' : 'debit';
        
        transactions.push({
            date: dateStr,
            description: desc,
            amount,
            type
        });
    }
    
    console.log('[TABLE DETECTOR] Extracted', transactions.length, 'valid transactions');
    
    return transactions;
}
