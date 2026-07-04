"""Statement import repository - CRUD operations for statement imports and staged transactions.

This module provides database operations for the PDF statement import pipeline,
including statement imports, staged transactions, and related operations.
"""

import sqlite3
import uuid
import json as json_mod
from typing import List, Dict, Optional, Any

from src.logger import log
from ..pagination import PaginatedResult, paginate_query


# ============================================================
# Statement Import CRUD
# ============================================================

def insert_statement_import(conn: sqlite3.Connection, import_data: dict) -> str:
    """Insert a new statement import record.
    
    Args:
        conn: Database connection
        import_data: Dict with keys:
            - id: UUID string (required)
            - source_filename: Original filename (required)
            - source_path: Relative path to stored file
            - bank: Detected bank name
            - status: 'STAGED', 'NEEDS_REVIEW', 'COMMITTED', 'FAILED'
            - job_id: Optional job reference
            - opening_balance_paise: Opening balance in paise
            - closing_balance_paise: Closing balance in paise
    
    Returns:
        The import ID (UUID)
    """
    conn.execute("""
        INSERT INTO statement_imports 
        (id, source_filename, source_path, bank, status, job_id,
         opening_balance_paise, closing_balance_paise)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        import_data['id'],
        import_data['source_filename'],
        import_data.get('source_path'),
        import_data.get('bank'),
        import_data.get('status', 'STAGED'),
        import_data.get('job_id'),
        import_data.get('opening_balance_paise'),
        import_data.get('closing_balance_paise'),
    ))
    log.info("Statement import staged: %s (%s)", import_data['id'], import_data.get('bank', 'Unknown'))
    return import_data['id']


def get_statement_import(conn: sqlite3.Connection, import_id: str) -> dict | None:
    """Get statement import by ID with transaction counts.
    
    Returns:
        Dict with import details including:
        - id, source_filename, source_path, bank, status
        - created_at, committed_at, error
        - opening_balance_paise, closing_balance_paise, delta_paise
        - transaction_count
    """
    cur = conn.execute("""
        SELECT 
            si.*,
            COUNT(st.id) as transaction_count
        FROM statement_imports si
        LEFT JOIN staged_transactions st ON st.statement_id = si.id
        WHERE si.id = ?
        GROUP BY si.id
    """, (import_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def update_statement_import_status(
    conn: sqlite3.Connection,
    import_id: str, 
    status: str,
    error: str | None = None,
    delta_paise: int | None = None
) -> bool:
    """Update status and optionally error/delta.
    
    Args:
        conn: Database connection
        import_id: The import UUID
        status: New status ('STAGED', 'NEEDS_REVIEW', 'COMMITTED', 'FAILED')
        error: Optional error message
        delta_paise: Optional computed delta
    
    Returns:
        True if a row was updated
    """
    fields = ["status = ?"]
    params = [status]
    
    if error is not None:
        fields.append("error = ?")
        params.append(error)
    
    if delta_paise is not None:
        fields.append("delta_paise = ?")
        params.append(delta_paise)
    
    if status == 'COMMITTED':
        fields.append("committed_at = datetime('now')")
    
    params.append(import_id)
    
    sql = f"UPDATE statement_imports SET {', '.join(fields)} WHERE id = ?"
    cur = conn.execute(sql, params)
    
    if cur.rowcount > 0:
        log.info("Statement import %s status updated to %s", import_id, status)
    
    return cur.rowcount > 0


def update_statement_import_balances(
    conn: sqlite3.Connection,
    import_id: str, 
    opening_balance_paise: int, 
    closing_balance_paise: int
) -> bool:
    """Update opening/closing balances for a statement import.
    
    Args:
        conn: Database connection
        import_id: The import UUID
        opening_balance_paise: Opening balance in paise
        closing_balance_paise: Closing balance in paise
    
    Returns:
        True if a row was updated
    """
    cur = conn.execute("""
        UPDATE statement_imports 
        SET opening_balance_paise = ?,
            closing_balance_paise = ?
        WHERE id = ?
    """, (opening_balance_paise, closing_balance_paise, import_id))
    
    if cur.rowcount > 0:
        log.info("Statement import %s balances updated: opening=%d, closing=%d", 
                 import_id, opening_balance_paise, closing_balance_paise)
    
    return cur.rowcount > 0


def list_statement_imports(
    conn: sqlite3.Connection,
    status: str | None = None,
    page: int = 1,
    per_page: int = 50
) -> PaginatedResult:
    """List statement imports with optional status filter.
    
    Returns:
        PaginatedResult with items containing import details
    """
    where_clause = "WHERE si.status = ?" if status else ""
    params = [status] if status else []
    
    base_query = f"""
        SELECT 
            si.id, si.source_filename, si.bank, si.status,
            si.created_at, si.committed_at, si.error,
            si.opening_balance_paise, si.closing_balance_paise, si.delta_paise,
            COUNT(st.id) as transaction_count
        FROM statement_imports si
        LEFT JOIN staged_transactions st ON st.statement_id = si.id
        {where_clause}
        GROUP BY si.id
        ORDER BY si.created_at DESC
    """
    
    count_query = f"""
        SELECT COUNT(*) FROM statement_imports si {where_clause}
    """
    
    return paginate_query(
        conn,
        base_query.strip(),
        count_query.strip(),
        tuple(params),
        page,
        per_page,
    )


def delete_statement_import(conn: sqlite3.Connection, import_id: str) -> bool:
    """Delete a statement import and all related staged data.
    Cascades to staged_transactions and statement_pages via FK.
    
    Args:
        conn: Database connection
        import_id: The import UUID
    
    Returns:
        True if deleted
    """
    cur = conn.execute("DELETE FROM statement_imports WHERE id = ?", (import_id,))
    if cur.rowcount > 0:
        log.info("Statement import %s deleted", import_id)
    return cur.rowcount > 0


def get_statement_import_source_path(conn: sqlite3.Connection, import_id: str) -> Optional[str]:
    """Get the source PDF path for a statement import.
    
    Args:
        conn: Database connection
        import_id: The import UUID
    
    Returns:
        Source path (relative to data dir) or None
    """
    cur = conn.execute(
        "SELECT source_path FROM statement_imports WHERE id = ?",
        (import_id,)
    )
    row = cur.fetchone()
    return row['source_path'] if row else None


# ============================================================
# Staged Transaction CRUD
# ============================================================

def insert_staged_transactions(conn: sqlite3.Connection, statement_id: str, transactions: list[dict]) -> int:
    """Bulk insert staged transactions.
    
    Args:
        conn: Database connection
        statement_id: The import UUID
        transactions: List of transaction dicts with keys:
            - date: Original date string
            - date_iso: Parsed ISO date
            - description: Transaction description
            - debit_paise: Debit amount in paise
            - credit_paise: Credit amount in paise
            - balance_paise: Running balance if available
            - raw_row_json: Original row as JSON string
            - row_hash: Hash for deduplication
            - page_number: Page number in PDF
    
    Returns:
        Count of rows inserted
    """
    if not transactions:
        return 0

    inserted = 0
    for seq, txn in enumerate(transactions):
        txn_id = str(uuid.uuid4())
        
        cur = conn.execute("""
            INSERT INTO staged_transactions 
            (id, statement_id, page_number, date, date_iso, description,
             debit_paise, credit_paise, balance_paise, raw_row_json, 
             row_hash, sequence_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn_id,
            statement_id,
            txn.get('page_number'),
            txn.get('date', ''),
            txn.get('date_iso'),
            txn.get('description', ''),
            txn.get('debit_paise', 0),
            txn.get('credit_paise', 0),
            txn.get('balance_paise'),
            txn.get('raw_row_json'),
            txn.get('row_hash'),
            seq,
        ))
        inserted += cur.rowcount
    
    log.info("Inserted %d staged transactions for import %s", inserted, statement_id)
    return inserted


def get_staged_transactions(conn: sqlite3.Connection, statement_id: str) -> list[dict]:
    """Get all staged transactions for a statement, ordered by sequence.
    
    Args:
        conn: Database connection
        statement_id: The import UUID
    
    Returns:
        List of staged transaction dicts
    """
    cur = conn.execute("""
        SELECT * FROM staged_transactions
        WHERE statement_id = ?
        ORDER BY sequence_num
    """, (statement_id,))
    return [dict(row) for row in cur.fetchall()]


def get_staged_transaction_summary(conn: sqlite3.Connection, statement_id: str) -> dict:
    """Get sum of debits/credits and count for a statement.
    
    Args:
        conn: Database connection
        statement_id: The import UUID
    
    Returns:
        Dict with total_debits_paise, total_credits_paise, transaction_count
    """
    cur = conn.execute("""
        SELECT 
            COALESCE(SUM(debit_paise), 0) as total_debits_paise,
            COALESCE(SUM(credit_paise), 0) as total_credits_paise,
            COUNT(*) as transaction_count
        FROM staged_transactions
        WHERE statement_id = ?
    """, (statement_id,))
    row = cur.fetchone()
    return {
        'total_debits_paise': row['total_debits_paise'],
        'total_credits_paise': row['total_credits_paise'],
        'transaction_count': row['transaction_count']
    }


def clear_staged_transactions(conn: sqlite3.Connection, statement_id: str) -> int:
    """Delete all staged transactions for a statement.
    Used when rebuilding transactions from corrected extraction.
    
    Args:
        conn: Database connection
        statement_id: The import UUID
    
    Returns:
        Number of rows deleted
    """
    cur = conn.execute(
        "DELETE FROM staged_transactions WHERE statement_id = ?",
        (statement_id,)
    )
    if cur.rowcount > 0:
        log.info("Cleared %d staged transactions for %s", cur.rowcount, statement_id)
    return cur.rowcount


def update_staged_transaction_amounts(conn: sqlite3.Connection, txn_id: str, debit_paise: int, credit_paise: int) -> bool:
    """Update the debit/credit amounts of a staged transaction.
    
    Args:
        conn: Database connection
        txn_id: The staged transaction UUID
        debit_paise: New debit amount in paise
        credit_paise: New credit amount in paise
    
    Returns:
        True if a row was updated
    """
    cur = conn.execute("""
        UPDATE staged_transactions 
        SET debit_paise = ?, credit_paise = ?
        WHERE id = ?
    """, (debit_paise, credit_paise, txn_id))
    
    if cur.rowcount > 0:
        log.debug("Updated staged transaction %s: debit=%d, credit=%d", 
                 txn_id, debit_paise, credit_paise)
    
    return cur.rowcount > 0


def merge_staged_transactions(
    conn: sqlite3.Connection,
    keep_txn_id: str, 
    remove_txn_id: str, 
    new_debit_paise: int, 
    new_credit_paise: int,
    merged_description: str
) -> bool:
    """Merge two staged transactions.
    Updates the kept transaction with merged amounts and removes the other.
    
    Args:
        conn: Database connection
        keep_txn_id: The transaction to keep and update
        remove_txn_id: The transaction to remove
        new_debit_paise: Merged debit amount
        new_credit_paise: Merged credit amount
        merged_description: Combined description
    
    Returns:
        True if merge was successful
    """
    # Update the kept transaction
    cur = conn.execute("""
        UPDATE staged_transactions 
        SET debit_paise = ?, credit_paise = ?, description = ?
        WHERE id = ?
    """, (new_debit_paise, new_credit_paise, merged_description, keep_txn_id))
    
    if cur.rowcount == 0:
        return False
    
    # Remove the other transaction
    cur = conn.execute("""
        DELETE FROM staged_transactions WHERE id = ?
    """, (remove_txn_id,))
    
    if cur.rowcount > 0:
        log.info("Merged staged transactions: kept %s, removed %s", 
                 keep_txn_id, remove_txn_id)
    
    return cur.rowcount > 0


def clear_and_insert_staged_transactions(
    conn: sqlite3.Connection,
    statement_id: str,
    transactions: list[dict]
) -> int:
    """Atomically clear existing staged transactions and insert new ones.
    Used by bbox re-extraction to replace transactions.
    
    Args:
        conn: Database connection
        statement_id: The import UUID
        transactions: List of new transaction dicts
    
    Returns:
        Count of rows inserted
    """
    if not transactions:
        return 0

    # Clear existing transactions
    conn.execute(
        "DELETE FROM staged_transactions WHERE statement_id = ?",
        (statement_id,)
    )
    deleted = conn.total_changes
    
    # Insert new transactions
    inserted = 0
    for seq, txn in enumerate(transactions):
        txn_id = str(uuid.uuid4())
        
        # Build raw_row_json from raw data if available
        raw_json = txn.get('raw')
        if isinstance(raw_json, list):
            raw_row_json = json_mod.dumps(raw_json)
        else:
            raw_row_json = json_mod.dumps(raw_json) if raw_json else None
        
        cur = conn.execute(
            """
            INSERT INTO staged_transactions 
            (id, statement_id, page_number, date, date_iso, description,
             debit_paise, credit_paise, balance_paise, raw_row_json, sequence_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                txn_id,
                statement_id,
                txn.get('page_number', 1),
                txn.get('date', ''),
                txn.get('date_iso'),
                txn.get('description', ''),
                txn.get('debit_paise', 0),
                txn.get('credit_paise', 0),
                txn.get('balance_paise'),
                raw_row_json,
                seq,
            )
        )
        inserted += cur.rowcount
    
    log.info(
        "Replaced staged transactions for %s: deleted %s, inserted %d",
        statement_id, deleted, inserted
    )
    return inserted


# ============================================================
# Fingerprint Operations
# ============================================================

def update_statement_import_fingerprint(
    conn: sqlite3.Connection,
    import_id: str,
    fingerprint: str,
    template_id: Optional[str] = None,
    bbox_norm_json: Optional[str] = None
) -> bool:
    """Update fingerprint and template info for a statement import.
    
    Args:
        conn: Database connection
        import_id: The import UUID
        fingerprint: Computed PDF fingerprint
        template_id: Optional matched template ID
        bbox_norm_json: Optional JSON string of bbox_norm used
    
    Returns:
        True if updated
    """
    cur = conn.execute(
        """
        UPDATE statement_imports
        SET fingerprint = ?,
            template_id = ?,
            bbox_norm_json = ?
        WHERE id = ?
        """,
        (fingerprint, template_id, bbox_norm_json, import_id)
    )
    if cur.rowcount > 0:
        log.debug("Updated fingerprint for import %s: %s...", import_id, fingerprint[:16])
    return cur.rowcount > 0


def get_statement_import_with_fingerprint(conn: sqlite3.Connection, import_id: str) -> Optional[dict]:
    """Get statement import with fingerprint and template info.
    
    Args:
        conn: Database connection
        import_id: The import UUID
    
    Returns:
        Dict with import details including fingerprint, template_id, bbox_norm_json
    """
    cur = conn.execute(
        """
        SELECT 
            si.*,
            COUNT(st.id) as transaction_count,
            lt.bbox_norm_json as template_bbox_norm_json
        FROM statement_imports si
        LEFT JOIN staged_transactions st ON st.statement_id = si.id
        LEFT JOIN layout_templates lt ON si.template_id = lt.id
        WHERE si.id = ?
        GROUP BY si.id
        """,
        (import_id,)
    )
    row = cur.fetchone()
    if row is None:
        return None
    
    result = dict(row)
    
    # Parse bbox_norm_json if present
    if result.get('bbox_norm_json'):
        try:
            result['bbox_norm'] = json_mod.loads(result['bbox_norm_json'])
        except json_mod.JSONDecodeError:
            result['bbox_norm'] = None
    
    # Parse template bbox if present
    if result.get('template_bbox_norm_json'):
        try:
            result['template_bbox_norm'] = json_mod.loads(result['template_bbox_norm_json'])
        except json_mod.JSONDecodeError:
            result['template_bbox_norm'] = None
    
    return result
