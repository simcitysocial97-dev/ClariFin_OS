"""
Ledger Audit Engine
===================

Minimal audit and integrity validation for the transaction ledger.
Read-only operations only. No mutations.

Phase 2C: Essential audit guarantees without expanding system complexity.
"""

import hashlib
from typing import Dict, List, Any, TYPE_CHECKING

from src.logger import log

if TYPE_CHECKING:
    from src.db import FinanceDB


def validate_ledger_integrity(db: "FinanceDB") -> Dict[str, Any]:
    """
    Validate ledger invariants.
    
    Checks:
    1. account_id NOT NULL
    2. debit >= 0
    3. credit >= 0
    4. NOT (debit > 0 AND credit > 0)
    5. hash_signature NOT NULL
    6. hash_signature uniqueness
    
    Returns:
        {
            "status": "PASS" or "FAIL",
            "violations": [...]
        }
    """
    violations = []
    
    with db.connection() as conn:
        cur = conn.cursor()
        
        # Check 1: account_id NOT NULL
        cur.execute("""
            SELECT id, account_id FROM transactions 
            WHERE account_id IS NULL OR account_id = ''
        """)
        for row in cur.fetchall():
            violations.append({
                "type": "NULL_ACCOUNT_ID",
                "transaction_id": row[0],
                "message": f"Transaction {row[0]} has null or empty account_id"
            })
        
        # Check 2: debit >= 0
        cur.execute("""
            SELECT id, debit FROM transactions 
            WHERE debit < 0
        """)
        for row in cur.fetchall():
            violations.append({
                "type": "NEGATIVE_DEBIT",
                "transaction_id": row[0],
                "message": f"Transaction {row[0]} has negative debit: {row[1]}"
            })
        
        # Check 3: credit >= 0
        cur.execute("""
            SELECT id, credit FROM transactions 
            WHERE credit < 0
        """)
        for row in cur.fetchall():
            violations.append({
                "type": "NEGATIVE_CREDIT",
                "transaction_id": row[0],
                "message": f"Transaction {row[0]} has negative credit: {row[1]}"
            })
        
        # Check 4: NOT (debit > 0 AND credit > 0)
        cur.execute("""
            SELECT id, debit, credit FROM transactions 
            WHERE debit > 0 AND credit > 0
        """)
        for row in cur.fetchall():
            violations.append({
                "type": "DUAL_ENTRY",
                "transaction_id": row[0],
                "message": f"Transaction {row[0]} has both debit ({row[1]}) and credit ({row[2]})"
            })
        
        # Check 5: hash_signature NOT NULL
        cur.execute("""
            SELECT id FROM transactions 
            WHERE hash_signature IS NULL OR hash_signature = ''
        """)
        for row in cur.fetchall():
            violations.append({
                "type": "NULL_HASH",
                "transaction_id": row[0],
                "message": f"Transaction {row[0]} has null or empty hash_signature"
            })
        
        # Check 6: hash_signature uniqueness
        cur.execute("""
            SELECT hash_signature, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
            FROM transactions 
            WHERE hash_signature IS NOT NULL AND hash_signature != ''
            GROUP BY hash_signature
            HAVING COUNT(*) > 1
        """)
        for row in cur.fetchall():
            violations.append({
                "type": "DUPLICATE_HASH",
                "hash_signature": row[0],
                "transaction_ids": [int(x) for x in row[2].split(",")],
                "message": f"Duplicate hash_signature found in transactions: {row[2]}"
            })
    
    return {
        "status": "PASS" if len(violations) == 0 else "FAIL",
        "violation_count": len(violations),
        "violations": violations
    }


def verify_hash_signatures(db: "FinanceDB") -> Dict[str, Any]:
    """
    Verify hash signatures by recomputing and comparing.
    
    For each transaction:
    1. Recompute hash using existing hash logic
    2. Compare with stored hash_signature
    3. Collect mismatches
    
    Hash formula: SHA256(account_id | date_iso | description | debit | credit)
    
    Returns:
        {
            "status": "PASS" or "FAIL",
            "tampered_transactions": [...]
        }
    """
    tampered = []
    
    with db.connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, account_id, date_iso, description, debit, credit, hash_signature
            FROM transactions
            WHERE hash_signature IS NOT NULL AND hash_signature != ''
        """)
        
        for row in cur.fetchall():
            # Recompute hash
            hash_input = f"{row[1]}|{row[2]}|{row[3]}|{row[4]}|{row[5]}"
            computed_hash = hashlib.sha256(hash_input.encode()).hexdigest().lower()
            stored_hash = row[6].lower()
            
            if computed_hash != stored_hash:
                tampered.append({
                    "transaction_id": row[0],
                    "stored_hash": stored_hash,
                    "computed_hash": computed_hash,
                    "message": f"Transaction {row[0]} hash mismatch - possible tampering"
                })
    
    return {
        "status": "PASS" if len(tampered) == 0 else "FAIL",
        "tampered_count": len(tampered),
        "tampered_transactions": tampered
    }


def run_full_audit(db: "FinanceDB") -> Dict[str, Any]:
    """
    Run all audit checks and return combined report.
    
    Returns:
        {
            "ledger_integrity": {...},
            "hash_verification": {...},
            "overall_status": "PASS" or "FAIL"
        }
    """
    log.info("Running ledger audit")
    
    integrity = validate_ledger_integrity(db)
    hashes = verify_hash_signatures(db)
    
    overall = "PASS" if (integrity["status"] == "PASS" and hashes["status"] == "PASS") else "FAIL"
    
    return {
        "overall_status": overall,
        "ledger_integrity": integrity,
        "hash_verification": hashes
    }
