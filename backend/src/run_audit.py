#!/usr/bin/env python3
"""Main script to run audits using the refactored system."""

import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.db.connection import DatabaseConnection
from audits.p31_inventory_audit import P31InventoryAudit
from audits.p32_classification_audit import P32ClassificationAudit
from audits.p33_truth_validation import P33TruthValidationAudit
from reports.markdown_reporter import MarkdownReporter

def main():
    """Main entry point for running audits."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_audit.py --audit [p3.1|p3.2|p3.3|all] [--db db_path]")
        sys.exit(1)

    # Parse arguments
    audit_type = None
    db_path = "backend/data/finance.db"

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--audit":
            i += 1
            audit_type = sys.argv[i]
        elif sys.argv[i] == "--db":
            i += 1
            db_path = sys.argv[i]
        i += 1

    if not audit_type:
        print("Error: --audit parameter is required")
        sys.exit(1)

    # Create database connection
    db_connection = DatabaseConnection(db_path)

    # Run selected audits
    if audit_type == "all" or audit_type == "p3.1":
        print(f"🔍 Running P3.1 Financial Inventory Audit...")
        audit = P31InventoryAudit(db_connection)
        result = audit.run()
        reporter = MarkdownReporter()
        reporter.save_to_file(result, "P3_1_FINANCIAL_INVENTORY_AUDIT.md")
        print(f"✅ P3.1 Audit completed: {result.status.value}")

    if audit_type == "all" or audit_type == "p3.2":
        print(f"🔍 Running P3.2 Transaction Classification Audit...")
        audit = P32ClassificationAudit(db_connection)
        result = audit.run()
        reporter = MarkdownReporter()
        reporter.save_to_file(result, "P3_2_TRANSACTION_CLASSIFICATION_AUDIT.md")
        print(f"✅ P3.2 Audit completed: {result.status.value}")

    if audit_type == "all" or audit_type == "p3.3":
        print(f"🔍 Running P3.3 Financial Truth Validation...")
        audit = P33TruthValidationAudit(db_connection)
        result = audit.run()
        reporter = MarkdownReporter()
        reporter.save_to_file(result, "P3_3_FINANCIAL_TRUTH_VALIDATION.md")
        print(f"✅ P3.3 Audit completed: {result.status.value}")

    print("🎉 All requested audits completed successfully!")

if __name__ == "__main__":
    main()