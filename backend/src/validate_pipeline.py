"""
Pipeline Validator
==================
End-to-end validation script that checks the ENTIRE stack:
- Database schema
- API routes
- Engine imports
- Frontend build
- Cross-layer consistency

Usage:
    cd backend && python3 -m src.validate_pipeline

This script does NOT start the server — it only validates.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# Issue Types
# ============================================================

class Severity(Enum):
    ERROR = "ERROR"      # Will break at runtime
    WARNING = "WARNING"  # May cause problems
    INFO = "INFO"        # Suggestion


@dataclass
class Issue:
    severity: Severity
    category: str        # "database", "api", "engine", "frontend", "consistency"
    message: str
    file: str = ""
    line: int = 0
    fix_hint: str = ""


# ============================================================
# Pipeline Validator
# ============================================================

class PipelineValidator:
    """
    Validates the entire ClariFin stack.
    
    Run from backend/ directory:
        python3 -m src.validate_pipeline
    """

    def __init__(self, db_path: str | None = None):
        """Initialize validator with optional custom DB path."""
        self.backend_dir = Path(__file__).parent.parent
        self.frontend_dir = self.backend_dir.parent / "frontend"
        
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = str(self.backend_dir / "data" / "finance.db")
        
        self.issues: List[Issue] = []
        
        # Expected tables and their critical columns
        self.expected_tables = {
            "statements": ["id", "bank", "file_name", "imported_at"],
            "transactions": ["id", "statement_id", "date", "amount", "type", "category", "date_iso", "hash_signature", "account_id"],
            "accounts": ["id", "name", "account_type", "balance_paise", "is_active"],
            "cards": ["id", "card_name", "card_type", "last_four", "is_active"],
            "members": ["id", "name", "color"],
            "reconciliations": ["id", "debit_txn_id", "credit_txn_id", "status", "deterministic_key"],
            # Phase 3: New financial management tables
            "income_sources": ["id", "name", "type", "account_id", "amount_paise", "frequency", "start_date", "end_date", "is_active"],
            "loans": ["id", "name", "lender", "loan_type", "principal_paise", "outstanding_paise", "interest_rate", "emi_paise", "tenure_months", "start_date", "end_date", "linked_account_id", "status"],
            "loan_payments": ["id", "loan_id", "transaction_id", "principal_component_paise", "interest_component_paise", "payment_date", "remaining_principal_paise"],
            "investments": ["id", "name", "type", "platform", "invested_paise", "current_value_paise", "units", "purchase_date", "maturity_date", "linked_account_id", "is_active"],
            "monthly_snapshots": ["id", "month", "total_income_paise", "total_expense_paise", "total_emi_paise", "total_investment_paise", "net_cashflow_paise", "net_worth_paise", "savings_rate", "data_json"],
            "recurring_transactions": ["id", "description", "amount_paise", "type", "category", "frequency", "account_id", "next_due_date", "last_detected_date", "occurrence_count", "is_active", "auto_detected"],
        }
        
        # Engine modules to check
        self.engines = [
            "src.engines.balance_engine",
            "src.engines.behavior_engine",
            "src.engines.reconciliation_engine",
            "src.engines.ledger_audit_engine",
            "src.engines.insight_generator",
            "src.engines.nudge_engine",
            # Phase 3: New engines
            "src.engines.cashflow_engine",
            "src.engines.networth_engine",
            "src.engines.recurring_engine",
            "src.engines.loan_engine",
            "src.engines.snapshot_engine",
            "src.engines.projection_engine",
        ]
        
        # Router files to check
        self.router_files = [
            "src/routers/accounts.py",
            "src/routers/audit.py",
            "src/routers/behavior.py",
            "src/routers/cards.py",
            "src/routers/categories.py",
            "src/routers/dashboard.py",
            "src/routers/income_sources.py",
            "src/routers/investments.py",
            "src/routers/loans.py",
            "src/routers/reconciliation.py",
            "src/routers/recurring.py",
            "src/routers/snapshots.py",
            "src/routers/transactions.py",
            "src/routers/upload.py",
            # Phase 3: New routers
            "src/routers/projections.py",
            "src/routers/export.py",
        ]

    def _check_optional_dependencies(self) -> List[Issue]:
        """Check which optional dependencies are available."""
        issues = []
        optional_deps = {
            "camelot": "camelot-py[cv] — required for PDF table extraction",
            "pdfplumber": "pdfplumber — required for PDF text extraction",
            "ghostscript": "ghostscript — required for camelot PDF processing",
        }
        for module_name, description in optional_deps.items():
            try:
                __import__(module_name)
            except ImportError:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="dependency",
                    message=f"Optional dependency not installed: {description}",
                    fix_hint=f"pip install {module_name}",
                ))
        return issues

    def run_all_checks(self) -> List[Issue]:
        """Run all validation checks and return collected issues."""
        self.issues = []
        
        print("🔍 Running ClariFin Pipeline Validation...\n")
        
        # Check optional dependencies first (as warnings)
        self.issues.extend(self._check_optional_dependencies())
        
        # Run all check groups
        self.issues.extend(self.check_database())
        self.issues.extend(self.check_api_routes())
        self.issues.extend(self.check_engines())
        self.issues.extend(self.check_router_db_methods())
        self.issues.extend(self.check_frontend())
        self.issues.extend(self.check_type_consistency())
        
        return self.issues

    # ============================================================
    # Check Group 1: Database Schema Validation
    # ============================================================

    def check_database(self) -> List[Issue]:
        """Validate database schema and data integrity."""
        issues = []
        category = "database"
        
        print("📊 Checking database schema...")
        
        # Check if database file exists
        if not os.path.exists(self.db_path):
            issues.append(Issue(
                severity=Severity.ERROR,
                category=category,
                message=f"Database file not found: {self.db_path}",
                file=self.db_path,
                fix_hint="Run the application to initialize the database"
            ))
            return issues
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            
            try:
                # Get existing tables
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cur.fetchall()}
                
                # Check for missing tables
                for table in self.expected_tables:
                    if table not in existing_tables:
                        issues.append(Issue(
                            severity=Severity.ERROR,
                            category=category,
                            message=f"Missing table: {table}",
                            file=self.db_path,
                            fix_hint=f"Create table {table} or run database migrations"
                        ))
                
                # Check critical columns for each existing table
                for table, expected_cols in self.expected_tables.items():
                    if table not in existing_tables:
                        continue
                    
                    cur = conn.execute(f"PRAGMA table_info({table})")
                    existing_cols = {row[1] for row in cur.fetchall()}
                    
                    for col in expected_cols:
                        if col not in existing_cols:
                            issues.append(Issue(
                                severity=Severity.WARNING,
                                category=category,
                                message=f"Missing column: {table}.{col}",
                                file=self.db_path,
                                fix_hint=f"Add column {col} to table {table}"
                            ))
                
                # Check for orphaned foreign keys in transactions
                if "transactions" in existing_tables and "statements" in existing_tables:
                    cur = conn.execute("""
                        SELECT COUNT(*) FROM transactions t
                        LEFT JOIN statements s ON t.statement_id = s.id
                        WHERE s.id IS NULL
                    """)
                    orphan_count = cur.fetchone()[0]
                    if orphan_count > 0:
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category=category,
                            message=f"Found {orphan_count} transactions with orphaned statement_id",
                            file=self.db_path,
                            fix_hint="Clean up orphaned transactions or restore missing statements"
                        ))
                
                # Check for NULL values in critical columns
                if "transactions" in existing_tables:
                    cur = conn.execute("SELECT COUNT(*) FROM transactions WHERE date_iso IS NULL")
                    null_date_iso = cur.fetchone()[0]
                    if null_date_iso > 0:
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category=category,
                            message=f"Found {null_date_iso} transactions with NULL date_iso",
                            file=self.db_path,
                            fix_hint="Run date migration to populate date_iso field"
                        ))
                    
                    cur = conn.execute("SELECT COUNT(*) FROM transactions WHERE hash_signature IS NULL")
                    null_hash = cur.fetchone()[0]
                    if null_hash > 0:
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category=category,
                            message=f"Found {null_hash} transactions with NULL hash_signature",
                            file=self.db_path,
                            fix_hint="Run hash migration to populate hash_signature field"
                        ))
                
                # Check for duplicate hash signatures
                if "transactions" in existing_tables:
                    cur = conn.execute("""
                        SELECT hash_signature, COUNT(*) as cnt
                        FROM transactions
                        WHERE hash_signature IS NOT NULL
                        GROUP BY hash_signature
                        HAVING COUNT(*) > 1
                    """)
                    duplicates = cur.fetchall()
                    if duplicates:
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category=category,
                            message=f"Found {len(duplicates)} duplicate hash signatures",
                            file=self.db_path,
                            fix_hint="Review and deduplicate transactions with identical hashes"
                        ))
                
                # Report success if no issues
                if not any(i.category == category for i in issues):
                    issues.append(Issue(
                        severity=Severity.INFO,
                        category=category,
                        message=f"All {len(self.expected_tables)} tables verified successfully",
                        file=self.db_path
                    ))
                
            finally:
                conn.close()
                
        except Exception as e:
            issues.append(Issue(
                severity=Severity.ERROR,
                category=category,
                message=f"Database error: {str(e)}",
                file=self.db_path,
                fix_hint="Check database file permissions and integrity"
            ))
        
        return issues

    # ============================================================
    # Check Group 2: API Route Consistency
    # ============================================================

    def check_api_routes(self) -> List[Issue]:
        """Check frontend API calls match backend routes."""
        issues = []
        category = "api"
        
        print("🔗 Checking API route consistency...")
        
        # Get backend routes
        backend_routes = self._get_backend_routes()
        
        # Get frontend API calls
        frontend_calls = self._get_frontend_api_calls()
        
        # Check for frontend calls without backend routes
        for call in frontend_calls:
            if not self._route_matches(call, backend_routes):
                issues.append(Issue(
                    severity=Severity.ERROR,
                    category=category,
                    message=f"Frontend API call has no matching backend route: {call}",
                    file="frontend/lib/api/client.ts",
                    fix_hint=f"Add backend route for {call} or remove frontend call"
                ))
        
        # Check for backend routes without frontend calls (unused endpoints)
        # Skip health checks and internal routes
        skip_patterns = ['/api/health', '/api/health/detailed']
        for route in backend_routes:
            if route not in skip_patterns and not self._frontend_uses_route(route, frontend_calls):
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category=category,
                    message=f"Backend route has no frontend usage: {route}",
                    file="backend/src/api.py",
                    fix_hint="Remove unused route or add frontend integration"
                ))
        
        # Report success if no issues
        if not any(i.category == category for i in issues):
            issues.append(Issue(
                severity=Severity.INFO,
                category=category,
                message=f"All {len(frontend_calls)} frontend API calls have matching backend routes",
                file="backend/src/api.py"
            ))
        
        return issues

    def _get_backend_routes(self) -> List[str]:
        """Extract all registered API routes from FastAPI app."""
        routes = []
        try:
            # Import the app
            from src.api import app
            
            for route in app.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    # Skip internal routes
                    if route.path not in ['/', '/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc']:
                        routes.append(route.path)
        except Exception as e:
            print(f"  ⚠️ Could not import FastAPI app: {e}")
            print("  ℹ️ Falling back to parsing router files for routes...")
            routes = self._get_backend_routes_from_routers()
        
        return routes

    def _get_backend_routes_from_routers(self) -> List[str]:
        """Extract API routes by parsing router files directly."""
        routes = []
        
        for router_file in self.router_files:
            router_path = self.backend_dir / router_file
            if not router_path.exists():
                continue
            
            content = router_path.read_text()
            
            # Find @router.get/post/put/delete decorators with path
            # Pattern: @router.get("/api/something") or @router.get("/api/something/{id}")
            pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for method, path in matches:
                if path.startswith('/api/'):
                    routes.append(path)
        
        # Also check for health endpoints in api.py
        api_file = self.backend_dir / "src" / "api.py"
        if api_file.exists():
            content = api_file.read_text()
            pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content, re.IGNORECASE)
            for method, path in matches:
                if path.startswith('/api/'):
                    routes.append(path)
        
        return routes

    def _get_frontend_api_calls(self) -> List[str]:
        """Extract API URL patterns from frontend client.ts."""
        calls = []
        client_file = self.frontend_dir / "lib" / "api" / "client.ts"
        
        if not client_file.exists():
            return calls
        
        content = client_file.read_text()
        
        # Find patterns like /api/something, ${API_BASE}/api/something
        patterns = [
            r'`\$\{API_BASE\}(/api/[^`?]+)',  # Template literals with API_BASE
            r'`(/api/[^`?]+)',                # Template literals starting with /api
            r'"(/api/[^"?]+)',                # Double quotes
            r"'(/api/[^'?]+)",                # Single quotes
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Normalize the route (remove trailing slashes, path params)
                route = match.rstrip('/')
                # Replace path params with generic pattern
                route = re.sub(r'/\{[^}]+\}', '/{id}', route)
                route = re.sub(r'/\$\{[^}]+\}', '/{id}', route)
                if route not in calls:
                    calls.append(route)
        
        return calls

    def _route_matches(self, frontend_call: str, backend_routes: List[str]) -> bool:
        """Check if a frontend call matches any backend route."""
        for route in backend_routes:
            # Exact match
            if frontend_call == route:
                return True
            # Handle path params
            frontend_pattern = re.sub(r'/\{[^}]+\}', r'/[^/]+', frontend_call)
            if re.match(f'^{frontend_pattern}$', route):
                return True
        return False

    def _frontend_uses_route(self, route: str, frontend_calls: List[str]) -> bool:
        """Check if any frontend call uses this backend route."""
        for call in frontend_calls:
            if call == route:
                return True
            # Handle path params
            route_pattern = re.sub(r'/\{[^}]+\}', r'/[^/]+', route)
            if re.match(f'^{route_pattern}$', call):
                return True
        return False

    # ============================================================
    # Check Group 3: Engine Health
    # ============================================================

    def check_engines(self) -> List[Issue]:
        """Validate all engine modules can be imported."""
        issues = []
        category = "engine"
        
        print("⚙️ Checking engine health...")
        
        failed_imports = []
        for engine_module in self.engines:
            try:
                module = importlib.import_module(engine_module)
                
                # Check for key functions in the module
                expected_functions = self._get_expected_engine_functions(engine_module)
                for func_name in expected_functions:
                    if not hasattr(module, func_name):
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category=category,
                            message=f"Engine {engine_module} missing expected function: {func_name}",
                            file=f"backend/{engine_module.replace('.', '/')}.py",
                            fix_hint=f"Add {func_name} function to {engine_module}"
                        ))
                
            except ImportError as e:
                failed_imports.append(f"{engine_module}: {str(e)}")
            except Exception as e:
                failed_imports.append(f"{engine_module}: {str(e)}")
        
        if failed_imports:
            for failure in failed_imports:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    category=category,
                    message=f"Failed to import engine: {failure}",
                    file="backend/src/engines/",
                    fix_hint="Check engine module for syntax errors or missing dependencies"
                ))
        
        # Check router imports from engines
        router_engine_issues = self._check_router_engine_imports()
        issues.extend(router_engine_issues)
        
        # Report success if no issues
        if not any(i.category == category for i in issues):
            issues.append(Issue(
                severity=Severity.INFO,
                category=category,
                message=f"All {len(self.engines)} engines loaded successfully",
                file="backend/src/engines/"
            ))
        
        return issues

    def _get_expected_engine_functions(self, engine_module: str) -> List[str]:
        """Get expected key functions for each engine module."""
        expectations = {
            "src.engines.balance_engine": ["compute_running_balance", "compute_account_balance", "validate_statement_balance"],
            "src.engines.behavior_engine": ["compute_behavior_profile"],
            "src.engines.reconciliation_engine": ["find_potential_matches"],
            "src.engines.ledger_audit_engine": ["validate_ledger_integrity", "verify_hash_signatures", "run_full_audit"],
            "src.engines.insight_generator": ["generate_behavioral_insights"],
            "src.engines.nudge_engine": ["generate_nudges"],
            # Phase 3: New engines
            "src.engines.cashflow_engine": ["compute_monthly_cashflow", "compute_cashflow_breakdown", "compute_cashflow_summary"],
            "src.engines.networth_engine": ["compute_net_worth", "compute_net_worth_trend", "compute_asset_allocation"],
            "src.engines.recurring_engine": ["detect_recurring_transactions", "save_detected_recurring"],
            "src.engines.loan_engine": ["compute_emi", "generate_ideal_schedule", "replay_payments", "forecast_from_state", "simulate_prepayment", "compute_loan_summary"],
            "src.engines.snapshot_engine": ["generate_monthly_snapshot", "generate_snapshots_backfill", "snapshot_exists"],
            "src.engines.projection_engine": ["project_net_worth", "project_loan_payoff", "project_goal", "what_if_analysis"],
        }
        return expectations.get(engine_module, [])

    def _check_router_engine_imports(self) -> List[Issue]:
        """Check that routers only import existing engine functions."""
        issues = []
        category = "engine"
        
        for router_file in self.router_files:
            router_path = self.backend_dir / router_file
            if not router_path.exists():
                continue
            
            content = router_path.read_text()
            
            # Find imports from src.engines using AST parsing for accuracy
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('src.engines.'):
                            engine_name = node.module.split('.')[-1]
                            
                            # Determine the correct engine module
                            if engine_name.endswith('_engine'):
                                engine_module = f"src.engines.{engine_name}"
                            elif engine_name in ['insight_generator', 'nudge_engine', 'ledger_audit_engine', 'reconciliation_engine']:
                                engine_module = f"src.engines.{engine_name}"
                            else:
                                engine_module = f"src.engines.{engine_name}_engine"
                            
                            # Get imported names
                            imported_names = []
                            for alias in node.names:
                                name = alias.name
                                # Handle 'as' aliases
                                if alias.asname:
                                    name = alias.name
                                imported_names.append(name)
                            
                            # Verify imports
                            try:
                                module = importlib.import_module(engine_module)
                                for name in imported_names:
                                    if not hasattr(module, name):
                                        issues.append(Issue(
                                            severity=Severity.ERROR,
                                            category=category,
                                            message=f"Router imports non-existent function: {name} from {engine_module}",
                                            file=f"backend/{router_file}",
                                            line=node.lineno,
                                            fix_hint=f"Remove import or add {name} to {engine_module}"
                                        ))
                            except ImportError:
                                issues.append(Issue(
                                    severity=Severity.ERROR,
                                    category=category,
                                    message=f"Router imports from non-existent engine: {engine_module}",
                                    file=f"backend/{router_file}",
                                    line=node.lineno,
                                    fix_hint=f"Create {engine_module} or fix the import"
                                ))
            except SyntaxError:
                # Skip files with syntax errors
                pass
        
        return issues

    # ============================================================
    # Check Group 4: Router-Database Method Consistency
    # ============================================================

    def check_router_db_methods(self) -> List[Issue]:
        """Check that routers only call existing db methods."""
        issues = []
        category = "api"
        
        print("🔄 Checking router-database method consistency...")
        
        # Get FinanceDB methods
        db_methods = self._get_db_methods()
        
        for router_file in self.router_files:
            router_path = self.backend_dir / router_file
            if not router_path.exists():
                continue
            
            content = router_path.read_text()
            
            # Find db.method() calls
            method_calls = re.findall(r'db\.(\w+)\(', content)
            
            for method_name in set(method_calls):
                if method_name not in db_methods:
                    # Find line number
                    for i, line in enumerate(content.split('\n'), 1):
                        if f'db.{method_name}(' in line:
                            issues.append(Issue(
                                severity=Severity.ERROR,
                                category=category,
                                message=f"Router calls non-existent db method: {method_name}()",
                                file=f"backend/{router_file}",
                                line=i,
                                fix_hint=f"Add {method_name} to FinanceDB class or fix the call"
                            ))
                            break
        
        # Report success if no issues
        if not any(i.category == category and i.severity == Severity.ERROR for i in issues):
            issues.append(Issue(
                severity=Severity.INFO,
                category=category,
                message="All router database method calls are valid",
                file="backend/src/routers/"
            ))
        
        return issues

    def _get_db_methods(self) -> Set[str]:
        """Get all public method names from FinanceDB class."""
        methods = set()
        
        try:
            from src.db import FinanceDB
            for name, obj in inspect.getmembers(FinanceDB, predicate=inspect.isfunction):
                if not name.startswith('_'):
                    methods.add(name)
        except Exception as e:
            print(f"Warning: Could not inspect FinanceDB: {e}")
        
        return methods

    # ============================================================
    # Check Group 5: Frontend Build Check
    # ============================================================

    def check_frontend(self) -> List[Issue]:
        """Validate frontend build readiness."""
        issues = []
        category = "frontend"
        
        print("🎨 Checking frontend build...")
        
        # Check node_modules exists
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            issues.append(Issue(
                severity=Severity.WARNING,
                category=category,
                message="node_modules not found - dependencies not installed",
                file="frontend/",
                fix_hint="Run 'npm install' in the frontend directory"
            ))
        
        # Check build output exists (INFO only)
        out_dir = self.frontend_dir / "out"
        next_dir = self.frontend_dir / ".next"
        if not out_dir.exists() and not next_dir.exists():
            issues.append(Issue(
                severity=Severity.INFO,
                category=category,
                message="No build output found - run 'npm run build' to build",
                file="frontend/",
                fix_hint="Run 'npm run build' in the frontend directory"
            ))
        
        # Check tsconfig.json strict mode
        tsconfig = self.frontend_dir / "tsconfig.json"
        if tsconfig.exists():
            try:
                config = json.loads(tsconfig.read_text())
                compiler_options = config.get("compilerOptions", {})
                if not compiler_options.get("strict", False):
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category=category,
                        message="tsconfig.json does not have strict: true",
                        file="frontend/tsconfig.json",
                        fix_hint="Set 'strict: true' in tsconfig.json compilerOptions"
                    ))
            except json.JSONDecodeError:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    category=category,
                    message="tsconfig.json is not valid JSON",
                    file="frontend/tsconfig.json",
                    fix_hint="Fix JSON syntax errors in tsconfig.json"
                ))
        else:
            issues.append(Issue(
                severity=Severity.ERROR,
                category=category,
                message="tsconfig.json not found",
                file="frontend/",
                fix_hint="Create tsconfig.json with proper TypeScript configuration"
            ))
        
        # Run TypeScript compiler check (with timeout)
        if node_modules.exists():
            print("  ⏳ Running TypeScript type check (this may take a moment)...")
            tsc_issues = self._run_tsc_check()
            issues.extend(tsc_issues)
        
        return issues

    def _run_tsc_check(self) -> List[Issue]:
        """Run TypeScript compiler and parse errors."""
        issues = []
        category = "frontend"
        
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                issues.append(Issue(
                    severity=Severity.INFO,
                    category=category,
                    message="TypeScript compilation clean - no type errors",
                    file="frontend/"
                ))
            else:
                # Parse TypeScript errors
                error_pattern = r'(.+?)\((\d+),(\d+)\):\s+error\s+TS\d+:\s+(.+)'
                matches = re.findall(error_pattern, result.stdout)
                
                for match in matches[:20]:  # Limit to first 20 errors
                    file_path, line, col, message = match
                    # Make path relative
                    rel_path = file_path.replace(str(self.frontend_dir), "frontend")
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category=category,
                        message=f"TypeScript error: {message}",
                        file=rel_path,
                        line=int(line),
                        fix_hint="Fix the type error in the source file"
                    ))
                
                # If there are more errors, add a summary
                if len(matches) > 20:
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category=category,
                        message=f"... and {len(matches) - 20} more TypeScript errors",
                        file="frontend/",
                        fix_hint="Fix the above errors first, then re-run validation"
                    ))
                
        except subprocess.TimeoutExpired:
            issues.append(Issue(
                severity=Severity.WARNING,
                category=category,
                message="TypeScript check timed out after 30 seconds",
                file="frontend/",
                fix_hint="Check for circular dependencies or run manually: npx tsc --noEmit"
            ))
        except FileNotFoundError:
            issues.append(Issue(
                severity=Severity.WARNING,
                category=category,
                message="Could not run TypeScript compiler (npx not found)",
                file="frontend/",
                fix_hint="Ensure Node.js and npm are installed"
            ))
        except Exception as e:
            issues.append(Issue(
                severity=Severity.WARNING,
                category=category,
                message=f"TypeScript check failed: {str(e)}",
                file="frontend/",
                fix_hint="Run manually to diagnose: npx tsc --noEmit"
            ))
        
        return issues

    # ============================================================
    # Check Group 6: Cross-Layer Type Consistency
    # ============================================================

    def check_type_consistency(self) -> List[Issue]:
        """Check frontend types match backend Pydantic models."""
        issues = []
        category = "consistency"
        
        print("🔄 Checking cross-layer type consistency...")
        
        # Get TypeScript types
        ts_types = self._extract_typescript_types()
        
        # Get Python Pydantic models
        py_models = self._extract_python_models()
        
        # Compare Transaction type
        if "Transaction" in ts_types and "Transaction" in py_models:
            ts_fields = ts_types["Transaction"]
            py_fields = py_models["Transaction"]
            
            # Check for fields in TS but not in Python (ERROR)
            for field in ts_fields:
                if field not in py_fields:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category=category,
                        message=f"TypeScript Transaction expects field '{field}' not in backend",
                        file="frontend/types/transaction.ts",
                        fix_hint=f"Add '{field}' to backend Transaction model or remove from frontend"
                    ))
            
            # Check for fields in Python but not in TS (WARNING)
            for field in py_fields:
                if field not in ts_fields:
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category=category,
                        message=f"Backend sends field '{field}' not in TypeScript Transaction",
                        file="backend/src/dependencies.py",
                        fix_hint=f"Add '{field}' to frontend Transaction type or remove from backend"
                    ))
        
        # Compare Account type
        if "Account" in ts_types and "Account" in py_models:
            ts_fields = ts_types["Account"]
            py_fields = py_models["Account"]
            
            for field in ts_fields:
                if field not in py_fields:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category=category,
                        message=f"TypeScript Account expects field '{field}' not in backend",
                        file="frontend/lib/api/client.ts",
                        fix_hint=f"Add '{field}' to backend Account model or remove from frontend"
                    ))
            
            for field in py_fields:
                if field not in ts_fields:
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category=category,
                        message=f"Backend sends field '{field}' not in TypeScript Account",
                        file="backend/src/dependencies.py",
                        fix_hint=f"Add '{field}' to frontend Account type or remove from backend"
                    ))
        
        # Report success if no issues
        if not any(i.category == category for i in issues):
            issues.append(Issue(
                severity=Severity.INFO,
                category=category,
                message="Frontend types are consistent with backend models",
                file="frontend/types/"
            ))
        
        return issues

    def _extract_typescript_types(self) -> Dict[str, Set[str]]:
        """Extract interface field names from TypeScript files."""
        types = {}
        
        # Read transaction.ts
        txn_file = self.frontend_dir / "types" / "transaction.ts"
        if txn_file.exists():
            content = txn_file.read_text()
            # Extract Transaction interface
            match = re.search(r'interface\s+Transaction\s*\{([^}]+)\}', content, re.DOTALL)
            if match:
                fields = set()
                for line in match.group(1).split('\n'):
                    # Match field_name?: type or field_name: type
                    field_match = re.search(r'^(\w+)\??\s*:', line.strip())
                    if field_match:
                        fields.add(field_match.group(1))
                types["Transaction"] = fields
        
        # Read api.ts for Account and Card types
        api_file = self.frontend_dir / "lib" / "api" / "client.ts"
        if api_file.exists():
            content = api_file.read_text()
            
            # Extract Account interface
            match = re.search(r'interface\s+Account\s*\{([^}]+)\}', content, re.DOTALL)
            if match:
                fields = set()
                for line in match.group(1).split('\n'):
                    field_match = re.search(r'^(\w+)\??\s*:', line.strip())
                    if field_match:
                        fields.add(field_match.group(1))
                types["Account"] = fields
            
            # Extract Card interface
            match = re.search(r'interface\s+Card\s*\{([^}]+)\}', content, re.DOTALL)
            if match:
                fields = set()
                for line in match.group(1).split('\n'):
                    field_match = re.search(r'^(\w+)\??\s*:', line.strip())
                    if field_match:
                        fields.add(field_match.group(1))
                types["Card"] = fields
        
        return types

    def _extract_python_models(self) -> Dict[str, Set[str]]:
        """Extract field names from Python Pydantic models."""
        models = {}
        
        # We can't easily extract the exact response structure, so we'll
        # infer from the enrich_transaction function and common patterns
        deps_file = self.backend_dir / "src" / "dependencies.py"
        if deps_file.exists():
            content = deps_file.read_text()
            
            # Extract AccountCreate fields
            match = re.search(r'class\s+AccountCreate\s*\([^)]*\):\s*\n((?:\s+\w+:\s*[^\n]+\n)+)', content)
            if match:
                fields = set()
                for line in match.group(1).split('\n'):
                    field_match = re.search(r'^\s+(\w+):', line)
                    if field_match:
                        fields.add(field_match.group(1))
                # Account responses include all AccountCreate fields plus more
                models["Account"] = fields | {"id", "balance_display", "credit_limit_display", "is_active", "created_at", "updated_at"}
        
        # Infer Transaction fields from enrich_transaction function
        # Note: cardId is optional and may be populated conditionally
        models["Transaction"] = {
            "id", "date", "description", "amount", "type", "category", "bank",
            "parsed_date", "date_display", "month_key", "weekday", "amount_display",
            "description_display", "is_large", "sequence_num", "subcategory",
            "raw_description", "member", "statement_file", "statement_period_from",
            "statement_period_to", "debit", "credit", "amount_paise", "cardId"
        }
        
        return models


# ============================================================
# Main Execution
# ============================================================

if __name__ == "__main__":
    validator = PipelineValidator()
    issues = validator.run_all_checks()
    
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]
    
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60 + "\n")
    
    for issue in issues:
        icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[issue.severity.value]
        print(f"{icon} [{issue.category.upper()}] {issue.message}")
        if issue.file:
            if issue.line > 0:
                print(f"   📁 {issue.file}:{issue.line}")
            else:
                print(f"   📁 {issue.file}")
        if issue.fix_hint:
            print(f"   💡 {issue.fix_hint}")
        print()
    
    print("="*60)
    print(f"SUMMARY: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")
    print("="*60)
    
    if errors:
        print("\n🚨 ERRORS MUST BE FIXED BEFORE RUNNING THE APP")
        sys.exit(1)
    else:
        print("\n✅ Pipeline validation passed")
        sys.exit(0)
