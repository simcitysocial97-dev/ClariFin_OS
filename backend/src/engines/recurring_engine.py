"""
Recurring Transaction Detector Engine
=====================================

Auto-detects recurring transactions from transaction history using
pattern recognition and statistical analysis.

Key Principles:
1. Deterministic: same data → same output
2. SQL for data retrieval, Python for pattern detection
3. Statistical consistency checks (coefficient of variation < 0.3)
4. Frequency classification based on median intervals
"""

import re
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING

from src.logger import log
from src.utils import parse_date_to_iso

if TYPE_CHECKING:
    from src.db import FinanceDB


# ============================================================
# Constants
# ============================================================

# Frequency classification based on median interval (days)
FREQUENCY_RANGES = {
    "weekly": (5, 9),      # 5-9 days
    "monthly": (25, 35),   # 25-35 days
    "quarterly": (85, 95), # 85-95 days
    "annual": (355, 375),  # 355-375 days
}

# Minimum coefficient of variation for consistency check
MAX_CV = 0.3


# ============================================================
# Helper Functions
# ============================================================

def normalize_description(description: str) -> str:
    """
    Normalize transaction description for grouping.
    
    Steps:
    1. Lowercase
    2. Remove numbers and special characters
    3. Keep only alphabetic characters and spaces
    4. Strip whitespace
    5. Collapse multiple spaces
    
    Args:
        description: Original transaction description
        
    Returns:
        Normalized description string
    """
    if not description:
        return ""
    
    # Lowercase
    text = description.lower()
    
    # Remove numbers and special chars, keep only letters and spaces
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Strip and collapse whitespace
    text = ' '.join(text.split())
    
    return text


def _parse_date_to_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object using centralized date parsing.
    
    Args:
        date_str: Date in YYYY-MM-DD format (date_iso)
        
    Returns:
        datetime object or None if invalid
    """
    if not date_str:
        return None
    
    # Use centralized parse_date_to_iso for consistent parsing
    iso_date = parse_date_to_iso(date_str)
    if iso_date:
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d")
        except ValueError:
            pass
    
    # Fallback: try direct parsing
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    return None


def calculate_intervals(dates: List[str]) -> List[int]:
    """
    Calculate intervals in days between consecutive dates.
    
    Args:
        dates: List of date strings in YYYY-MM-DD format, sorted ascending
        
    Returns:
        List of intervals in days between consecutive dates
    """
    intervals = []
    parsed_dates = []
    
    for date_str in dates:
        parsed = _parse_date_to_datetime(date_str)
        if parsed:
            parsed_dates.append(parsed)
    
    # Sort dates
    parsed_dates.sort()
    
    # Calculate intervals
    for i in range(1, len(parsed_dates)):
        delta = (parsed_dates[i] - parsed_dates[i-1]).days
        if delta > 0:  # Only positive intervals
            intervals.append(delta)
    
    return intervals


def calculate_coefficient_of_variation(values: List[int]) -> float:
    """
    Calculate coefficient of variation (CV) = std_dev / mean.
    
    Args:
        values: List of numeric values
        
    Returns:
        CV value (0 if mean is 0)
    """
    if not values or len(values) < 2:
        return float('inf')
    
    mean_val = statistics.mean(values)
    if mean_val == 0:
        return float('inf')
    
    try:
        std_dev = statistics.stdev(values)
        return std_dev / mean_val
    except statistics.StatisticsError:
        return float('inf')


def classify_frequency(median_interval: float) -> Optional[str]:
    """
    Classify frequency based on median interval in days.
    
    Args:
        median_interval: Median interval in days
        
    Returns:
        Frequency string ("weekly", "monthly", "quarterly", "annual") or None
    """
    for freq, (min_days, max_days) in FREQUENCY_RANGES.items():
        if min_days <= median_interval <= max_days:
            return freq
    return None


def get_most_common(values: List[str]) -> str:
    """
    Get the most common value from a list.
    
    Args:
        values: List of string values
        
    Returns:
        Most common value or empty string
    """
    if not values:
        return ""
    
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    
    return max(counts.items(), key=lambda x: x[1])[0]


def calculate_median(values: List[int]) -> float:
    """
    Calculate median of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Median value
    """
    if not values:
        return 0.0
    return statistics.median(values)


def add_days_to_date(date_str: str, days: int) -> str:
    """
    Add days to a date string.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        days: Number of days to add
        
    Returns:
        Resulting date string in YYYY-MM-DD format
    """
    parsed = _parse_date_to_datetime(date_str)
    if not parsed:
        return ""
    new_date = parsed + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


# ============================================================
# Main Detection Function
# ============================================================

def detect_recurring_transactions(
    db: "FinanceDB",
    min_occurrences: int = 3,
    date_tolerance_days: int = 5
) -> list[dict]:
    """
    Auto-detect recurring transactions from transaction history.
    
    Algorithm:
    1. Query transactions from last 6 months, ordered by date_iso
    2. Normalize descriptions: lowercase, strip numbers/special chars
    3. Group transactions by normalized description
    4. For each group with >= min_occurrences:
       a. Calculate intervals between consecutive dates (in days)
       b. Compute median interval
       c. Classify frequency based on median
       d. Check consistency: CV of intervals < 0.3
       e. If passes, mark as recurring
    5. Return sorted by confidence descending
    
    Args:
        db: FinanceDB instance
        min_occurrences: Minimum number of occurrences to consider (default 3)
        date_tolerance_days: Tolerance for date matching (reserved for future use)
        
    Returns:
        List of detected recurring transactions with metadata
    """
    log.info("Starting recurring transaction detection (min_occurrences=%d)", min_occurrences)
    
    # Calculate cutoff date (6 months ago)
    cutoff_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    log.debug("Querying transactions since %s", cutoff_date)
    
    # Query transactions from last 6 months
    with db.connection() as conn:
        # Check if we have any data
        cur = conn.execute("SELECT 1 FROM transactions LIMIT 1")
        if not cur.fetchone():
            log.warning("No transactions found for recurring detection")
            return []
        
        # Query transactions with all needed fields
        sql = """
            SELECT 
                id,
                description,
                amount_paise,
                type,
                category,
                date_iso,
                account_id
            FROM transactions
            WHERE date_iso >= ?
            ORDER BY date_iso ASC
        """
        cur = conn.execute(sql, (cutoff_date,))
        rows = cur.fetchall()
    
    if not rows:
        log.warning("No transactions found in last 6 months")
        return []
    
    log.info("Found %d transactions to analyze", len(rows))
    
    # Group transactions by normalized description
    groups: Dict[str, List[dict]] = {}
    for row in rows:
        normalized = normalize_description(row["description"] or "")
        if not normalized:
            continue
        
        if normalized not in groups:
            groups[normalized] = []
        
        groups[normalized].append({
            "id": row["id"],
            "description": row["description"],
            "amount_paise": row["amount_paise"],
            "type": row["type"],
            "category": row["category"],
            "date_iso": row["date_iso"],
            "account_id": row["account_id"],
            "normalized_description": normalized,
        })
    
    log.info("Grouped into %d unique descriptions", len(groups))
    
    # Analyze each group for recurring patterns
    detected = []
    
    for normalized_desc, transactions in groups.items():
        # Skip groups with fewer than min_occurrences
        if len(transactions) < min_occurrences:
            continue
        
        # Get all dates for this group
        dates = [t["date_iso"] for t in transactions if t["date_iso"]]
        
        if len(dates) < min_occurrences:
            continue
        
        # Calculate intervals between consecutive dates
        intervals = calculate_intervals(dates)
        
        if len(intervals) < 2:
            continue
        
        # Compute median interval
        median_interval = calculate_median(intervals)
        
        # Classify frequency
        frequency = classify_frequency(median_interval)
        if not frequency:
            log.debug("Skipping '%s': median interval %.1f doesn't match any frequency", 
                     normalized_desc, median_interval)
            continue
        
        # Check consistency: coefficient of variation < 0.3
        cv = calculate_coefficient_of_variation(intervals)
        if cv >= MAX_CV:
            log.debug("Skipping '%s': CV %.3f >= %.1f (inconsistent intervals)", 
                     normalized_desc, cv, MAX_CV)
            continue
        
        # Calculate confidence score (1 - CV, clamped to 0-1)
        confidence = max(0.0, min(1.0, 1.0 - cv))
        
        # Get median amount
        amounts = [t["amount_paise"] for t in transactions if t["amount_paise"] is not None]
        median_amount = int(calculate_median(amounts)) if amounts else 0
        
        # Get most common type
        types = [t["type"] for t in transactions if t["type"]]
        most_common_type = get_most_common(types) or "debit"
        
        # Get most common category
        categories = [t["category"] for t in transactions if t["category"]]
        most_common_category = get_most_common(categories) or "Uncategorized"
        
        # Get most recent description (original)
        sorted_txns = sorted(transactions, key=lambda x: x["date_iso"] or "", reverse=True)
        most_recent_desc = sorted_txns[0]["description"] if sorted_txns else normalized_desc
        last_date = sorted_txns[0]["date_iso"] if sorted_txns else ""
        
        # Calculate next expected date
        next_expected_date = add_days_to_date(last_date, int(median_interval))
        
        # Get transaction IDs
        transaction_ids = [t["id"] for t in transactions]
        
        detected.append({
            "description": most_recent_desc,
            "normalized_description": normalized_desc,
            "amount_paise": median_amount,
            "type": most_common_type,
            "category": most_common_category,
            "frequency": frequency,
            "occurrence_count": len(transactions),
            "last_date": last_date,
            "next_expected_date": next_expected_date,
            "confidence": round(confidence, 4),
            "transaction_ids": transaction_ids,
        })
        
        log.debug("Detected recurring: '%s' (%s, %d occurrences, confidence=%.3f)",
                 normalized_desc, frequency, len(transactions), confidence)
    
    # Sort by confidence descending
    detected.sort(key=lambda x: x["confidence"], reverse=True)
    
    log.info("Recurring detection complete: %d patterns found", len(detected))
    return detected


# ============================================================
# Save Function
# ============================================================

def save_detected_recurring(db: "FinanceDB", detected: list[dict]) -> int:
    """
    Save detected recurring transactions to the database.
    
    For each detected recurring transaction:
    - Insert into recurring_transactions table with auto_detected = 1
    - Skip if similar entry exists (match on normalized description + 
      amount within 10% + same frequency)
    
    Args:
        db: FinanceDB instance
        detected: List of detected recurring transaction dicts
        
    Returns:
        Count of newly inserted records
    """
    if not detected:
        log.info("No detected recurring transactions to save")
        return 0
    
    log.info("Saving %d detected recurring transactions", len(detected))
    
    inserted_count = 0
    
    with db.transaction() as conn:
        for item in detected:
            normalized_desc = item["normalized_description"]
            amount_paise = item["amount_paise"]
            frequency = item["frequency"]
            
            # Calculate amount range (±10%)
            amount_min = int(amount_paise * 0.9)
            amount_max = int(amount_paise * 1.1)
            
            # Check for existing similar entry
            cur = conn.execute("""
                SELECT 1 FROM recurring_transactions
                WHERE LOWER(TRIM(description)) = LOWER(TRIM(?))
                AND amount_paise BETWEEN ? AND ?
                AND frequency = ?
                LIMIT 1
            """, (normalized_desc, amount_min, amount_max, frequency))
            
            if cur.fetchone():
                log.debug("Skipping '%s': similar entry already exists", normalized_desc)
                continue
            
            # Also check by normalized description match
            cur = conn.execute("""
                SELECT 1 FROM recurring_transactions
                WHERE LOWER(TRIM(description)) LIKE ?
                AND amount_paise BETWEEN ? AND ?
                AND frequency = ?
                LIMIT 1
            """, (f"%{normalized_desc}%", amount_min, amount_max, frequency))
            
            if cur.fetchone():
                log.debug("Skipping '%s': partial match already exists", normalized_desc)
                continue
            
            # Insert new recurring transaction
            cur = conn.execute("""
                INSERT INTO recurring_transactions 
                (description, amount_paise, type, category, frequency, 
                 next_due_date, last_detected_date, occurrence_count, 
                 is_active, auto_detected, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["description"],
                item["amount_paise"],
                item["type"],
                item["category"],
                item["frequency"],
                item["next_expected_date"],
                item["last_date"],
                item["occurrence_count"],
                1,  # is_active
                1,  # auto_detected
                f"Auto-detected from {item['occurrence_count']} transactions. Confidence: {item['confidence']:.2%}",
            ))
            
            if cur.rowcount > 0:
                inserted_count += 1
                log.debug("Inserted recurring: '%s' (%s)", 
                         item["description"], item["frequency"])
    
    log.info("Saved %d new recurring transactions", inserted_count)
    return inserted_count


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from src.db import FinanceDB
    
    # Default db path
    db_path = str(Path(__file__).parent.parent / "data" / "finance.db")
    
    log.info("=" * 60)
    log.info("Recurring Transaction Detector Engine Test")
    log.info("=" * 60)
    log.info("Database: %s", db_path)
    
    db = FinanceDB(db_path=db_path)
    
    # Test detection
    log.info("\n--- Detecting Recurring Transactions ---")
    detected = detect_recurring_transactions(db, min_occurrences=3)
    
    log.info("\n--- Detection Results ---")
    log.info("Total detected: %d", len(detected))
    
    for i, item in enumerate(detected[:10], 1):
        log.info("\n%d. %s", i, item["description"])
        log.info("   Normalized: %s", item["normalized_description"])
        log.info("   Amount: ₹%.2f", item["amount_paise"] / 100)
        log.info("   Type: %s", item["type"])
        log.info("   Category: %s", item["category"])
        log.info("   Frequency: %s", item["frequency"])
        log.info("   Occurrences: %d", item["occurrence_count"])
        log.info("   Last Date: %s", item["last_date"])
        log.info("   Next Expected: %s", item["next_expected_date"])
        log.info("   Confidence: %.2f%%", item["confidence"] * 100)
        log.info("   Transaction IDs: %s", item["transaction_ids"])
    
    if len(detected) > 10:
        log.info("\n... and %d more", len(detected) - 10)
    
    # Uncomment to test saving:
    # log.info("\n--- Saving Detected Recurring ---")
    # saved = save_detected_recurring(db, detected)
    # log.info("Saved %d new recurring transactions", saved)
    
    db.close()
