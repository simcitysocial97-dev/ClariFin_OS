/**
 * Parser Debug Panel for Multi-PDF Upload
 * Browser-only debug system for bank statement parser
 */

let totalFiles = 0;
let parsedFiles = 0;
let parseLogs = [];

/**
 * Initialize parser debug panel
 * @param {number} total - Total number of files to parse
 */
function initParserDebug(total) {
    totalFiles = total;
    parsedFiles = 0;
    parseLogs = [];

    let panel = document.getElementById('parser-debug-panel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'parser-debug-panel';
        panel.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 350px;
            max-height: 80vh;
            background-color: rgba(0, 0, 0, 0.9);
            color: #00ff00;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            border-radius: 8px;
            z-index: 9999;
            overflow-y: auto;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            border: 1px solid #333;
        `;
        document.body.appendChild(panel);
    }
    
    panel.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 10px;">
            <strong style="color: #fff;">🔍 Parser Debug</strong>
            <button onclick="hideParserDebug()" style="background: none; border: none; color: #fff; cursor: pointer; font-size: 16px;">×</button>
        </div>
        <div id="parser-progress" style="margin-bottom: 10px; color: #ffff00; font-weight: bold;">
            0 / ${totalFiles} PDFs parsed
        </div>
        <div id="parser-entries"></div>
        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #333;">
            <button onclick="exportParserLogs()" style="background: #333; color: #fff; border: 1px solid #555; padding: 5px 10px; cursor: pointer; font-size: 11px; border-radius: 4px;">
                📥 Export Logs
            </button>
            <button onclick="clearParserDebug()" style="background: #333; color: #fff; border: 1px solid #555; padding: 5px 10px; cursor: pointer; font-size: 11px; border-radius: 4px; margin-left: 5px;">
                🗑️ Clear
            </button>
        </div>
    `;
    
    console.log('[PARSER-DEBUG]', `Initialized for ${total} files`);
}

/**
 * Update parser debug panel with new entry
 * @param {Object} entry - Parse result entry
 * @param {string} entry.fileName - Name of the file
 * @param {number} entry.transactions - Number of transactions extracted
 * @param {boolean} entry.success - Whether parsing succeeded
 * @param {number} entry.duration - Parse duration in milliseconds
 */
function updateParserDebug(entry) {
    parsedFiles++;
    
    // Store log entry
    const logEntry = {
        timestamp: new Date().toISOString(),
        fileName: entry.fileName || 'unknown.pdf',
        transactions: entry.transactions || 0,
        success: entry.success,
        duration: entry.duration || 0
    };
    parseLogs.push(logEntry);

    const panel = document.getElementById('parser-debug-panel');
    if (!panel) return;

    const name = entry.fileName || 'unknown.pdf';
    const success = entry.success ? '✅' : '❌';
    const txns = entry.transactions || 0;
    const duration = entry.duration ? `${entry.duration}ms` : '-';
    
    const color = entry.success ? '#00ff00' : '#ff4444';

    const entriesContainer = document.getElementById('parser-entries');
    const row = document.createElement('div');
    row.style.cssText = `
        margin: 5px 0;
        padding: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 4px;
        border-left: 3px solid ${color};
        font-size: 11px;
    `;
    row.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #fff; font-weight: bold;">${success} ${name}</span>
            <span style="color: #888;">${duration}</span>
        </div>
        <div style="color: #aaa; margin-top: 3px;">
            ${txns} transactions extracted
        </div>
    `;
    
    // Insert at top (newest first)
    entriesContainer.insertBefore(row, entriesContainer.firstChild);

    // Update progress
    const progress = document.getElementById('parser-progress');
    if (progress) {
        const percent = Math.round((parsedFiles / totalFiles) * 100);
        progress.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${parsedFiles} / ${totalFiles} PDFs parsed (${percent}%)</span>
                <span style="color: ${percent === 100 ? '#00ff00' : '#ffff00'};">${percent === 100 ? '✓ Complete' : '⏳ Processing...'}</span>
            </div>
            <div style="width: 100%; height: 4px; background: #333; margin-top: 5px; border-radius: 2px;">
                <div style="width: ${percent}%; height: 100%; background: ${percent === 100 ? '#00ff00' : '#ffff00'}; border-radius: 2px; transition: width 0.3s;"></div>
            </div>
        `;
    }
    
    console.log('[PARSER-DEBUG]', `[${success}] ${name}: ${txns} txns (${duration})`);
}

/**
 * Hide parser debug panel
 */
function hideParserDebug() {
    const panel = document.getElementById('parser-debug-panel');
    if (panel) {
        panel.style.display = 'none';
    }
}

/**
 * Show parser debug panel
 */
function showParserDebug() {
    const panel = document.getElementById('parser-debug-panel');
    if (panel) {
        panel.style.display = 'block';
    }
}

/**
 * Clear parser debug panel
 */
function clearParserDebug() {
    parsedFiles = 0;
    parseLogs = [];
    const entriesContainer = document.getElementById('parser-entries');
    if (entriesContainer) {
        entriesContainer.innerHTML = '';
    }
    const progress = document.getElementById('parser-progress');
    if (progress) {
        progress.innerHTML = `0 / ${totalFiles} PDFs parsed`;
    }
    console.log('[PARSER-DEBUG]', 'Panel cleared');
}

/**
 * Export parser logs to JSON file
 */
function exportParserLogs() {
    if (parseLogs.length === 0) {
        console.warn('[PARSER-DEBUG]', 'No logs to export');
        return;
    }
    
    const exportData = {
        exportTime: new Date().toISOString(),
        totalFiles: totalFiles,
        parsedFiles: parsedFiles,
        logs: parseLogs
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `parser_logs_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('[PARSER-DEBUG]', `Exported ${parseLogs.length} log entries`);
}

/**
 * Handle multiple file uploads with debug tracking
 * @param {FileList} files - List of files to parse
 */
async function handleMultipleFiles(files) {
    if (!files || files.length === 0) return;
    
    // Initialize debug panel
    initParserDebug(files.length);
    
    // Process each file sequentially
    for (const file of files) {
        try {
            // Capture ArrayBuffer immediately to avoid zero-byte issues
            const arrayBuffer = await file.arrayBuffer();
            if (!arrayBuffer || arrayBuffer.byteLength === 0) {
                throw new Error(`File "${file.name}" is empty or could not be read`);
            }
            
            // Track parse start time
            const startTime = Date.now();
            
            // Call browser-only parser
            const result = await window.BankParser.parsePDFWithMetadata(arrayBuffer, {
                fileName: file.name
            });
            
            const endTime = Date.now();
            
            // Update debug panel
            updateParserDebug({
                fileName: result.fileName || file.name,
                transactions: result.transactions?.length || 0,
                success: true,
                duration: endTime - startTime
            });
            
            // Update UI or dashboard (if function exists)
            if (typeof addParsedFileToUI === 'function') {
                addParsedFileToUI(result.transactions, result.fileName || file.name);
            }
            
        } catch (err) {
            console.error(`[PDF-PARSER ERROR] ${file.name}:`, err.message);
            
            // Update debug panel with failure
            updateParserDebug({
                fileName: file.name,
                transactions: 0,
                success: false,
                duration: 0
            });
        }
    }
}

// Make functions globally available
window.initParserDebug = initParserDebug;
window.updateParserDebug = updateParserDebug;
window.hideParserDebug = hideParserDebug;
window.showParserDebug = showParserDebug;
window.clearParserDebug = clearParserDebug;
window.exportParserLogs = exportParserLogs;
window.handleMultipleFiles = handleMultipleFiles;

console.log('[PARSER-DEBUG]', 'Debug system loaded and ready');
