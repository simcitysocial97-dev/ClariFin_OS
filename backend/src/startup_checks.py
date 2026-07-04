"""
Startup Validator
=================
Validates the entire backend is healthy BEFORE accepting any HTTP requests.

Usage:
    from src.startup_checks import StartupValidator
    validator = StartupValidator(db_path, upload_dir)
    validator.run_all_checks()  # Raises RuntimeError on failure
"""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from src.logger import log


class StartupValidator:
    """
    Validates backend health at startup.
    
    Runs checks in order and collects results. If any check has status "fail",
    the startup should log all results and raise a RuntimeError so the server
    refuses to start with broken state.
    """

    def __init__(self, db_path: str, upload_dir: Path, data_dir: Path | None = None):
        """
        Initialize the startup validator.
        
        Args:
            db_path: Path to the SQLite database file
            upload_dir: Path to the upload directory
            data_dir: Path to the data directory (defaults to parent of upload_dir)
        """
        self.db_path = db_path
        self.upload_dir = upload_dir
        self.data_dir = data_dir or upload_dir.parent
        self.results: list[dict[str, Any]] = []

    def run_all_checks(self) -> None:
        """
        Execute all startup checks in order.
        
        Raises:
            RuntimeError: If any check fails (status="fail")
        """
        self.results = []
        
        # Run all checks
        self.results.append(self._check_database_connectivity())
        self.results.append(self._check_schema_integrity())
        self.results.append(self._check_engine_imports())
        self.results.append(self._check_router_imports())
        self.results.append(self._check_upload_directory())
        self.results.append(self._check_data_directory())
        
        # Count results
        pass_count = sum(1 for r in self.results if r["status"] == "pass")
        warn_count = sum(1 for r in self.results if r["status"] == "warn")
        fail_count = sum(1 for r in self.results if r["status"] == "fail")
        
        log.info(
            "Startup checks: %d passed, %d warnings, %d failed",
            pass_count, warn_count, fail_count
        )
        
        # Handle failures
        if fail_count > 0:
            for result in self.results:
                if result["status"] == "fail":
                    log.error(
                        "Startup check failed [%s]: %s",
                        result["check"],
                        result["detail"]
                    )
            raise RuntimeError("Startup checks failed — see logs above")
        
        # Handle warnings
        if warn_count > 0:
            for result in self.results:
                if result["status"] == "warn":
                    log.warning(
                        "Startup check warning [%s]: %s",
                        result["check"],
                        result["detail"]
                    )

    def _check_database_connectivity(self) -> dict[str, Any]:
        """
        Check 1: Database connectivity
        
        Attempt to connect to the database at DB_PATH and execute SELECT 1.
        """
        check_name = "database_connectivity"
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            try:
                cur = conn.execute("SELECT 1")
                cur.fetchone()
                return {
                    "check": check_name,
                    "status": "pass",
                    "detail": f"Connected to {self.db_path}"
                }
            finally:
                conn.close()
        except Exception as e:
            return {
                "check": check_name,
                "status": "fail",
                "detail": f"Failed to connect to database: {str(e)}"
            }

    def _check_schema_integrity(self) -> dict[str, Any]:
        """
        Check 2: Schema integrity
        
        Verify required tables exist and have critical columns.
        """
        check_name = "schema_integrity"
        
        required_tables = {
            "statements": ["id", "bank", "file_name"],
            "transactions": ["id", "statement_id", "date_iso", "debit", "credit", 
                           "hash_signature", "account_id", "category"],
            "accounts": ["id", "name", "account_type", "balance_paise"],
            "cards": ["id", "card_name", "card_type", "last_four"],
            "members": ["id", "name", "color"],
            "reconciliations": ["id", "debit_txn_id", "credit_txn_id", 
                               "status", "deterministic_key"],
        }
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            try:
                # Get all table names from sqlite_master
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                existing_tables = {row[0] for row in cur.fetchall()}
                
                # Check for missing tables
                missing_tables = [
                    table for table in required_tables
                    if table not in existing_tables
                ]
                
                if missing_tables:
                    return {
                        "check": check_name,
                        "status": "fail",
                        "detail": f"Missing tables: {', '.join(missing_tables)}"
                    }
                
                # Check critical columns for each table
                missing_columns = []
                for table, columns in required_tables.items():
                    cur = conn.execute(f"PRAGMA table_info({table})")
                    existing_columns = {row[1] for row in cur.fetchall()}
                    
                    for col in columns:
                        if col not in existing_columns:
                            missing_columns.append(f"{table}.{col}")
                
                if missing_columns:
                    return {
                        "check": check_name,
                        "status": "warn",
                        "detail": f"Missing columns (migrations may add): {', '.join(missing_columns)}"
                    }
                
                return {
                    "check": check_name,
                    "status": "pass",
                    "detail": f"All {len(required_tables)} tables and critical columns verified"
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            return {
                "check": check_name,
                "status": "fail",
                "detail": f"Failed to verify schema: {str(e)}"
            }

    def _check_engine_imports(self) -> dict[str, Any]:
        """
        Check 3: Engine imports
        
        Attempt to import each engine module.
        """
        check_name = "engine_imports"
        
        engines = [
            "src.engines.balance_engine",
            "src.engines.behavior_engine",
            "src.engines.reconciliation_engine",
            "src.engines.ledger_audit_engine",
            "src.engines.insight_generator",
            "src.engines.nudge_engine",
        ]
        
        failed_imports = []
        
        for engine in engines:
            try:
                __import__(engine)
            except ImportError as e:
                failed_imports.append(f"{engine}: {str(e)}")
        
        if failed_imports:
            return {
                "check": check_name,
                "status": "fail",
                "detail": f"Failed imports: {'; '.join(failed_imports)}"
            }
        
        return {
            "check": check_name,
            "status": "pass",
            "detail": f"All {len(engines)} engines loaded successfully"
        }

    def _check_router_imports(self) -> dict[str, Any]:
        """
        Check 4: Router imports
        
        Attempt to import each router module.
        """
        check_name = "router_imports"
        
        routers = [
            "src.routers.dashboard",
            "src.routers.transactions",
            "src.routers.upload",
            "src.routers.accounts",
            "src.routers.categories",
            "src.routers.reconciliation",
            "src.routers.behavior",
            "src.routers.audit",
        ]
        
        failed_imports = []
        
        for router in routers:
            try:
                __import__(router)
            except ImportError as e:
                failed_imports.append(f"{router}: {str(e)}")
        
        if failed_imports:
            return {
                "check": check_name,
                "status": "fail",
                "detail": f"Failed imports: {'; '.join(failed_imports)}"
            }
        
        return {
            "check": check_name,
            "status": "pass",
            "detail": f"All {len(routers)} routers loaded successfully"
        }

    def _check_upload_directory(self) -> dict[str, Any]:
        """
        Check 5: Upload directory
        
        Verify UPLOAD_DIR exists and is writable.
        """
        check_name = "upload_directory"
        
        try:
            # Check if directory exists
            if not self.upload_dir.exists():
                return {
                    "check": check_name,
                    "status": "warn",
                    "detail": f"Upload directory does not exist: {self.upload_dir}"
                }
            
            # Check if it's actually a directory
            if not self.upload_dir.is_dir():
                return {
                    "check": check_name,
                    "status": "fail",
                    "detail": f"Upload path is not a directory: {self.upload_dir}"
                }
            
            # Test write permissions by creating a temp file
            try:
                test_file = self.upload_dir / f".startup_test_{os.getpid()}.tmp"
                test_file.write_text("test")
                test_file.unlink()
            except (OSError, PermissionError) as e:
                return {
                    "check": check_name,
                    "status": "warn",
                    "detail": f"Upload directory not writable: {str(e)}"
                }
            
            return {
                "check": check_name,
                "status": "pass",
                "detail": f"Upload directory ready: {self.upload_dir}"
            }
            
        except Exception as e:
            return {
                "check": check_name,
                "status": "warn",
                "detail": f"Upload directory check failed: {str(e)}"
            }

    def _check_data_directory(self) -> dict[str, Any]:
        """
        Check 6: Data directory permissions
        
        Verify backend/data/ and backend/data/logs/ exist.
        """
        check_name = "data_directory"
        
        logs_dir = self.data_dir / "logs"
        
        issues = []
        
        if not self.data_dir.exists():
            issues.append(f"Data directory missing: {self.data_dir}")
        
        if not logs_dir.exists():
            issues.append(f"Logs directory missing: {logs_dir}")
        
        if issues:
            return {
                "check": check_name,
                "status": "warn",
                "detail": "; ".join(issues)
            }
        
        return {
            "check": check_name,
            "status": "pass",
            "detail": f"Data directory structure verified: {self.data_dir}"
        }
