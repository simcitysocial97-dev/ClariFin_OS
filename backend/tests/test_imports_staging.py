"""
Tests for Staging-based Import Pipeline
=========================================
Tests atomic commit behavior and validation.

Run: python -m pytest tests/test_imports_staging.py -v
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from engines.statement_validator import validate_staged_statement, commit_staged_statement


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    # Create temp file for database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create FinanceDB instance
    db = FinanceDB(db_path=db_path)
    
    yield db
    
    # Cleanup
    db.close()
    os.unlink(db_path)


@pytest.fixture
def sample_staged_import(test_db):
    """Create a sample staged import with transactions."""
    import_id = "test-import-123"
    
    # Insert statement import
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test_statement.pdf',
        'source_path': 'uploads/test_statement.pdf',
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': 100000,  # ₹1000.00
        'closing_balance_paise': 50000,   # ₹500.00
    })
    
    # Insert staged transactions
    # Opening: 1000, Credits: 500, Debits: 1000, Expected Closing: 500
    transactions = [
        {
            'date': '01/01/2025',
            'date_iso': '2025-01-01',
            'description': 'Opening Balance',
            'debit_paise': 0,
            'credit_paise': 0,
            'balance_paise': 100000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
        {
            'date': '02/01/2025',
            'date_iso': '2025-01-02',
            'description': 'Salary Credit',
            'debit_paise': 0,
            'credit_paise': 50000,  # ₹500.00 credit
            'balance_paise': 150000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
        {
            'date': '03/01/2025',
            'date_iso': '2025-01-03',
            'description': 'Rent Payment',
            'debit_paise': 100000,  # ₹1000.00 debit
            'credit_paise': 0,
            'balance_paise': 50000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
    ]
    
    test_db.insert_staged_transactions(import_id, transactions)
    
    return import_id


@pytest.fixture
def unbalanced_staged_import(test_db):
    """Create an unbalanced staged import."""
    import_id = "test-import-unbalanced"
    
    # Insert statement import with wrong closing balance
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test_unbalanced.pdf',
        'source_path': 'uploads/test_unbalanced.pdf',
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': 100000,  # ₹1000.00
        'closing_balance_paise': 100000,  # Wrong! Should be 500
    })
    
    # Same transactions as balanced case
    transactions = [
        {
            'date': '02/01/2025',
            'date_iso': '2025-01-02',
            'description': 'Salary Credit',
            'debit_paise': 0,
            'credit_paise': 50000,
            'balance_paise': 150000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
        {
            'date': '03/01/2025',
            'date_iso': '2025-01-03',
            'description': 'Rent Payment',
            'debit_paise': 100000,
            'credit_paise': 0,
            'balance_paise': 50000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
    ]
    
    test_db.insert_staged_transactions(import_id, transactions)
    
    return import_id


@pytest.fixture
def missing_balance_import(test_db):
    """Create a staged import with missing balance."""
    import_id = "test-import-missing-balance"
    
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test_missing.pdf',
        'source_path': 'uploads/test_missing.pdf',
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': None,
        'closing_balance_paise': None,
    })
    
    transactions = [
        {
            'date': '02/01/2025',
            'date_iso': '2025-01-02',
            'description': 'Transaction 1',
            'debit_paise': 10000,
            'credit_paise': 0,
            'balance_paise': None,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
    ]
    
    test_db.insert_staged_transactions(import_id, transactions)
    
    return import_id


# ============================================================
# Test 1: Balanced Statement Validation
# ============================================================

def test_balanced_statement_delta_zero(test_db, sample_staged_import):
    """Test that a balanced statement returns delta=0."""
    result = validate_staged_statement(test_db, sample_staged_import)
    
    assert result['valid'] is True
    assert result['delta_paise'] == 0
    assert result['opening_balance_paise'] == 100000
    assert result['closing_balance_paise'] == 50000
    assert result['total_credits_paise'] == 50000
    assert result['total_debits_paise'] == 100000
    assert result['transaction_count'] == 3
    assert result['reason'] is None


# ============================================================
# Test 2: Unbalanced Statement Validation
# ============================================================

def test_unbalanced_statement_returns_delta(test_db, unbalanced_staged_import):
    """Test that an unbalanced statement returns non-zero delta."""
    result = validate_staged_statement(test_db, unbalanced_staged_import)
    
    assert result['valid'] is False
    # Opening: 100000 + Credits: 50000 - Debits: 100000 = Expected: 50000
    # Actual closing: 100000
    # Delta = 50000 - 100000 = -50000
    assert result['delta_paise'] == -50000
    assert result['reason'] is not None
    assert 'delta is -50000' in result['reason']


# ============================================================
# Test 3: Missing Balance Validation
# ============================================================

def test_missing_balances_cannot_validate(test_db, missing_balance_import):
    """Test that missing opening/closing balance fails validation."""
    result = validate_staged_statement(test_db, missing_balance_import)
    
    assert result['valid'] is False
    assert result['opening_balance_paise'] is None
    assert result['closing_balance_paise'] is None
    assert result['reason'] == 'Missing opening or closing balance for validation'


def test_missing_balances_returns_null_delta(test_db, missing_balance_import):
    """Test that missing balances returns delta_paise=None (not 0)."""
    result = validate_staged_statement(test_db, missing_balance_import)
    
    # Delta should be None (not 0) when validation cannot run due to missing balances
    assert result['delta_paise'] is None, f"Expected delta_paise to be None, got {result['delta_paise']}"
    
    # This distinguishes "unvalidated" from "validated but balanced (delta=0)"
    assert result['valid'] is False


# ============================================================
# Test 4: Atomic Commit - Balanced Statement
# ============================================================

def test_commit_balanced_statement_inserts_transactions(test_db, sample_staged_import):
    """Test that a balanced statement commits successfully."""
    # Get initial transaction count
    initial_count = test_db.get_transaction_count()
    
    # Commit
    result = commit_staged_statement(test_db, sample_staged_import)
    
    # Should succeed
    assert result['success'] is True
    # Only 2 transactions inserted - opening balance row (0 debit/credit) is skipped
    assert result['inserted'] == 2
    assert result['error'] is None
    
    # Verify transactions were inserted (2 real transactions, opening balance skipped)
    new_count = test_db.get_transaction_count()
    assert new_count == initial_count + 2
    
    # Verify import status is COMMITTED
    import_record = test_db.get_statement_import(sample_staged_import)
    assert import_record['status'] == 'COMMITTED'
    assert import_record['committed_at'] is not None


# ============================================================
# Test 5: Atomic Commit - Unbalanced Statement Rejected
# ============================================================

def test_commit_unbalanced_statement_rejected(test_db, unbalanced_staged_import):
    """Test that an unbalanced statement is rejected and nothing inserted."""
    # Get initial transaction count
    initial_count = test_db.get_transaction_count()
    
    # Attempt commit
    result = commit_staged_statement(test_db, unbalanced_staged_import)
    
    # Should fail
    assert result['success'] is False
    assert result['inserted'] == 0
    assert result['error'] is not None
    
    # Verify NO transactions were inserted
    new_count = test_db.get_transaction_count()
    assert new_count == initial_count
    
    # Verify import status is NEEDS_REVIEW
    import_record = test_db.get_statement_import(unbalanced_staged_import)
    assert import_record['status'] == 'NEEDS_REVIEW'
    assert import_record['delta_paise'] == -50000


# ============================================================
# Test 6: Duplicate Detection on Commit
# ============================================================

def test_commit_skips_duplicates(test_db, sample_staged_import):
    """Test that duplicate transactions are skipped on commit."""
    # First commit
    result1 = commit_staged_statement(test_db, sample_staged_import)
    assert result1['success'] is True
    # Only 2 transactions inserted - opening balance row (0 debit/credit) is skipped
    assert result1['inserted'] == 2
    assert result1['skipped'] == 0
    
    # Create new staged import with same transactions
    import_id2 = "test-import-duplicate"
    test_db.insert_statement_import({
        'id': import_id2,
        'source_filename': 'test_duplicate.pdf',
        'source_path': 'uploads/test_duplicate.pdf',
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': 100000,
        'closing_balance_paise': 50000,
    })
    
    # Same transactions
    transactions = [
        {
            'date': '02/01/2025',
            'date_iso': '2025-01-02',
            'description': 'Salary Credit',
            'debit_paise': 0,
            'credit_paise': 50000,
            'balance_paise': 150000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
        {
            'date': '03/01/2025',
            'date_iso': '2025-01-03',
            'description': 'Rent Payment',
            'debit_paise': 100000,
            'credit_paise': 0,
            'balance_paise': 50000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
    ]
    test_db.insert_staged_transactions(import_id2, transactions)
    
    # Second commit
    result2 = commit_staged_statement(test_db, import_id2)
    
    # Should succeed but skip duplicates
    assert result2['success'] is True
    assert result2['inserted'] == 0  # All duplicates
    assert result2['skipped'] == 2


# ============================================================
# Test 7: Import Status Management
# ============================================================

def test_update_import_status(test_db, sample_staged_import):
    """Test that import status can be updated."""
    # Initial status
    record = test_db.get_statement_import(sample_staged_import)
    assert record['status'] == 'STAGED'
    
    # Update to NEEDS_REVIEW
    updated = test_db.update_statement_import_status(
        sample_staged_import, 
        'NEEDS_REVIEW',
        delta_paise=1000,
        error='Test error'
    )
    assert updated is True
    
    record = test_db.get_statement_import(sample_staged_import)
    assert record['status'] == 'NEEDS_REVIEW'
    assert record['delta_paise'] == 1000
    assert record['error'] == 'Test error'


# ============================================================
# Test 8: Delete Staged Import
# ============================================================

def test_delete_staged_import(test_db, sample_staged_import):
    """Test that staged imports can be deleted."""
    # Verify exists
    record = test_db.get_statement_import(sample_staged_import)
    assert record is not None
    
    # Delete
    deleted = test_db.delete_statement_import(sample_staged_import)
    assert deleted is True
    
    # Verify deleted
    record = test_db.get_statement_import(sample_staged_import)
    assert record is None
    
    # Verify staged transactions also deleted (cascade)
    transactions = test_db.get_staged_transactions(sample_staged_import)
    assert len(transactions) == 0


# ============================================================
# Test 9: List Imports Pagination
# ============================================================

def test_list_imports_pagination(test_db):
    """Test listing imports with pagination."""
    # Create multiple imports
    for i in range(5):
        import_id = f"test-import-list-{i}"
        test_db.insert_statement_import({
            'id': import_id,
            'source_filename': f'test_{i}.pdf',
            'source_path': f'uploads/test_{i}.pdf',
            'bank': 'Test Bank',
            'status': 'STAGED' if i < 3 else 'COMMITTED',
        })
    
    # List all
    result = test_db.list_statement_imports(page=1, per_page=10)
    assert result.total >= 5
    
    # Filter by status
    result = test_db.list_statement_imports(status='STAGED', page=1, per_page=10)
    assert result.total == 3


# ============================================================
# Test 10: Transaction Summary
# ============================================================

def test_staged_transaction_summary(test_db, sample_staged_import):
    """Test getting transaction summary for a staged import."""
    summary = test_db.get_staged_transaction_summary(sample_staged_import)
    
    assert summary['total_debits_paise'] == 100000
    assert summary['total_credits_paise'] == 50000
    assert summary['transaction_count'] == 3


# ============================================================
# Test 11: Set Balances and Commit (Balanced)
# ============================================================

@pytest.fixture
def missing_balance_import_for_set_balances(test_db):
    """Create a staged import with missing balances for set-balances testing."""
    import_id = "test-import-set-balances"
    
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test_missing_balances.pdf',
        'source_path': 'uploads/test_missing_balances.pdf',
        'bank': 'Test Bank',
        'status': 'NEEDS_REVIEW',
        'opening_balance_paise': None,
        'closing_balance_paise': None,
    })
    
    # Add transactions that would balance if opening=100000, closing=50000
    # Opening: 100000, +50000 credit, -100000 debit = 50000 closing
    transactions = [
        {
            'date': '02/01/2025',
            'date_iso': '2025-01-02',
            'description': 'Salary Credit',
            'debit_paise': 0,
            'credit_paise': 50000,
            'balance_paise': 150000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
        {
            'date': '03/01/2025',
            'date_iso': '2025-01-03',
            'description': 'Rent Payment',
            'debit_paise': 100000,
            'credit_paise': 0,
            'balance_paise': 50000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
    ]
    
    test_db.insert_staged_transactions(import_id, transactions)
    
    return import_id


def test_set_balances_and_commit(test_db, missing_balance_import_for_set_balances):
    """Test that setting balances allows commit when delta==0."""
    import_id = missing_balance_import_for_set_balances
    
    # Get initial transaction count
    initial_count = test_db.get_transaction_count()
    
    # Verify initial state
    import_record = test_db.get_statement_import(import_id)
    assert import_record['status'] == 'NEEDS_REVIEW'
    assert import_record['opening_balance_paise'] is None
    assert import_record['closing_balance_paise'] is None
    
    # Set balances that will result in delta==0
    # Opening: 100000, Credits: 50000, Debits: 100000, Expected Closing: 50000
    updated = test_db.update_statement_import_balances(import_id, 100000, 50000)
    assert updated is True
    
    # Verify balances updated
    import_record = test_db.get_statement_import(import_id)
    assert import_record['opening_balance_paise'] == 100000
    assert import_record['closing_balance_paise'] == 50000
    
    # Now revalidate - should commit since delta==0
    from src.engines.statement_validator import revalidate_staged_statement
    result = revalidate_staged_statement(test_db, import_id)
    
    # Should be valid and committed
    assert result['success'] is True
    assert result['valid'] is True
    assert result['committed'] is True
    assert result['delta_paise'] == 0
    assert result['inserted'] == 2  # Both transactions committed
    assert result['error'] is None
    
    # Verify transactions were inserted
    new_count = test_db.get_transaction_count()
    assert new_count == initial_count + 2
    
    # Verify import status is COMMITTED
    import_record = test_db.get_statement_import(import_id)
    assert import_record['status'] == 'COMMITTED'
    assert import_record['delta_paise'] == 0


# ============================================================
# Test 12: Set Balances and Remain NEEDS_REVIEW (Unbalanced)
# ============================================================

@pytest.fixture
def missing_balance_import_unbalanced(test_db):
    """Create a staged import with missing balances for unbalanced testing."""
    import_id = "test-import-set-balances-unbalanced"
    
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test_unbalanced_missing.pdf',
        'source_path': 'uploads/test_unbalanced_missing.pdf',
        'bank': 'Test Bank',
        'status': 'NEEDS_REVIEW',
        'opening_balance_paise': None,
        'closing_balance_paise': None,
    })
    
    # Add transactions
    # If opening=100000, +50000 credit, -100000 debit = 50000 expected closing
    # But we'll set closing=100000 (wrong), so delta will be -50000
    transactions = [
        {
            'date': '02/01/2025',
            'date_iso': '2025-01-02',
            'description': 'Salary Credit',
            'debit_paise': 0,
            'credit_paise': 50000,
            'balance_paise': 150000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
        {
            'date': '03/01/2025',
            'date_iso': '2025-01-03',
            'description': 'Rent Payment',
            'debit_paise': 100000,
            'credit_paise': 0,
            'balance_paise': 50000,
            'raw_row_json': '{}',
            'row_hash': None,
            'page_number': 1,
        },
    ]
    
    test_db.insert_staged_transactions(import_id, transactions)
    
    return import_id


def test_set_balances_and_remain_needs_review(test_db, missing_balance_import_unbalanced):
    """Test that setting wrong balances keeps import in NEEDS_REVIEW."""
    import_id = missing_balance_import_unbalanced
    
    # Get initial transaction count
    initial_count = test_db.get_transaction_count()
    
    # Set WRONG balances that will result in delta!=0
    # Opening: 100000, Credits: 50000, Debits: 100000, Expected Closing: 50000
    # But we set closing: 100000, so delta = -50000
    updated = test_db.update_statement_import_balances(import_id, 100000, 100000)
    assert updated is True
    
    # Verify balances updated
    import_record = test_db.get_statement_import(import_id)
    assert import_record['opening_balance_paise'] == 100000
    assert import_record['closing_balance_paise'] == 100000
    
    # Revalidate - should NOT commit since delta!=0
    from src.engines.statement_validator import revalidate_staged_statement
    result = revalidate_staged_statement(test_db, import_id)
    
    # Should NOT be valid or committed
    assert result['success'] is False
    assert result['valid'] is False
    assert result['committed'] is False
    assert result['delta_paise'] == -50000  # 50000 - 100000 = -50000
    assert result['inserted'] == 0
    assert result['error'] is not None
    
    # Verify NO transactions were inserted
    new_count = test_db.get_transaction_count()
    assert new_count == initial_count
    
    # Verify import status is still NEEDS_REVIEW
    import_record = test_db.get_statement_import(import_id)
    assert import_record['status'] == 'NEEDS_REVIEW'
    assert import_record['delta_paise'] == -50000


# ============================================================
# Test 13: Set Balances on Non-existent Import
# ============================================================

def test_set_balances_nonexistent_import(test_db):
    """Test that setting balances on non-existent import returns False."""
    result = test_db.update_statement_import_balances(
        "non-existent-id", 
        100000, 
        50000
    )
    assert result is False


# ============================================================
# Test 14: Set Balances Input Validation
# ============================================================

def test_set_balances_request_validation():
    """Test that SetBalancesRequest validates inputs correctly."""
    from src.routers.imports import SetBalancesRequest
    
    # Valid request
    req = SetBalancesRequest(opening_balance_paise=100000, closing_balance_paise=50000)
    assert req.opening_balance_paise == 100000
    assert req.closing_balance_paise == 50000
    
    # Zero is valid
    req = SetBalancesRequest(opening_balance_paise=0, closing_balance_paise=0)
    assert req.opening_balance_paise == 0
    assert req.closing_balance_paise == 0
    
    # Negative values should raise validation error
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        SetBalancesRequest(opening_balance_paise=-1000, closing_balance_paise=50000)
    assert "opening_balance_paise" in str(exc_info.value)
    
    with pytest.raises(ValidationError) as exc_info:
        SetBalancesRequest(opening_balance_paise=100000, closing_balance_paise=-5000)
    assert "closing_balance_paise" in str(exc_info.value)


# ============================================================
# Test 15: Get Statement File - Valid File Returns 200 and PDF
# ============================================================

def test_get_statement_file_valid(test_db, tmp_path, monkeypatch):
    """Test that a valid statement file returns 200 with application/pdf content-type."""
    import_id = "test-import-file-valid"
    
    # Create a test PDF file in the uploads directory
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_upload_dir / "test_statement.pdf"
    test_content = b"%PDF-1.4 test pdf content"
    test_file.write_bytes(test_content)
    
    # Insert statement import with source_path
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test_statement.pdf',
        'source_path': 'uploads/test_statement.pdf',
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': 100000,
        'closing_balance_paise': 50000,
    })
    
    # Test the endpoint using TestClient
    from fastapi.testclient import TestClient
    from src.api import app
    
    # Patch UPLOAD_DIR in the imports module
    import src.routers.imports as imports_module
    monkeypatch.setattr(imports_module, 'UPLOAD_DIR', test_upload_dir)
    
    # Patch get_db to return our test database
    monkeypatch.setattr(imports_module, 'get_db', lambda: test_db)
    
    client = TestClient(app)
    response = client.get(f"/api/statements/{import_id}/file")
    
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'
    assert response.content == test_content


# ============================================================
# Test 16: Get Statement File - Path Traversal Returns 404
# ============================================================

def test_get_statement_file_path_traversal_blocked(test_db, tmp_path):
    """Test that path traversal attempts return 404."""
    import_id = "test-import-file-traversal"
    
    # Create a test uploads directory
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a file outside uploads to try to access
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("secret data")
    
    # Insert statement import with malicious source_path (path traversal attempt)
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'secret.txt',
        'source_path': '../secret.txt',  # Path traversal attempt
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': 100000,
        'closing_balance_paise': 50000,
    })
    
    # Test the endpoint using TestClient
    from fastapi.testclient import TestClient
    from src.api import app
    
    # Temporarily override UPLOAD_DIR for this test
    from src.dependencies import UPLOAD_DIR
    original_upload_dir = UPLOAD_DIR
    
    try:
        # Monkey-patch UPLOAD_DIR for the test
        import src.routers.imports as imports_module
        imports_module.UPLOAD_DIR = test_upload_dir
        
        import src.dependencies as deps
        deps.UPLOAD_DIR = test_upload_dir
        
        client = TestClient(app)
        response = client.get(f"/api/statements/{import_id}/file")
        
        # Should return 404, not the secret file
        assert response.status_code == 404
    finally:
        # Restore original UPLOAD_DIR
        imports_module.UPLOAD_DIR = original_upload_dir
        deps.UPLOAD_DIR = original_upload_dir


# ============================================================
# Test 17: Get Statement File - Non-existent Statement Returns 404
# ============================================================

def test_get_statement_file_nonexistent_statement():
    """Test that requesting a file for non-existent statement returns 404."""
    from fastapi.testclient import TestClient
    from src.api import app
    
    client = TestClient(app)
    response = client.get("/api/statements/non-existent-id/file")
    
    assert response.status_code == 404


# ============================================================
# Test 18: Get Statement File - Missing Source Path Returns 404
# ============================================================

def test_get_statement_file_missing_source_path(test_db):
    """Test that statement with no source_path returns 404."""
    import_id = "test-import-file-no-path"
    
    # Insert statement import with NO source_path
    test_db.insert_statement_import({
        'id': import_id,
        'source_filename': 'test.pdf',
        'source_path': None,  # No source path
        'bank': 'Test Bank',
        'status': 'STAGED',
        'opening_balance_paise': 100000,
        'closing_balance_paise': 50000,
    })
    
    from fastapi.testclient import TestClient
    from src.api import app
    
    client = TestClient(app)
    response = client.get(f"/api/statements/{import_id}/file")
    
    assert response.status_code == 404


# ============================================================
# Test 19: Template Fetch Called Given Fingerprint (Mock Repo)
# ============================================================

def test_template_fetch_called_given_fingerprint(test_db, tmp_path, monkeypatch):
    """Test that template fetch is called when uploading PDF with fingerprint."""
    # Track if template fetch was called
    template_fetch_called = False
    fingerprint_passed = None
    
    def mock_get_template_by_fingerprint(fingerprint):
        nonlocal template_fetch_called, fingerprint_passed
        template_fetch_called = True
        fingerprint_passed = fingerprint
        # Return a template with bbox
        return {
            'id': 'test-template-id-123',
            'fingerprint': fingerprint,
            'bank': 'Test Bank',
            'page_width': 595.0,
            'page_height': 842.0,
            'bbox_norm': [0.1, 0.15, 0.9, 0.25],
            'bbox_norm_json': '[0.1, 0.15, 0.9, 0.25]',
            'created_at': '2025-01-01T00:00:00',
            'last_used_at': None,
            'notes': 'Test template'
        }
    
    # Track if mark_template_used was called
    mark_used_called = False
    template_id_passed = None
    
    def mock_mark_layout_template_used(template_id):
        nonlocal mark_used_called, template_id_passed
        mark_used_called = True
        template_id_passed = template_id
        return True
    
    # Mock bbox extraction to avoid actual PDF processing
    def mock_extract_with_bbox(file_path, bboxes_norm, apply_to_all_pages=True):
        # Return sample extracted rows
        return [
            {
                'date': '01/01/2025',
                'date_iso': '2025-01-01',
                'description': 'Test Transaction',
                'debit_paise': 10000,
                'credit_paise': 0,
                'balance_paise': 90000,
            }
        ]
    
    # Mock fingerprint computation to return predictable 64-char value
    def mock_compute_fingerprint(file_path, bank_hint=None):
        return 'a1b2c3d4e5f6' * 5 + 'a1b2'  # 64 char hex fingerprint
    
    # Mock bank detection
    def mock_detect_bank(file_path, max_pages=3):
        return 'Test Bank'
    
    # Create a proper mock DB class that tracks calls
    class MockDB:
        def __init__(self, real_db):
            self._real_db = real_db
            self.get_layout_template_by_fingerprint = mock_get_template_by_fingerprint
            self.mark_layout_template_used = mock_mark_layout_template_used
            
        def __getattr__(self, name):
            # Delegate all other methods to real test_db
            return getattr(self._real_db, name)
    
    mock_db = MockDB(test_db)
    
    # Import modules and apply mocks BEFORE creating TestClient
    import src.routers.imports as imports_module
    import src.extraction.bbox_extractor as bbox_module
    
    # Mock at the imports module level (where they're imported into)
    monkeypatch.setattr(imports_module, 'get_db', lambda: mock_db)
    monkeypatch.setattr(imports_module, 'compute_fingerprint', mock_compute_fingerprint)
    monkeypatch.setattr(imports_module, 'detect_bank_from_pdf', mock_detect_bank)
    monkeypatch.setattr(imports_module, 'extract_with_bbox', mock_extract_with_bbox)
    
    # Create test upload directory
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(imports_module, 'UPLOAD_DIR', test_upload_dir)
    
    # Create a test PDF file
    test_file = test_upload_dir / "test_statement.pdf"
    test_content = b"%PDF-1.4 test pdf content for template fetch test"
    test_file.write_bytes(test_content)
    
    # Test the endpoint using TestClient
    from fastapi.testclient import TestClient
    from src.api import app
    
    client = TestClient(app)
    
    # Upload PDF
    with open(test_file, 'rb') as f:
        response = client.post(
            "/api/imports/pdf",
            files={"file": ("test_statement.pdf", f, "application/pdf")},
            data={"member": "Self", "auto_commit": "false"}
        )
    
    # Verify template fetch was called
    assert template_fetch_called is True, "Template fetch should be called"
    assert fingerprint_passed is not None, "Fingerprint should be passed to fetch"
    assert len(fingerprint_passed) == 64, f"Fingerprint should be 64 chars, got {len(fingerprint_passed)}"
    
    # Verify mark_template_used was called
    assert mark_used_called is True, "mark_template_used should be called when template is applied"
    assert template_id_passed == 'test-template-id-123', "Correct template ID should be passed"
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data['template_applied'] is True, "template_applied should be true"
    assert data['fingerprint'] == 'a1b2c3d4e5f6' * 5 + 'a1b2', "Fingerprint should be returned"


# ============================================================
# Test 20: No Template Returns template_applied=false
# ============================================================

def test_no_template_returns_template_applied_false(test_db, tmp_path, monkeypatch):
    """Test that when no template matches, template_applied=false is returned."""
    # Mock template fetch to return None (no template found)
    def mock_get_template_by_fingerprint(fingerprint):
        return None
    
    # Mock legacy extractor to avoid actual PDF processing
    def mock_legacy_extract(file_path):
        class MockResult:
            normalized_rows = [
                {
                    'date': '01/01/2025',
                    'date_iso': '2025-01-01',
                    'description': 'Legacy Test Transaction',
                    'debit_paise': 10000,
                    'credit_paise': 0,
                    'balance_paise': 90000,
                }
            ]
            opening_balance = 100000
            closing_balance = 90000
            bank = 'Test Bank'
        return MockResult()
    
    # Mock fingerprint computation
    def mock_compute_fingerprint(file_path, bank_hint=None):
        return 'no_match_fp' * 6 + '1234'  # 64 char hex fingerprint
    
    # Mock bank detection
    def mock_detect_bank(file_path, max_pages=3):
        return 'Test Bank'
    
    # Create mock extractor class
    class MockExtractor:
        name = 'legacy'
        def extract(self, file_path):
            return mock_legacy_extract(file_path)
    
    # Create a proper mock DB class
    class MockDB:
        def __init__(self, real_db):
            self._real_db = real_db
            self.get_layout_template_by_fingerprint = mock_get_template_by_fingerprint
            
        def __getattr__(self, name):
            return getattr(self._real_db, name)
    
    mock_db = MockDB(test_db)
    
    # Import modules and apply mocks BEFORE creating TestClient
    import src.routers.imports as imports_module
    import src.extraction.factory as factory_module
    
    # Mock at the imports module level
    monkeypatch.setattr(imports_module, 'get_db', lambda: mock_db)
    monkeypatch.setattr(imports_module, 'compute_fingerprint', mock_compute_fingerprint)
    monkeypatch.setattr(imports_module, 'detect_bank_from_pdf', mock_detect_bank)
    monkeypatch.setattr(imports_module, 'get_extractor', lambda: MockExtractor())
    
    # Create test upload directory
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(imports_module, 'UPLOAD_DIR', test_upload_dir)
    
    # Create a test PDF file
    test_file = test_upload_dir / "test_statement.pdf"
    test_content = b"%PDF-1.4 test pdf content for no template test"
    test_file.write_bytes(test_content)
    
    # Test the endpoint using TestClient
    from fastapi.testclient import TestClient
    from src.api import app
    
    client = TestClient(app)
    
    # Upload PDF
    with open(test_file, 'rb') as f:
        response = client.post(
            "/api/imports/pdf",
            files={"file": ("test_statement.pdf", f, "application/pdf")},
            data={"member": "Self", "auto_commit": "false"}
        )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data['template_applied'] is False, "template_applied should be false when no template"
    assert data['suggested_bbox_norm'] is None, "suggested_bbox_norm should be null when no template"


# ============================================================
# Test 21: Template with No Bbox Falls Back to Legacy
# ============================================================

def test_template_with_no_bbox_falls_back(test_db, tmp_path, monkeypatch):
    """Test that template without bbox falls back to legacy extraction."""
    # Mock template fetch to return template WITHOUT bbox
    def mock_get_template_by_fingerprint(fingerprint):
        return {
            'id': 'test-template-no-bbox',
            'fingerprint': fingerprint,
            'bank': 'Test Bank',
            'page_width': 595.0,
            'page_height': 842.0,
            'bbox_norm': None,  # No bbox!
            'bbox_norm_json': None,
            'created_at': '2025-01-01T00:00:00',
            'last_used_at': None,
            'notes': 'Template without bbox'
        }
    
    # Mock legacy extractor
    def mock_legacy_extract(file_path):
        class MockResult:
            normalized_rows = [
                {
                    'date': '01/01/2025',
                    'date_iso': '2025-01-01',
                    'description': 'Fallback Transaction',
                    'debit_paise': 10000,
                    'credit_paise': 0,
                    'balance_paise': 90000,
                }
            ]
            opening_balance = 100000
            closing_balance = 90000
            bank = 'Test Bank'
        return MockResult()
    
    # Mock fingerprint computation
    def mock_compute_fingerprint(file_path, bank_hint=None):
        return 'template_no_bbox' * 4  # 64 char hex fingerprint
    
    # Mock bank detection
    def mock_detect_bank(file_path, max_pages=3):
        return 'Test Bank'
    
    # Create mock extractor class
    class MockExtractor:
        name = 'legacy'
        def extract(self, file_path):
            return mock_legacy_extract(file_path)
    
    # Create a proper mock DB class
    class MockDB:
        def __init__(self, real_db):
            self._real_db = real_db
            self.get_layout_template_by_fingerprint = mock_get_template_by_fingerprint
            
        def __getattr__(self, name):
            return getattr(self._real_db, name)
    
    mock_db = MockDB(test_db)
    
    # Import modules and apply mocks BEFORE creating TestClient
    import src.routers.imports as imports_module
    import src.extraction.factory as factory_module
    
    # Mock at the imports module level
    monkeypatch.setattr(imports_module, 'get_db', lambda: mock_db)
    monkeypatch.setattr(imports_module, 'compute_fingerprint', mock_compute_fingerprint)
    monkeypatch.setattr(imports_module, 'detect_bank_from_pdf', mock_detect_bank)
    monkeypatch.setattr(imports_module, 'get_extractor', lambda: MockExtractor())
    
    # Create test upload directory
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(imports_module, 'UPLOAD_DIR', test_upload_dir)
    
    # Create a test PDF file
    test_file = test_upload_dir / "test_statement.pdf"
    test_content = b"%PDF-1.4 test pdf content for template no bbox test"
    test_file.write_bytes(test_content)
    
    # Test the endpoint using TestClient
    from fastapi.testclient import TestClient
    from src.api import app
    
    client = TestClient(app)
    
    # Upload PDF
    with open(test_file, 'rb') as f:
        response = client.post(
            "/api/imports/pdf",
            files={"file": ("test_statement.pdf", f, "application/pdf")},
            data={"member": "Self", "auto_commit": "false"}
        )
    
    # Verify response - template found but no bbox, so falls back to legacy
    assert response.status_code == 200
    data = response.json()
    assert data['template_applied'] is False, "template_applied should be false when template has no bbox"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
