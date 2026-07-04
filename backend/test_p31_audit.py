#!/usr/bin/env python3
"""Test script for P3.1 audit only."""

import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.db.connection import DatabaseConnection
from audits.p31_inventory_audit import P31InventoryAudit
from reports.markdown_reporter import MarkdownReporter

def main():
    """Test P3.1 audit."""
    db_path = "data/finance.db"

    # Create database connection
    db_connection = DatabaseConnection(db_path)

    print(f"🔍 Running P3.1 Financial Inventory Audit...")
    audit = P31InventoryAudit(db_connection)
    result = audit.run()
    reporter = MarkdownReporter()
    reporter.save_to_file(result, "P3_1_FINANCIAL_INVENTORY_AUDIT.md")
    print(f"✅ P3.1 Audit completed: {result.status.value}")

    print("🎉 Test completed successfully!")

if __name__ == "__main__":
    main()