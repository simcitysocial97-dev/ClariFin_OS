"""
Statement Validator for Staging Pipeline
=========================================
Validates staged statements before commit to immutable ledger.

Uses the B0 validation_engine helper for deterministic delta calculation.
"""

import json
import os
import hashlib

from src.db import FinanceDB
from src.engines.validation_engine import compute_statement_delta_paise


def validate_staged_statement(db: FinanceDB, import_id: str, auto_quarantine: bool = False) -> dict:
    """
    Validate a staged statement by computing delta from opening/closing balances.
    
    Args:
        db: FinanceDB instance
        import_id: The statement import UUID
        auto_quarantine: DEPRECATED - no longer creates quarantine. Kept for API compatibility.
    
    Returns:
        Dict with:
            - valid: bool (True if can be committed)
            - delta_paise: int (discrepancy amount)
            - opening_balance_paise: int | None
            - closing_balance_paise: int | None
            - total_credits_paise: int
            - total_debits_paise: int
            - transaction_count: int
            - reason: str | None (why validation failed)
            - quarantine_created: bool (whether quarantine entries were created)
    """
    # Get the import record
    import_record = db.get_statement_import(import_id)
    if not import_record:
        return {
            'valid': False,
            'delta_paise': 0,
            'opening_balance_paise': None,
            'closing_balance_paise': None,
            'total_credits_paise': 0,
            'total_debits_paise': 0,
            'transaction_count': 0,
            'reason': 'Import record not found',
            'quarantine_created': False
        }
    
    # Get transaction summary
    summary = db.get_staged_transaction_summary(import_id)
    
    opening = import_record.get('opening_balance_paise')
    closing = import_record.get('closing_balance_paise')
    
    # If opening or closing is missing, we can't validate
    # But we still allow commit (will be marked as NEEDS_REVIEW)
    if opening is None or closing is None:
        return {
            'valid': False,
            'delta_paise': None,
            'opening_balance_paise': opening,
            'closing_balance_paise': closing,
            'total_credits_paise': summary.get('total_credits_paise', 0),
            'total_debits_paise': summary.get('total_debits_paise', 0),
            'transaction_count': summary.get('transaction_count', 0),
            'reason': 'Missing opening or closing balance for validation',
            'quarantine_created': False
        }
    
    # Get credits and debits lists for validation
    # We need individual amounts for the validation engine
    transactions = db.get_staged_transactions(import_id)
    credits_paise = [t['credit_paise'] for t in transactions if t['credit_paise'] > 0]
    debits_paise = [t['debit_paise'] for t in transactions if t['debit_paise'] > 0]
    
    # Compute delta using the B0 validation engine
    delta = compute_statement_delta_paise(
        opening_balance_paise=opening,
        closing_balance_paise=closing,
        credits_paise=credits_paise,
        debits_paise=debits_paise
    )
    
    # Valid if delta is 0 (perfect balance)
    is_valid = delta == 0
    quarantine_created = False
    
    # Create quarantine entries if validation failed and auto_quarantine is enabled
    if not is_valid and auto_quarantine:
        quarantine_created = _create_quarantine_for_statement(db, import_id, delta, transactions)
    
    return {
        'valid': is_valid,
        'delta_paise': delta,
        'opening_balance_paise': opening,
        'closing_balance_paise': closing,
        'total_credits_paise': summary.get('total_credits_paise', 0),
        'total_debits_paise': summary.get('total_debits_paise', 0),
        'transaction_count': summary.get('transaction_count', 0),
        'reason': None if is_valid else f'Statement delta is {delta} paise (expected 0)',
        'quarantine_created': quarantine_created
    }


def create_quarantine_for_extraction_error(
    db: FinanceDB,
    import_id: str,
    reason: str,
    raw_extraction_json: dict | None = None
) -> str | None:
    """
    DEPRECATED: Quarantine feature removed. This function is now a no-op.
    
    Previously created a quarantine entry for an extraction error.
    Kept for backwards compatibility with existing code.
    
    Args:
        db: FinanceDB instance (unused)
        import_id: The statement import UUID (unused)
        reason: Why the extraction failed (unused)
        raw_extraction_json: Optional raw extraction data (unused)
    
    Returns:
        None (quarantine feature removed)
    """
    # Quarantine feature has been removed - no-op for backwards compatibility
    return None


def _create_quarantine_for_statement(
    db: FinanceDB, 
    import_id: str, 
    delta_paise: int,
    transactions: list
) -> bool:
    """
    DEPRECATED: This function is no longer called during validation.
    Quarantine is now only created for extraction errors, not validation failures.
    
    Kept for potential future use and backwards compatibility.
    """
    return False


def commit_staged_statement(db: FinanceDB, import_id: str, member: str = "Self") -> dict:
    """
    Atomically commit staged transactions to the immutable ledger.
    
    This function:
    1. Validates the statement
    2. If valid, creates a statement record and inserts all transactions
    3. Updates the import status to COMMITTED
    4. If any step fails, rolls back and marks as FAILED
    
    Args:
        db: FinanceDB instance
        import_id: The statement import UUID
        member: Member name for transactions
    
    Returns:
        Dict with:
            - success: bool
            - inserted: int (number of transactions inserted)
            - skipped: int (number of duplicates skipped)
            - error: str | None
            - auto_heal_applied: bool (DEPRECATED: always False)
    """
    from src.logger import log
    from src.engines.transaction_classifier import classify_transaction
    
    # First validate
    validation = validate_staged_statement(db, import_id)
    
    # If not valid, quarantine for manual review
    if not validation['valid']:
        db.update_statement_import_status(
            import_id, 
            'NEEDS_REVIEW',
            delta_paise=validation['delta_paise']
        )
        return {
            'success': False,
            'inserted': 0,
            'skipped': 0,
            'error': validation['reason'] or 'Statement validation failed',
            'auto_heal_applied': False
        }
    
    # Get the import record
    import_record = db.get_statement_import(import_id)
    if not import_record:
        return {
            'success': False,
            'inserted': 0,
            'skipped': 0,
            'error': 'Import record not found',
            'auto_heal_applied': False
        }
    
    # Get staged transactions
    staged_txns = db.get_staged_transactions(import_id)
    if not staged_txns:
        return {
            'success': False,
            'inserted': 0,
            'skipped': 0,
            'error': 'No staged transactions found',
            'auto_heal_applied': False
        }
    
    try:
        with db.transaction() as conn:
            # Step 1: Create statement record
            cur = conn.execute("""
                INSERT INTO statements (bank, file_name, source, 
                                       statement_period_from, statement_period_to)
                VALUES (?, ?, 'pdf_staged', ?, ?)
            """, (
                import_record.get('bank', 'Unknown'),
                import_record.get('source_filename', f'staged_{import_id}.pdf'),
                # Try to derive period from transactions
                staged_txns[0].get('date_iso') if staged_txns else None,
                staged_txns[-1].get('date_iso') if staged_txns else None
            ))
            statement_id = cur.lastrowid
            
            # Step 2: Convert staged transactions to format expected by insert_transactions
            # We need to insert directly here since we're in a transaction
            account_id = import_record.get('bank', 'Unknown')
            inserted = 0
            skipped = 0
            
            for seq, txn in enumerate(staged_txns):
                date = txn.get('date', '')
                date_iso = txn.get('date_iso', '')
                description = txn.get('description', '')
                debit_paise = txn.get('debit_paise', 0)
                credit_paise = txn.get('credit_paise', 0)
                
                # Determine type and amount
                if debit_paise > 0:
                    txn_type = 'debit'
                    amount = debit_paise / 100.0
                elif credit_paise > 0:
                    txn_type = 'credit'
                    amount = credit_paise / 100.0
                else:
                    continue  # Skip zero-amount transactions
                
                # Compute hash for deduplication
                hash_input = f"{account_id}|{date_iso}|{description}|{debit_paise}|{credit_paise}"
                hash_signature = hashlib.sha256(hash_input.encode()).hexdigest().lower()
                
                # debit/credit are GENERATED ALWAYS columns - do not include in INSERT
                cur = conn.execute("""
                    INSERT OR IGNORE INTO transactions
                        (statement_id, sequence_num, date, description, amount, type,
                         amount_paise, date_iso, hash_signature, account_id, member)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    statement_id,
                    seq,
                    date,
                    description,
                    amount,
                    txn_type,
                    debit_paise + credit_paise,
                    date_iso,
                    hash_signature,
                    account_id,
                    member
                ))
                
                if cur.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1

            # Step 2.5: Classify transactions after insertion
            # Now that we have transaction IDs, we can update the nature column
            if inserted > 0:
                # Get the IDs of the newly inserted transactions
                cur = conn.execute("""
                    SELECT id, description, amount_paise, type, category, account_id
                    FROM transactions
                    WHERE statement_id = ? AND nature IS NULL
                """, (statement_id,))
                new_transactions = cur.fetchall()

                # Classify each transaction and update nature
                for txn in new_transactions:
                    nature = classify_transaction({
                        'description': txn['description'],
                        'amount_paise': txn['amount_paise'],
                        'type': txn['type'],
                        'category': txn['category'],
                        'account_id': txn['account_id']
                    })

                    # Update the nature column (trigger allows this)
                    conn.execute("""
                        UPDATE transactions SET nature = ? WHERE id = ?
                    """, (nature, txn['id']))

            # Step 3: Update import status to COMMITTED
            conn.execute("""
                UPDATE statement_imports 
                SET status = 'COMMITTED', 
                    committed_at = datetime('now'),
                    delta_paise = ?
                WHERE id = ?
            """, (validation['delta_paise'], import_id))
            
            log.info(
                "Committed staged import %s: %d inserted, %d skipped",
                import_id, inserted, skipped
            )
            
            return {
                'success': True,
                'inserted': inserted,
                'skipped': skipped,
                'error': None,
                'auto_heal_applied': False
            }
            
    except Exception as e:
        # Mark as failed
        db.update_statement_import_status(
            import_id,
            'FAILED',
            error=str(e)
        )
        return {
            'success': False,
            'inserted': 0,
            'skipped': 0,
            'error': str(e),
            'auto_heal_applied': False
        }


def revalidate_staged_statement(db: FinanceDB, import_id: str, member: str = "Self") -> dict:
    """
    Revalidate a statement by rebuilding staged transactions from corrected extraction.
    
    This function:
    1. Fetches all quarantine_pages for the statement
    2. Rebuilds staged_transactions from the latest available extraction JSON:
       - Uses corrected_extraction_json if present (from resolved quarantine)
       - Else uses raw_extraction_json
    3. Clears existing staged_transactions for the statement
    4. Inserts rebuilt transactions
    5. Recomputes opening/closing + delta
    6. If delta == 0, atomically commits staged_transactions to immutable ledger
    7. Updates statement_imports status accordingly
    
    Args:
        db: FinanceDB instance
        import_id: The statement import UUID
        member: Member name for transactions
    
    Returns:
        Dict with:
            - success: bool
            - delta_paise: int (new computed delta)
            - valid: bool (whether validation passed)
            - committed: bool (whether transactions were committed)
            - inserted: int (number of transactions inserted to ledger)
            - skipped: int (number of duplicates skipped)
            - error: str | None
    """
    from src.logger import log
    
    # Get the import record
    import_record = db.get_statement_import(import_id)
    if not import_record:
        return {
            'success': False,
            'delta_paise': 0,
            'valid': False,
            'committed': False,
            'inserted': 0,
            'skipped': 0,
            'error': 'Import record not found'
        }
    
    # Get quarantine pages for this statement
    quarantine_pages = db.get_quarantine_pages_for_statement(import_id)
    
    if not quarantine_pages:
        # No quarantine pages - just revalidate existing staged transactions
        validation = validate_staged_statement(db, import_id, auto_quarantine=False)
        
        if validation['valid']:
            # Can commit directly
            commit_result = commit_staged_statement(db, import_id, member=member)
            return {
                'success': commit_result['success'],
                'delta_paise': validation['delta_paise'],
                'valid': True,
                'committed': commit_result['success'],
                'inserted': commit_result.get('inserted', 0),
                'skipped': commit_result.get('skipped', 0),
                'error': commit_result.get('error')
            }
        else:
            # Still invalid - update status
            db.update_statement_import_status(
                import_id,
                'NEEDS_REVIEW',
                delta_paise=validation['delta_paise']
            )
            return {
                'success': False,
                'delta_paise': validation['delta_paise'],
                'valid': False,
                'committed': False,
                'inserted': 0,
                'skipped': 0,
                'error': validation.get('reason', 'Statement validation failed')
            }
    
    # Rebuild staged transactions from quarantine pages
    rebuilt_transactions = []
    
    for qp in quarantine_pages:
        # Use corrected extraction if available, else raw
        extraction_json = qp.get('corrected_extraction_json') or qp.get('raw_extraction_json')
        
        if not extraction_json:
            continue
        
        try:
            extraction = json.loads(extraction_json)
            page_transactions = extraction.get('transactions', [])
            page_number = qp.get('page_number', 1)
            
            for txn in page_transactions:
                rebuilt_transactions.append({
                    'date': txn.get('date', ''),
                    'date_iso': txn.get('date_iso'),
                    'description': txn.get('description', ''),
                    'debit_paise': txn.get('debit_paise', 0),
                    'credit_paise': txn.get('credit_paise', 0),
                    'balance_paise': txn.get('balance_paise'),
                    'raw_row_json': txn.get('raw_row_json'),
                    'page_number': page_number
                })
        except json.JSONDecodeError:
            log.error("Failed to parse extraction JSON for quarantine %s", qp.get('id'))
            continue
    
    if not rebuilt_transactions:
        return {
            'success': False,
            'delta_paise': 0,
            'valid': False,
            'committed': False,
            'inserted': 0,
            'skipped': 0,
            'error': 'No transactions could be rebuilt from quarantine pages'
        }
    
    # Clear existing staged transactions
    db.clear_staged_transactions(import_id)
    
    # Insert rebuilt transactions
    db.insert_staged_transactions(import_id, rebuilt_transactions)
    
    # Revalidate with auto_quarantine disabled (we already have quarantine entries)
    validation = validate_staged_statement(db, import_id, auto_quarantine=False)
    
    if validation['valid']:
        # Delta is 0 - commit to ledger
        commit_result = commit_staged_statement(db, import_id, member=member)
        
        return {
            'success': commit_result['success'],
            'delta_paise': validation['delta_paise'],
            'valid': True,
            'committed': commit_result['success'],
            'inserted': commit_result.get('inserted', 0),
            'skipped': commit_result.get('skipped', 0),
            'error': commit_result.get('error')
        }
    else:
        # Still invalid - update status and delta
        db.update_statement_import_status(
            import_id,
            'NEEDS_REVIEW',
            delta_paise=validation['delta_paise']
        )
        
        return {
            'success': False,
            'delta_paise': validation['delta_paise'],
            'valid': False,
            'committed': False,
            'inserted': 0,
            'skipped': 0,
            'error': validation.get('reason', 'Statement validation failed after revalidation')
        }
