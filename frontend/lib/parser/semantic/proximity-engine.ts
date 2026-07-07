/**
 * Proximity-based label-value matching
 * Finds values near labels based on spatial position
 */
import type { TextItem, PageData } from '../core/text-extractor';

export interface LabelValuePair {
    label: string;
    value: string;
    confidence: number;
    labelPosition: { x: number; y: number };
    valuePosition: { x: number; y: number };
    distance: number;
}

export interface ProximityConfig {
    maxHorizontalDistance: number;  // Max pixels to right
    maxVerticalDistance: number;    // Max pixels below
    sameLine: boolean;               // Look on same line only?
    nextLine: boolean;               // Look on next line?
}

/**
 * Find value near a label
 */
export function findValueNearLabel(
    label: string,
    pageData: PageData,
    config: ProximityConfig = {
        maxHorizontalDistance: 300,
        maxVerticalDistance: 30,
        sameLine: true,
        nextLine: true
    }
): LabelValuePair | null {
    
    console.log(`[PROXIMITY] Searching for value near label: "${label}"`);
    
    // Find label in page
    const labelItem = findLabelInPage(label, pageData);
    if (!labelItem) {
        console.log(`[PROXIMITY] Label "${label}" not found`);
        return null;
    }
    
    console.log(`[PROXIMITY] Found label at x:${labelItem.x.toFixed(0)}, y:${labelItem.y.toFixed(0)}`);
    
    // Search for value
    const candidates: Array<{item: TextItem, distance: number, type: string}> = [];
    
    // Search same line (to the right of label)
    if (config.sameLine) {
        const sameLine = pageData.items.filter(item => 
            Math.abs(item.y - labelItem.y) < 5 &&  // Same Y position
            item.x > labelItem.x &&                 // To the right
            item.x - labelItem.x < config.maxHorizontalDistance
        );
        
        sameLine.forEach(item => {
            candidates.push({
                item,
                distance: item.x - labelItem.x,
                type: 'same-line'
            });
        });
    }
    
    // Search next line (below label)
    if (config.nextLine) {
        const nextLine = pageData.items.filter(item =>
            item.y > labelItem.y &&                 // Below
            item.y - labelItem.y < config.maxVerticalDistance &&
            Math.abs(item.x - labelItem.x) < 100    // Roughly aligned
        );
        
        nextLine.forEach(item => {
            candidates.push({
                item,
                distance: item.y - labelItem.y,
                type: 'next-line'
            });
        });
    }
    
    if (candidates.length === 0) {
        console.log(`[PROXIMITY] No value candidates found near "${label}"`);
        return null;
    }
    
    // Sort by distance, pick closest
    candidates.sort((a, b) => a.distance - b.distance);
    const best = candidates[0];
    
    console.log(`[PROXIMITY] Found value "${best.item.text}" (${best.type}, distance: ${best.distance.toFixed(0)}px)`);
    
    return {
        label,
        value: best.item.text,
        confidence: calculateConfidence(best.distance, best.type),
        labelPosition: { x: labelItem.x, y: labelItem.y },
        valuePosition: { x: best.item.x, y: best.item.y },
        distance: best.distance
    };
}

/**
 * Find label text in page
 */
function findLabelInPage(labelText: string, pageData: PageData): TextItem | null {
    const labelLower = labelText.toLowerCase();
    
    // Try exact match first
    let found = pageData.items.find(item => 
        item.text.toLowerCase().includes(labelLower)
    );
    
    // Try fuzzy match on lines
    if (!found) {
        for (const line of pageData.lines) {
            if (line.text.toLowerCase().includes(labelLower)) {
                // Return first item of this line
                found = line.items[0];
                break;
            }
        }
    }
    
    return found || null;
}

/**
 * Calculate confidence score
 */
function calculateConfidence(distance: number, type: string): number {
    let score = 1.0;
    
    // Closer = higher confidence
    if (type === 'same-line') {
        score = Math.max(0.5, 1.0 - (distance / 300));
    } else if (type === 'next-line') {
        score = Math.max(0.3, 1.0 - (distance / 50));
    }
    
    return score;
}

/**
 * Find multiple values for a label (e.g., multiple cards)
 */
export function findAllValuesNearLabel(
    label: string,
    pageData: PageData,
    config?: ProximityConfig
): LabelValuePair[] {
    // Find all instances of label
    const labelInstances = pageData.items.filter(item =>
        item.text.toLowerCase().includes(label.toLowerCase())
    );
    
    const results: LabelValuePair[] = [];
    
    for (const labelItem of labelInstances) {
        // Temporarily modify pageData to search from this position
        const tempPageData = {
            ...pageData,
            items: pageData.items.map(item => ({
                ...item,
                x: item.x - labelItem.x,  // Adjust relative to label
                y: item.y - labelItem.y
            }))
        };
        
        const result = findValueNearLabel(label, tempPageData, config);
        if (result) {
            results.push(result);
        }
    }
    
    return results;
}
