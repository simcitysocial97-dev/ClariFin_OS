"""
Tests for Layout Templates Repository
======================================
Unit tests for layout template persistence in SQLite.

These tests use a temporary SQLite database.

Run: python -m pytest tests/test_layout_templates.py -v
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import FinanceDB from the main db module
from db import FinanceDB

# Import layout template repo functions directly from the module
import importlib.util
spec = importlib.util.spec_from_file_location("layout_templates_repo", str(Path(__file__).parent.parent / "src" / "db" / "layout_templates_repo.py"))
layout_templates_repo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout_templates_repo)

# Export the functions we need
init_layout_templates_table = layout_templates_repo.init_layout_templates_table
get_template_by_fingerprint = layout_templates_repo.get_template_by_fingerprint
get_template_by_id = layout_templates_repo.get_template_by_id
upsert_template = layout_templates_repo.upsert_template
mark_template_used = layout_templates_repo.mark_template_used
list_templates = layout_templates_repo.list_templates
delete_template = layout_templates_repo.delete_template


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
def sample_template_data():
    """Sample template data for testing."""
    return {
        'fingerprint': 'a1b2c3d4e5f6' * 8,  # 64 char hex string
        'bank': 'HDFC Bank',
        'page_width': 595.0,
        'page_height': 842.0,
        'bbox_norm': [0.1, 0.15, 0.9, 0.25],
        'notes': 'Test template for HDFC statements'
    }


# ============================================================
# Test 1: Template Insert and Fetch by Fingerprint
# ============================================================

def test_upsert_new_template(test_db, sample_template_data):
    """Test inserting a new template."""
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank=sample_template_data['bank'],
            page_width=sample_template_data['page_width'],
            page_height=sample_template_data['page_height'],
            bbox_norm=sample_template_data['bbox_norm'],
            notes=sample_template_data['notes']
        )
    
    # Should return a valid UUID
    assert template_id is not None
    assert len(template_id) == 36  # UUID length


def test_fetch_template_by_fingerprint(test_db, sample_template_data):
    """Test fetching a template by fingerprint."""
    # Insert template
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank=sample_template_data['bank'],
            page_width=sample_template_data['page_width'],
            page_height=sample_template_data['page_height'],
            bbox_norm=sample_template_data['bbox_norm'],
            notes=sample_template_data['notes']
        )
    
    # Fetch by fingerprint
    with test_db.connection() as conn:
        template = get_template_by_fingerprint(conn, sample_template_data['fingerprint'])
    
    assert template is not None
    assert template['id'] == template_id
    assert template['fingerprint'] == sample_template_data['fingerprint']
    assert template['bank'] == sample_template_data['bank']
    assert template['page_width'] == sample_template_data['page_width']
    assert template['page_height'] == sample_template_data['page_height']
    assert template['bbox_norm'] == sample_template_data['bbox_norm']
    assert template['notes'] == sample_template_data['notes']
    assert template['created_at'] is not None


def test_fetch_nonexistent_template(test_db):
    """Test fetching a template that doesn't exist."""
    with test_db.connection() as conn:
        template = get_template_by_fingerprint(conn, 'nonexistent_fingerprint')
    
    assert template is None


# ============================================================
# Test 2: Template Update (Upsert Behavior)
# ============================================================

def test_upsert_updates_existing_template(test_db, sample_template_data):
    """Test that upsert updates an existing template."""
    # Insert initial template
    with test_db.transaction() as conn:
        template_id_1 = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank=sample_template_data['bank'],
            page_width=sample_template_data['page_width'],
            page_height=sample_template_data['page_height'],
            bbox_norm=sample_template_data['bbox_norm'],
            notes='Original notes'
        )
    
    # Upsert with same fingerprint but different data
    with test_db.transaction() as conn:
        template_id_2 = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank='Axis Bank',  # Changed bank
            page_width=612.0,  # Changed dimensions
            page_height=792.0,
            bbox_norm=[0.05, 0.1, 0.95, 0.2],
            notes='Updated notes'
        )
    
    # Should return the same ID
    assert template_id_1 == template_id_2
    
    # Fetch and verify updates
    with test_db.connection() as conn:
        template = get_template_by_fingerprint(conn, sample_template_data['fingerprint'])
    
    assert template['bank'] == 'Axis Bank'
    assert template['page_width'] == 612.0
    assert template['page_height'] == 792.0
    assert template['bbox_norm'] == [0.05, 0.1, 0.95, 0.2]
    assert template['notes'] == 'Updated notes'


# ============================================================
# Test 3: Mark Template Used
# ============================================================

def test_mark_template_used(test_db, sample_template_data):
    """Test updating last_used_at timestamp."""
    # Insert template
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank=sample_template_data['bank'],
            page_width=sample_template_data['page_width'],
            page_height=sample_template_data['page_height']
        )
    
    # Initially last_used_at should be None
    with test_db.connection() as conn:
        template = get_template_by_id(conn, template_id)
    assert template['last_used_at'] is None
    
    # Mark as used
    with test_db.transaction() as conn:
        result = mark_template_used(conn, template_id)
    
    assert result is True
    
    # Verify timestamp was updated
    with test_db.connection() as conn:
        template = get_template_by_id(conn, template_id)
    assert template['last_used_at'] is not None


def test_mark_nonexistent_template_used(test_db):
    """Test marking a non-existent template as used."""
    with test_db.transaction() as conn:
        result = mark_template_used(conn, 'nonexistent-id')
    
    assert result is False


# ============================================================
# Test 4: List Templates
# ============================================================

def test_list_templates_empty(test_db):
    """Test listing templates when none exist."""
    with test_db.connection() as conn:
        templates = list_templates(conn)
    
    assert templates == []


def test_list_templates_multiple(test_db):
    """Test listing multiple templates."""
    # Insert multiple templates
    with test_db.transaction() as conn:
        upsert_template(conn, 'fp1' * 16, 'HDFC Bank', 595.0, 842.0)
        upsert_template(conn, 'fp2' * 16, 'Axis Bank', 612.0, 792.0)
        upsert_template(conn, 'fp3' * 16, 'HDFC Bank', 595.0, 842.0)
    
    # List all templates
    with test_db.connection() as conn:
        templates = list_templates(conn)
    
    assert len(templates) == 3


def test_list_templates_by_bank(test_db):
    """Test listing templates filtered by bank."""
    # Insert multiple templates
    with test_db.transaction() as conn:
        upsert_template(conn, 'fp1' * 16, 'HDFC Bank', 595.0, 842.0)
        upsert_template(conn, 'fp2' * 16, 'Axis Bank', 612.0, 792.0)
        upsert_template(conn, 'fp3' * 16, 'HDFC Bank', 595.0, 842.0)
    
    # List only HDFC templates
    with test_db.connection() as conn:
        templates = list_templates(conn, bank='HDFC Bank')
    
    assert len(templates) == 2
    for template in templates:
        assert template['bank'] == 'HDFC Bank'


def test_list_templates_pagination(test_db):
    """Test template listing with pagination."""
    # Insert multiple templates
    with test_db.transaction() as conn:
        for i in range(10):
            upsert_template(conn, f'fp{i}' * 16, f'Bank {i}', 595.0, 842.0)
    
    # List with limit
    with test_db.connection() as conn:
        templates = list_templates(conn, limit=5)
    
    assert len(templates) == 5


# ============================================================
# Test 5: Delete Template
# ============================================================

def test_delete_template(test_db, sample_template_data):
    """Test deleting a template."""
    # Insert template
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank=sample_template_data['bank'],
            page_width=sample_template_data['page_width'],
            page_height=sample_template_data['page_height']
        )
    
    # Verify it exists
    with test_db.connection() as conn:
        template = get_template_by_id(conn, template_id)
    assert template is not None
    
    # Delete it
    with test_db.transaction() as conn:
        result = delete_template(conn, template_id)
    
    assert result is True
    
    # Verify it's gone
    with test_db.connection() as conn:
        template = get_template_by_id(conn, template_id)
    assert template is None


def test_delete_nonexistent_template(test_db):
    """Test deleting a non-existent template."""
    with test_db.transaction() as conn:
        result = delete_template(conn, 'nonexistent-id')
    
    assert result is False


# ============================================================
# Test 6: Template with Optional Fields
# ============================================================

def test_template_without_bbox(test_db):
    """Test creating a template without bbox_norm."""
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint='fp_no_bbox' * 8,
            bank='Test Bank',
            page_width=595.0,
            page_height=842.0,
            bbox_norm=None,
            notes=None
        )
    
    with test_db.connection() as conn:
        template = get_template_by_id(conn, template_id)
    
    assert template is not None
    assert template['bbox_norm'] is None
    assert template['bbox_norm_json'] is None
    assert template['notes'] is None


def test_template_bbox_json_parsing(test_db):
    """Test that bbox_norm JSON is correctly parsed."""
    bbox = [0.1, 0.15, 0.9, 0.25]
    
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint='fp_bbox_test' * 6,
            bank='Test Bank',
            page_width=595.0,
            page_height=842.0,
            bbox_norm=bbox
        )
    
    with test_db.connection() as conn:
        template = get_template_by_id(conn, template_id)
    
    assert template['bbox_norm'] == bbox


# ============================================================
# Test 7: FinanceDB Glue Methods
# ============================================================

def test_financedb_get_layout_template_by_fingerprint(test_db, sample_template_data):
    """Test FinanceDB wrapper for get_template_by_fingerprint."""
    # Insert via repo
    with test_db.transaction() as conn:
        template_id = upsert_template(
            conn,
            fingerprint=sample_template_data['fingerprint'],
            bank=sample_template_data['bank'],
            page_width=sample_template_data['page_width'],
            page_height=sample_template_data['page_height']
        )
    
    # Fetch via FinanceDB method
    template = test_db.get_layout_template_by_fingerprint(sample_template_data['fingerprint'])
    
    assert template is not None
    assert template['id'] == template_id


def test_financedb_upsert_layout_template(test_db):
    """Test FinanceDB wrapper for upsert_template."""
    template_id = test_db.upsert_layout_template(
        fingerprint='test_fp' * 16,
        bank='Test Bank',
        page_width=595.0,
        page_height=842.0,
        bbox_norm=[0.1, 0.2, 0.9, 0.8],
        notes='Test notes'
    )
    
    assert template_id is not None
    
    # Verify it was created
    template = test_db.get_layout_template_by_id(template_id)
    assert template['bank'] == 'Test Bank'


def test_financedb_mark_layout_template_used(test_db, sample_template_data):
    """Test FinanceDB wrapper for mark_template_used."""
    # Create template
    template_id = test_db.upsert_layout_template(
        fingerprint=sample_template_data['fingerprint'],
        bank=sample_template_data['bank'],
        page_width=sample_template_data['page_width'],
        page_height=sample_template_data['page_height']
    )
    
    # Mark as used
    result = test_db.mark_layout_template_used(template_id)
    assert result is True
    
    # Verify
    template = test_db.get_layout_template_by_id(template_id)
    assert template['last_used_at'] is not None


def test_financedb_list_layout_templates(test_db):
    """Test FinanceDB wrapper for list_templates."""
    # Create templates
    test_db.upsert_layout_template('fp1' * 16, 'HDFC Bank', 595.0, 842.0)
    test_db.upsert_layout_template('fp2' * 16, 'Axis Bank', 612.0, 792.0)
    
    # List all
    templates = test_db.list_layout_templates()
    assert len(templates) == 2
    
    # List filtered
    hdfc_templates = test_db.list_layout_templates(bank='HDFC Bank')
    assert len(hdfc_templates) == 1


def test_financedb_delete_layout_template(test_db):
    """Test FinanceDB wrapper for delete_template."""
    # Create template
    template_id = test_db.upsert_layout_template(
        fingerprint='delete_test' * 6,
        bank='Test Bank',
        page_width=595.0,
        page_height=842.0
    )
    
    # Delete
    result = test_db.delete_layout_template(template_id)
    assert result is True
    
    # Verify deleted
    template = test_db.get_layout_template_by_id(template_id)
    assert template is None


# ============================================================
# Test 8: Fingerprint Uniqueness
# ============================================================

def test_fingerprint_uniqueness_constraint(test_db, sample_template_data):
    """Test that fingerprint must be unique."""
    # Insert first template
    test_db.upsert_layout_template(
        fingerprint=sample_template_data['fingerprint'],
        bank='HDFC Bank',
        page_width=595.0,
        page_height=842.0
    )
    
    # Insert with same fingerprint should update, not error
    template_id = test_db.upsert_layout_template(
        fingerprint=sample_template_data['fingerprint'],
        bank='Updated Bank',
        page_width=595.0,
        page_height=842.0
    )
    
    # Should have updated the existing template
    template = test_db.get_layout_template_by_id(template_id)
    assert template['bank'] == 'Updated Bank'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
