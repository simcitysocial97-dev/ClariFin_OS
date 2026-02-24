import reflex as rx
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from .services import FinanceDB, get_db_path, StatementExtractor, categorize, MetadataExtractor
from .utils import parse_date, format_inr, format_date_display, clean_description

_DB_PATH = get_db_path()

# Import CSVImporter
import sys
from pathlib import Path
_SRC_DIR = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
from csv_importer import CSVImporter


class FinanceState(rx.State):
    # ---- Raw data ----
    _all_transactions: list[dict] = []
    _all_statements: list[dict] = []

    # ---- Filters ----
    search_query: str = ""
    selected_bank: str = "All"
    selected_category: str = "All"
    selected_type: str = "All"
    date_range_start: str = ""
    date_range_end: str = ""
    min_amount_str: str = ""
    max_amount_str: str = ""

    # ---- UI state ----
    is_loading: bool = False
    selected_category_drill: str = ""
    bulk_category_input: str = ""

    # ---- KPI cards ----
    total_spend: str = "₹0"
    total_spend_raw: float = 0.0
    this_month_spend: str = "₹0"
    last_month_spend: str = "₹0"
    month_change: str = "—"
    latest_month_label: str = ""
    transaction_count: int = 0
    card_count: int = 0
    bank_count: int = 0
    # Display strings for UI
    card_count_display: str = ""
    bank_count_display: str = ""
    transaction_count_display: str = ""

    # ---- Error / status ----
    error_message: str = ""

    # ---- Tables / charts ----
    filtered_transactions: list[dict] = []
    monthly_chart_data: list[dict] = []
    category_chart_data: list[dict] = []
    bank_chart_data: list[dict] = []
    category_monthly_data: list[dict] = []
    top_merchants: list[dict] = []
    day_of_week_data: list[dict] = []
    recent_transactions: list[dict] = []
    statements_list: list[dict] = []
    statements_with_metadata: list[dict] = []
    uncategorized_patterns: list[dict] = []
    recurring_charges: list[dict] = []
    largest_transactions: list[dict] = []
    category_summary: list[dict] = []
    category_drill_transactions: list[dict] = []
    spending_trend: list[dict] = []

    # ---- Upload state ----
    upload_status: list[str] = []
    upload_processing: bool = False
    upload_error: str = ""

    # ---- Delete confirmation ----
    delete_confirm_id: int = 0
    delete_confirm_bank: str = ""
    delete_confirm_show: bool = False

    # ---- Analytics KPIs ----
    avg_monthly_spend: float = 0.0
    avg_monthly_display: str = "₹0"
    highest_month: str = ""
    highest_month_amount: str = "₹0"
    biggest_txn_desc: str = ""
    biggest_txn_amount: str = "₹0"
    biggest_txn_date: str = ""
    biggest_txn_bank: str = ""
    unique_merchants: int = 0
    unique_merchants_display: str = "0"

    # ---- Filter options ----
    available_banks: list[str] = ["All"]
    available_categories: list[str] = ["All"]
    
    # ---- Display transactions (limited for UI) ----
    display_transactions: list[dict] = []
    total_filtered_count: int = 0
    
    # ---- Exclude Transfers Toggle ----
    exclude_transfers: bool = True  # Default ON - exclude transfers from analytics
    analytics_count: int = 0
    analytics_count_display: str = ""
    
    # ---- Contextual KPI displays ----
    above_avg_display: str = ""
    above_avg_positive: bool = False  # True if spending MORE than average (bad for expenses)
    above_avg_color: str = "var(--gray-9)"  # Pre-computed color for subtitle
    total_months_display: str = ""
    avg_txn_display: str = ""
    
    # ---- Behavioral Insights ----
    behavioral_insights: list[dict] = []
    
    # ---- Import flow state ----
    import_step: int = 1
    import_file_name: str = ""
    import_detected: dict = {}
    import_columns: list[str] = []
    import_preview: list[dict] = []
    import_mapping: dict = {}
    import_result: dict = {}
    import_processing: bool = False
    import_transactions_cache: list[dict] = []  # Cache for full import
    
    # ---- Member support ----
    available_members: list[str] = ["All", "Self"]
    selected_member: str = "All"
    show_add_member_dialog: bool = False
    new_member_name: str = ""
    new_member_color: str = "#6366F1"
    
    # Preset colors for new members
    MEMBER_COLORS = ["#6366F1", "#EC4899", "#22C55E", "#F59E0B", "#8B5CF6", "#06B6D4", "#EF4444", "#14B8A6"]

    def _get_db(self) -> FinanceDB:
        return FinanceDB(db_path=_DB_PATH)

    # ============ DATA LOADING ============

    def load_all_data(self):
        self.error_message = ""
        self.is_loading = True
        # Reset computed lists to force re-render
        self.filtered_transactions = []
        self.monthly_chart_data = []
        self.category_chart_data = []
        self.bank_chart_data = []
        self.recent_transactions = []
        self.statements_with_metadata = []

        try:
            db = self._get_db()
            
            # Load members from database
            members = db.get_members()
            self.available_members = ["All"] + [m.get("name", "Self") for m in members]
            
            # Get transactions with member filter
            filters = {}
            if self.selected_member != "All":
                filters["member"] = self.selected_member
            
            raw = db.get_all_transactions_with_bank(filters)
            self._all_statements = db.get_all_statements()
            raw_uncategorized = db.get_uncategorized_patterns(limit=30)
            # Pre-format uncategorized patterns for reactive rendering
            self.uncategorized_patterns = [
                {
                    "description": p.get("description", ""),
                    "count": p.get("count", 0),
                    "total_amount": p.get("total_amount", 0),
                    "total_display": format_inr(p.get("total_amount", 0)),
                }
                for p in raw_uncategorized
            ]

            # Load statements with metadata for Cards page
            try:
                raw_statements = db.get_all_statements_with_metadata()
            except Exception:
                raw_statements = self._all_statements
            
            # Pre-format ALL display values for reactive rendering (no Python ops needed in UI)
            formatted_statements = []
            for stmt in raw_statements:
                total_debit = float(stmt.get("total_debit") or 0)
                total_credit = float(stmt.get("total_credit") or 0)
                total_due = float(stmt.get("total_amount_due") or 0)
                min_due = float(stmt.get("minimum_amount_due") or 0)
                diff = float(stmt.get("validation_difference") or 0)
                extracted_net = total_debit - total_credit
                
                # Pre-compute display strings
                total_debit_display = format_inr(total_debit) if total_debit else "₹0"
                total_credit_display = format_inr(total_credit) if total_credit else "₹0"
                total_due_display = format_inr(total_due) if total_due else "—"
                extracted_net_display = format_inr(extracted_net) if extracted_net else "₹0"
                min_due_display = format_inr(min_due) if min_due else ""
                diff_display = f"₹{diff:,.0f}" if diff else ""
                
                # Pre-compute boolean flags
                has_card = bool(stmt.get("card_last4"))
                has_period = bool(stmt.get("statement_period_from"))
                has_metadata = bool(total_due and total_due > 0)
                has_due_date = bool(stmt.get("payment_due_date"))
                has_min_due = bool(min_due and min_due > 0)
                has_difference = bool(diff and diff > 0)
                
                # Pre-compute card display
                card_last4 = stmt.get("card_last4") or ""
                card_display = f"****{card_last4}" if card_last4 else ""
                
                # Pre-compute period display
                period_from = stmt.get("statement_period_from") or ""
                period_to = stmt.get("statement_period_to") or ""
                period_display = f"{period_from} – {period_to}" if period_from else ""
                
                # Pre-compute validation badge text and color
                validation_status = stmt.get("validation_status") or "pending"
                badge_text = (
                    "✅ Exact Match" if validation_status == "exact_match"
                    else f"⚠️ Close (₹{diff:,.0f} off)" if validation_status == "close_match"
                    else f"❌ Mismatch (₹{diff:,.0f})" if validation_status == "mismatch"
                    else "— No Data" if validation_status == "no_metadata"
                    else "⏳ Pending"
                )
                badge_color = (
                    "green" if validation_status == "exact_match"
                    else "amber" if validation_status == "close_match"
                    else "red" if validation_status == "mismatch"
                    else "gray"
                )
                
                # Pre-compute bank accent color
                bank = stmt.get("bank", "Unknown")
                bank_color = {
                    "HDFC Bank": "#004B8D",
                    "ICICI Bank": "#F37920",
                    "Axis Bank": "#97144D",
                    "SBI Card": "#1A5DAB",
                    "IDFC First Bank": "#9C1D26",
                    "IndusInd Bank": "#8B0000",
                }.get(bank, "#6366F1")
                
                # Pre-compute border style for the card
                border_style = f"3px solid {bank_color}"
                
                formatted_statements.append({
                    "id": stmt.get("id", 0),
                    "bank": bank,
                    "bank_color": bank_color,
                    "border_style": border_style,
                    "file_name": stmt.get("file_name", ""),
                    "card_last4": card_last4,
                    "card_display": card_display,
                    "has_card": has_card,
                    "statement_period_from": period_from,
                    "statement_period_to": period_to,
                    "period_display": period_display,
                    "has_period": has_period,
                    "transaction_count": stmt.get("transaction_count", 0),
                    "total_debit": total_debit,
                    "total_credit": total_credit,
                    "total_debit_display": total_debit_display,
                    "total_credit_display": total_credit_display,
                    "total_amount_due": total_due,
                    "total_due_display": total_due_display,
                    "extracted_net": extracted_net,
                    "extracted_net_display": extracted_net_display,
                    "has_metadata": has_metadata,
                    "minimum_amount_due": min_due,
                    "min_due_display": min_due_display,
                    "has_min_due": has_min_due,
                    "payment_due_date": stmt.get("payment_due_date") or "",
                    "has_due_date": has_due_date,
                    "validation_status": validation_status,
                    "validation_difference": diff,
                    "diff_display": diff_display,
                    "has_difference": has_difference,
                    "badge_text": badge_text,
                    "badge_color": badge_color,
                })
            
            self.statements_with_metadata = formatted_statements

            # Enrich each transaction with parsed fields
            enriched = []
            for txn in raw:
                t = dict(txn)
                dt = parse_date(t.get("date", ""))
                t["parsed_date"] = dt.strftime("%Y-%m-%d") if dt else ""
                t["date_display"] = format_date_display(t.get("date", ""))
                t["month_key"] = dt.strftime("%Y-%m") if dt else ""
                t["weekday"] = dt.strftime("%A") if dt else ""
                t["amount_display"] = format_inr(t.get("amount") or 0)
                t["amount"] = float(t.get("amount") or 0)
                t["description_display"] = clean_description(t.get("description", ""))
                enriched.append(t)

            self._all_transactions = enriched

            banks = sorted(set(t["bank"] for t in enriched if t.get("bank")))
            self.available_banks = ["All"] + banks
            cats = sorted(set(t["category"] for t in enriched if t.get("category")))
            self.available_categories = ["All"] + cats
            self.bank_count = len(banks)
            self.card_count = len(banks)

            self._apply_filters_and_compute()
            self.statements_list = self._all_statements

        except Exception as e:
            self.error_message = f"Error loading data: {str(e)}"

        self.is_loading = False

    def _apply_filters_and_compute(self):
        filtered = list(self._all_transactions)

        # Apply member filter first (if not "All")
        if self.selected_member != "All":
            filtered = [t for t in filtered if t.get("member") == self.selected_member]

        if self.search_query:
            q = self.search_query.lower()
            filtered = [t for t in filtered if q in (t.get("description") or "").lower()]

        if self.selected_bank != "All":
            filtered = [t for t in filtered if t.get("bank") == self.selected_bank]

        if self.selected_category != "All":
            filtered = [t for t in filtered if t.get("category") == self.selected_category]

        if self.selected_type != "All":
            filtered = [t for t in filtered if (t.get("type") or "").lower() == self.selected_type.lower()]

        try:
            min_a = float(self.min_amount_str) if self.min_amount_str else 0.0
        except ValueError:
            min_a = 0.0
        try:
            max_a = float(self.max_amount_str) if self.max_amount_str else 999999999.0
        except ValueError:
            max_a = 999999999.0

        filtered = [t for t in filtered if min_a <= (t.get("amount") or 0) <= max_a]

        if self.date_range_start:
            filtered = [t for t in filtered if t.get("parsed_date", "") >= self.date_range_start]
        if self.date_range_end:
            filtered = [t for t in filtered if t.get("parsed_date", "") <= self.date_range_end]

        self.filtered_transactions = filtered
        self.transaction_count = len(filtered)
        
        # Compute display strings for UI
        self.transaction_count_display = str(self.transaction_count)
        self.card_count_display = f"{self.card_count} cards"
        self.bank_count_display = f"{self.bank_count} banks"

        # ── Create analytics dataset (optionally exclude transfers) ────────────
        if self.exclude_transfers:
            analytics_txns = [t for t in filtered if t.get("category") != "Payments & Transfers"]
        else:
            analytics_txns = filtered
        
        # Set analytics count for display
        self.analytics_count = len(analytics_txns)
        self.analytics_count_display = str(self.analytics_count)

        # ── Compute large transaction highlighting ──────────────────────────────
        debit_txns_for_avg = [t for t in filtered if t.get("type") == "debit"]
        avg_debit = sum(t.get("amount", 0) for t in debit_txns_for_avg) / len(debit_txns_for_avg) if debit_txns_for_avg else 0
        large_threshold = avg_debit * 2.5  # 2.5x average = "large" transaction
        
        # Add is_large flag to filtered_transactions
        for t in self.filtered_transactions:
            t["is_large"] = bool(t.get("type") == "debit" and t.get("amount", 0) > large_threshold)

        # ── Compute contextual KPIs ─────────────────────────────────────────────
        self._compute_contextual_kpis(analytics_txns)

        # ── Compute charts with analytics_txns (excludes transfers if toggle ON) ─
        self._compute_overview_metrics(analytics_txns)
        self._compute_monthly_chart(analytics_txns)
        self._compute_category_chart(analytics_txns)
        self._compute_bank_chart(analytics_txns)
        self._compute_category_summary(analytics_txns)
        self._compute_top_merchants(analytics_txns)
        self._compute_day_of_week(analytics_txns)
        self._compute_recent_transactions(filtered)  # Recent shows all, not filtered
        self._compute_analytics(analytics_txns)
        self._compute_recurring(analytics_txns)
        self._compute_largest(analytics_txns)
        self._compute_category_monthly(analytics_txns)
        self._compute_behavioral_insights(analytics_txns)
        
        # Update display transactions (limited to 100 for UI)
        self.display_transactions = filtered[:100]
        self.total_filtered_count = len(filtered)

    def _compute_contextual_kpis(self, txns: list):
        """Compute contextual KPI display strings."""
        debit_txns = [t for t in txns if t.get("type") == "debit"]
        
        # Total months of data
        month_keys = set(t.get("month_key", "") for t in debit_txns if t.get("month_key"))
        total_months = len(month_keys)
        self.total_months_display = f"across {total_months} months" if total_months > 0 else ""
        
        # Average transactions per month
        if total_months > 0:
            avg_txn = len(debit_txns) / total_months
            self.avg_txn_display = f"~{int(avg_txn)} per month"
        else:
            self.avg_txn_display = ""
        
        # This month vs average comparison
        monthly: dict = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly[mk] += t.get("amount", 0)
        
        if monthly:
            sorted_months = sorted(monthly.keys())
            this_month = sorted_months[-1] if sorted_months else ""
            this_month_amount = monthly.get(this_month, 0)
            
            # Average across all months
            avg_monthly = sum(monthly.values()) / len(monthly)
            
            # Difference from average
            diff = this_month_amount - avg_monthly
            if diff > 0:
                self.above_avg_display = f"+{format_inr(diff)} above avg"
                self.above_avg_positive = True  # Spending MORE is "bad"
                self.above_avg_color = "var(--amber-9)"  # Red/amber for above average (bad)
            elif diff < 0:
                self.above_avg_display = f"{format_inr(abs(diff))} below avg"
                self.above_avg_positive = False
                self.above_avg_color = "var(--green-9)"  # Green for below average (good)
            else:
                self.above_avg_display = "at average"
                self.above_avg_positive = False
                self.above_avg_color = "var(--gray-9)"
        else:
            self.above_avg_display = ""
            self.above_avg_positive = False
            self.above_avg_color = "var(--gray-9)"

    def toggle_exclude_transfers(self, value: bool):
        """Set the exclude_transfers flag and recompute."""
        self.exclude_transfers = value
        self._apply_filters_and_compute()

    def set_selected_member(self, value: str):
        """Set the selected member filter and recompute."""
        self.selected_member = value
        self._apply_filters_and_compute()

    def open_add_member_dialog(self):
        """Open the add member dialog."""
        self.show_add_member_dialog = True
        self.new_member_name = ""
        self.new_member_color = "#6366F1"

    def close_add_member_dialog(self):
        """Close the add member dialog."""
        self.show_add_member_dialog = False
        self.new_member_name = ""

    def set_new_member_name(self, value: str):
        """Set the new member name."""
        self.new_member_name = value

    def set_new_member_color(self, value: str):
        """Set the new member color."""
        self.new_member_color = value

    def add_new_member(self):
        """Add a new family member."""
        if self.new_member_name.strip():
            db = self._get_db()
            db.add_member(self.new_member_name.strip(), self.new_member_color)
            self.show_add_member_dialog = False
            self.new_member_name = ""
            self.load_all_data()

    def _compute_overview_metrics(self, txns: list):
        # Use the most recent month present in the data (not current calendar month)
        # This handles historical statements correctly
        debit_txns = [t for t in txns if t.get("type") == "debit"]
        month_keys = sorted(set(t.get("month_key", "") for t in debit_txns if t.get("month_key")))

        if month_keys:
            this_month = month_keys[-1]
            # Previous month in data
            if len(month_keys) >= 2:
                last_month = month_keys[-2]
            else:
                # Compute calendar previous month from this_month
                try:
                    dt = datetime.strptime(this_month, "%Y-%m")
                    last_month = (dt.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
                except ValueError:
                    last_month = ""
        else:
            this_month = datetime.now().strftime("%Y-%m")
            last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        total = sum(t.get("amount", 0) for t in debit_txns)
        self.total_spend = format_inr(total)
        self.total_spend_raw = total

        this_m = sum(t.get("amount", 0) for t in debit_txns if t.get("month_key") == this_month)
        self.this_month_spend = format_inr(this_m)

        last_m = sum(t.get("amount", 0) for t in debit_txns if t.get("month_key") == last_month)
        self.last_month_spend = format_inr(last_m)

        if last_m > 0:
            change = ((this_m - last_m) / last_m) * 100
            self.month_change = f"{'+' if change >= 0 else ''}{change:.1f}%"
        elif this_m > 0:
            self.month_change = "+100%"
        else:
            self.month_change = "—"

    def _compute_monthly_chart(self, txns: list):
        monthly: dict = defaultdict(float)
        for t in txns:
            mk = t.get("month_key", "")
            if mk and t.get("type") == "debit":
                monthly[mk] += t.get("amount", 0)
        sorted_months = sorted(monthly.keys())[-12:]
        self.monthly_chart_data = [
            {"month": self._fmt_month(m), "amount": round(monthly[m], 2)}
            for m in sorted_months
        ]

    def _compute_category_chart(self, txns: list):
        cat_totals: dict = defaultdict(float)
        for t in txns:
            if t.get("type") == "debit":
                cat_totals[t.get("category", "Uncategorized")] += t.get("amount", 0)
        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        result = []
        others = 0.0
        for i, (cat, amt) in enumerate(sorted_cats):
            if i < 8:
                result.append({"name": cat, "value": round(amt, 2)})
            else:
                others += amt
        if others > 0:
            result.append({"name": "Others", "value": round(others, 2)})
        self.category_chart_data = result

    def _compute_bank_chart(self, txns: list):
        bank_totals: dict = defaultdict(float)
        for t in txns:
            if t.get("type") == "debit":
                bank_totals[t.get("bank", "Unknown")] += t.get("amount", 0)
        self.bank_chart_data = [
            {"bank": bank, "amount": round(amt, 2)}
            for bank, amt in sorted(bank_totals.items(), key=lambda x: x[1], reverse=True)
        ]

    def _compute_category_summary(self, txns: list):
        cat_data: dict = defaultdict(lambda: {"amount": 0.0, "count": 0})
        total_debit = 0.0
        for t in txns:
            if t.get("type") == "debit":
                cat = t.get("category", "Uncategorized")
                cat_data[cat]["amount"] += t.get("amount", 0)
                cat_data[cat]["count"] += 1
                total_debit += t.get("amount", 0)
        self.category_summary = [
            {
                "category": cat,
                "amount": round(data["amount"], 2),
                "amount_display": format_inr(data["amount"]),
                "count": data["count"],
                "count_display": f"{data['count']} txns",
                "avg": round(data["amount"] / data["count"], 2) if data["count"] > 0 else 0,
                "percentage": round((data["amount"] / total_debit) * 100, 1) if total_debit > 0 else 0,
                "percentage_display": f"{round((data['amount'] / total_debit) * 100, 1) if total_debit > 0 else 0}%",
            }
            for cat, data in sorted(cat_data.items(), key=lambda x: x[1]["amount"], reverse=True)
        ]

    def _compute_top_merchants(self, txns: list):
        merchant_data: dict = defaultdict(lambda: {"amount": 0.0, "count": 0})
        for t in txns:
            if t.get("type") == "debit" and t.get("description"):
                desc = (t["description"] or "")[:40]
                merchant_data[desc]["amount"] += t.get("amount", 0)
                merchant_data[desc]["count"] += 1
        sorted_m = sorted(merchant_data.items(), key=lambda x: x[1]["amount"], reverse=True)[:10]
        self.top_merchants = [
            {
                "merchant": name,
                "amount": round(data["amount"], 2),
                "amount_display": format_inr(data["amount"]),
                "count": data["count"],
                "count_display": f"{data['count']}x",
            }
            for name, data in sorted_m
        ]

    def _compute_day_of_week(self, txns: list):
        day_totals: dict = defaultdict(lambda: {"amount": 0.0, "count": 0})
        for t in txns:
            if t.get("type") == "debit" and t.get("weekday"):
                day_totals[t["weekday"]]["amount"] += t.get("amount", 0)
                day_totals[t["weekday"]]["count"] += 1
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.day_of_week_data = [
            {
                "day": day[:3],
                "amount": round(day_totals[day]["amount"], 2),
                "avg": round(day_totals[day]["amount"] / max(day_totals[day]["count"], 1), 2),
                "count": day_totals[day]["count"],
            }
            for day in day_order
        ]

    def _compute_recent_transactions(self, txns: list):
        sorted_txns = sorted(txns, key=lambda t: t.get("parsed_date", ""), reverse=True)
        self.recent_transactions = sorted_txns[:10]

    def _compute_analytics(self, txns: list):
        debit_txns = [t for t in txns if t.get("type") == "debit"]
        monthly: dict = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly[mk] += t.get("amount", 0)
        sorted_months = sorted(monthly.keys())
        monthly_amounts = [monthly[m] for m in sorted_months]
        avg_monthly = round(sum(monthly_amounts) / len(monthly_amounts), 2) if monthly_amounts else 0.0
        
        # Add average field to each spending_trend item for reference line
        self.spending_trend = [
            {"month": self._fmt_month(m), "amount": round(monthly[m], 2), "average": avg_monthly}
            for m in sorted_months
        ]
        
        self.avg_monthly_spend = avg_monthly
        self.avg_monthly_display = format_inr(self.avg_monthly_spend)
        if monthly:
            max_month = max(monthly, key=lambda k: monthly[k])
            self.highest_month = self._fmt_month(max_month)
            self.highest_month_amount = format_inr(monthly[max_month])
        else:
            self.highest_month = ""
            self.highest_month_amount = "₹0"
        if debit_txns:
            biggest = max(debit_txns, key=lambda t: t.get("amount", 0))
            self.biggest_txn_desc = (biggest.get("description") or "")[:40]
            self.biggest_txn_amount = format_inr(biggest.get("amount", 0))
            self.biggest_txn_date = biggest.get("date", "")
            self.biggest_txn_bank = biggest.get("bank", "")
        self.unique_merchants = len(set((t.get("description") or "") for t in debit_txns))
        self.unique_merchants_display = str(self.unique_merchants)

    def _compute_recurring(self, txns: list):
        merchant_txns: dict = defaultdict(list)
        for t in txns:
            if t.get("type") == "debit" and t.get("description"):
                merchant_txns[t["description"]].append(t.get("amount", 0))
        recurring = []
        for desc, amounts in merchant_txns.items():
            if len(amounts) >= 2:
                avg_amt = sum(amounts) / len(amounts)
                if avg_amt > 0:
                    variance = max(abs(a - avg_amt) / avg_amt for a in amounts)
                    if variance < 0.2:
                        # Annualized cost: assume monthly if frequency >= 2
                        annual_cost = round(avg_amt * 12, 2)
                        recurring.append({
                            "description": desc[:50],
                            "frequency": len(amounts),
                            "frequency_display": f"{len(amounts)}x",
                            "avg_amount": round(avg_amt, 2),
                            "avg_display": format_inr(avg_amt),
                            "total": round(sum(amounts), 2),
                            "total_display": format_inr(sum(amounts)),
                            "annual_cost": annual_cost,
                            "annual_display": format_inr(annual_cost),
                        })
        recurring.sort(key=lambda x: x["frequency"], reverse=True)
        self.recurring_charges = recurring[:15]

    def _compute_largest(self, txns: list):
        debit_txns = [t for t in txns if t.get("type") == "debit"]
        debit_txns.sort(key=lambda t: t.get("amount", 0), reverse=True)
        # Add rank field to each transaction
        self.largest_transactions = [
            {**t, "rank": str(i + 1)}
            for i, t in enumerate(debit_txns[:10])
        ]

    def _compute_category_monthly(self, txns: list):
        data: dict = defaultdict(lambda: defaultdict(float))
        for t in txns:
            if t.get("type") == "debit":
                mk = t.get("month_key", "")
                cat = t.get("category", "Uncategorized")
                if mk:
                    data[mk][cat] += t.get("amount", 0)
        cat_totals: dict = defaultdict(float)
        for mk in data:
            for cat, amt in data[mk].items():
                cat_totals[cat] += amt
        top_cats = [c for c, _ in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:6]]
        sorted_months = sorted(data.keys())[-12:]
        result = []
        for m in sorted_months:
            row: dict = {"month": self._fmt_month(m)}
            for cat in top_cats:
                row[cat] = round(data[m].get(cat, 0), 2)
            others = sum(v for k, v in data[m].items() if k not in top_cats)
            if others > 0:
                row["Others"] = round(others, 2)
            result.append(row)
        self.category_monthly_data = result

    def _compute_behavioral_insights(self, txns: list):
        """Compute behavioral insights about spending patterns."""
        insights = []
        
        debit_txns = [t for t in txns if t.get("type") == "debit"]
        if not debit_txns:
            self.behavioral_insights = []
            return
        
        # Get month keys and identify current month
        month_keys = sorted(set(t.get("month_key", "") for t in debit_txns if t.get("month_key")))
        if len(month_keys) < 1:
            self.behavioral_insights = []
            return
        
        this_month = month_keys[-1]
        previous_months = month_keys[:-1]
        
        # 1. CATEGORY DRIFT: Compare current month vs average for each category
        cat_monthly: dict = defaultdict(lambda: defaultdict(float))
        for t in debit_txns:
            mk = t.get("month_key", "")
            cat = t.get("category", "Uncategorized")
            if mk:
                cat_monthly[cat][mk] += t.get("amount", 0)
        
        for cat, monthly_data in cat_monthly.items():
            if len(monthly_data) >= 2:
                this_month_cat = monthly_data.get(this_month, 0)
                other_months = [v for k, v in monthly_data.items() if k != this_month]
                if other_months:
                    avg_other = sum(other_months) / len(other_months)
                    if avg_other > 0:
                        pct_change = ((this_month_cat - avg_other) / avg_other) * 100
                        if pct_change > 30:
                            insights.append({
                                "title": f"{cat} Spending Up",
                                "description": f"You spent {int(pct_change)}% more on {cat} this month compared to your average",
                                "severity": "warning",
                                "icon": "trending-up",
                                "border_color": "var(--amber-9)",
                            })
                        elif pct_change < -30:
                            insights.append({
                                "title": f"{cat} Savings",
                                "description": f"You spent {int(abs(pct_change))}% less on {cat} this month — nice savings!",
                                "severity": "positive",
                                "icon": "trending-down",
                                "border_color": "var(--green-9)",
                            })
        
        # 2. SPENDING TREND: Compare total spend this month vs average
        monthly_totals: dict = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly_totals[mk] += t.get("amount", 0)
        
        if len(monthly_totals) >= 2:
            this_month_total = monthly_totals.get(this_month, 0)
            other_totals = [v for k, v in monthly_totals.items() if k != this_month]
            if other_totals:
                avg_other_total = sum(other_totals) / len(other_totals)
                if avg_other_total > 0:
                    pct_change_total = ((this_month_total - avg_other_total) / avg_other_total) * 100
                    if pct_change_total > 15:
                        insights.append({
                            "title": "Spending Trending Up",
                            "description": f"Overall spending is up {int(pct_change_total)}% compared to your monthly average",
                            "severity": "warning",
                            "icon": "alert-triangle",
                            "border_color": "var(--amber-9)",
                        })
                    elif pct_change_total < -15:
                        insights.append({
                            "title": "Spending Down",
                            "description": f"Great job! Spending is down {int(abs(pct_change_total))}% compared to your average",
                            "severity": "positive",
                            "icon": "check-circle",
                            "border_color": "var(--green-9)",
                        })
        
        # 3. LARGEST SINGLE EXPENSE this month
        this_month_txns = [t for t in debit_txns if t.get("month_key") == this_month]
        if this_month_txns:
            largest = max(this_month_txns, key=lambda t: t.get("amount", 0))
            desc = (largest.get("description_display") or largest.get("description", ""))[:30]
            amt = format_inr(largest.get("amount", 0))
            insights.append({
                "title": "Largest Expense",
                "description": f"Your biggest expense this month: {desc} at {amt}",
                "severity": "info",
                "icon": "zap",
                "border_color": "var(--blue-9)",
            })
        
        # 4. RECURRING BURDEN: Annual cost of recurring charges
        if self.recurring_charges:
            total_annual = sum(r.get("annual_cost", 0) for r in self.recurring_charges)
            count = len(self.recurring_charges)
            if total_annual > 0:
                insights.append({
                    "title": "Recurring Charges",
                    "description": f"You have {count} recurring charges totaling {format_inr(total_annual)}/year",
                    "severity": "info",
                    "icon": "repeat",
                    "border_color": "var(--blue-9)",
                })
        
        # 5. NEW MERCHANTS: Merchants appearing only in current month
        if previous_months:
            prev_merchants = set(
                t.get("description", "")[:40]
                for t in debit_txns
                if t.get("month_key") in previous_months and t.get("description")
            )
            this_month_merchants = set(
                t.get("description", "")[:40]
                for t in debit_txns
                if t.get("month_key") == this_month and t.get("description")
            )
            new_merchants = this_month_merchants - prev_merchants
            if new_merchants:
                # Pick the one with highest spend
                new_merchant_spends = {}
                for t in debit_txns:
                    if t.get("month_key") == this_month and t.get("description"):
                        desc = t.get("description", "")[:40]
                        if desc in new_merchants:
                            new_merchant_spends[desc] = new_merchant_spends.get(desc, 0) + t.get("amount", 0)
                if new_merchant_spends:
                    top_new = max(new_merchant_spends.items(), key=lambda x: x[1])
                    insights.append({
                        "title": "New Merchant",
                        "description": f"New merchant this month: {top_new[0][:25]} ({format_inr(top_new[1])})",
                        "severity": "info",
                        "icon": "store",
                        "border_color": "var(--blue-9)",
                    })
        
        # 6. WEEKEND VS WEEKDAY spending
        weekend_days = {"Saturday", "Sunday"}
        weekend_total = 0.0
        weekend_count = 0
        weekday_total = 0.0
        weekday_count = 0
        
        for t in debit_txns:
            weekday = t.get("weekday", "")
            amount = t.get("amount", 0)
            if weekday in weekend_days:
                weekend_total += amount
                weekend_count += 1
            else:
                weekday_total += amount
                weekday_count += 1
        
        if weekend_count > 0 and weekday_count > 0:
            avg_weekend = weekend_total / weekend_count
            avg_weekday = weekday_total / weekday_count
            if avg_weekday > 0 and avg_weekend > avg_weekday * 1.5:
                pct_higher = int(((avg_weekend - avg_weekday) / avg_weekday) * 100)
                insights.append({
                    "title": "Weekend Spending",
                    "description": f"Weekend spending is {pct_higher}% higher per transaction than weekdays",
                    "severity": "info",
                    "icon": "calendar",
                    "border_color": "var(--blue-9)",
                })
        
        # Sort by severity: alert > warning > info > positive
        severity_order = {"alert": 0, "warning": 1, "info": 2, "positive": 3}
        insights.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 2))
        
        # Take top 6 insights
        self.behavioral_insights = insights[:6]

    @staticmethod
    def _fmt_month(month_key: str) -> str:
        try:
            dt = datetime.strptime(month_key, "%Y-%m")
            return dt.strftime("%b %y")
        except (ValueError, TypeError):
            return month_key

    # ============ EVENT HANDLERS ============

    def set_search(self, value: str):
        self.search_query = value
        self._apply_filters_and_compute()

    def set_bank_filter(self, value: str):
        self.selected_bank = value
        self._apply_filters_and_compute()

    def set_category_filter(self, value: str):
        self.selected_category = value
        self._apply_filters_and_compute()

    def set_type_filter(self, value: str):
        self.selected_type = value
        self._apply_filters_and_compute()

    def set_date_start(self, value: str):
        self.date_range_start = value
        self._apply_filters_and_compute()

    def set_date_end(self, value: str):
        self.date_range_end = value
        self._apply_filters_and_compute()

    def set_min_amount(self, value: str):
        self.min_amount_str = value
        self._apply_filters_and_compute()

    def set_max_amount(self, value: str):
        self.max_amount_str = value
        self._apply_filters_and_compute()

    def clear_filters(self):
        self.search_query = ""
        self.selected_bank = "All"
        self.selected_category = "All"
        self.selected_type = "All"
        self.date_range_start = ""
        self.date_range_end = ""
        self.min_amount_str = ""
        self.max_amount_str = ""
        self._apply_filters_and_compute()

    def drill_into_category(self, category: str):
        self.selected_category_drill = category
        self.category_drill_transactions = [
            t for t in self._all_transactions if t.get("category") == category
        ]

    def update_transaction_category(self, txn_id: int, new_category: str):
        db = self._get_db()
        db.update_category(txn_id, new_category)
        self.load_all_data()

    def set_bulk_category_input(self, value: str):
        self.bulk_category_input = value

    # ============ DELETE STATEMENT ============

    def confirm_delete(self, stmt_id: int, bank: str):
        """Show delete confirmation dialog."""
        self.delete_confirm_id = stmt_id
        self.delete_confirm_bank = bank
        self.delete_confirm_show = True

    def cancel_delete(self):
        self.delete_confirm_show = False
        self.delete_confirm_id = 0
        self.delete_confirm_bank = ""

    def delete_statement(self):
        """Delete confirmed statement and reload."""
        if self.delete_confirm_id > 0:
            try:
                db = self._get_db()
                db.delete_statement(self.delete_confirm_id)
            except Exception as e:
                self.error_message = f"Delete failed: {str(e)}"
        self.delete_confirm_show = False
        self.delete_confirm_id = 0
        self.delete_confirm_bank = ""
        self.load_all_data()

    # ============ CSV EXPORT ============

    def export_csv(self) -> rx.event.EventSpec:
        """Export filtered transactions to CSV file."""
        import io
        
        # Build CSV content
        output = io.StringIO()
        output.write("Date,Bank,Description,Amount,Type,Category\n")
        
        for txn in self.filtered_transactions:
            date = txn.get("date_display", "")
            bank = txn.get("bank", "")
            desc = (txn.get("description_display") or txn.get("description", "")).replace(",", ";").replace('"', '""')
            amount = txn.get("amount", 0)
            txn_type = txn.get("type", "")
            category = txn.get("category", "")
            
            output.write(f'"{date}","{bank}","{desc}",{amount},"{txn_type}","{category}"\n')
        
        csv_data = output.getvalue()
        output.close()
        
        return rx.download(data=csv_data, filename="transactions.csv")

    # ============ UPLOAD HANDLER ============

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle PDF upload, process through extraction pipeline."""
        self.upload_status = []
        self.upload_error = ""
        self.upload_processing = True
        yield

        for file in files:
            try:
                filename = file.filename
                if not filename.lower().endswith(".pdf"):
                    self.upload_status = self.upload_status + [f"❌ {filename}: Not a PDF file"]
                    yield
                    continue

                self.upload_status = self.upload_status + [f"📄 Processing: {filename}"]
                yield

                # Save uploaded file to data/uploads/
                upload_dir = Path(_DB_PATH).parent / "uploads"
                upload_dir.mkdir(exist_ok=True)
                save_path = upload_dir / filename

                upload_data = await file.read()
                with open(save_path, "wb") as f:
                    f.write(upload_data)

                # Check for duplicate
                db = self._get_db()
                if db.get_duplicate_check_by_filename(filename):
                    self.upload_status = self.upload_status + [f"⚠️ {filename}: Already imported, skipping"]
                    yield
                    continue

                # Step 1: Extract transactions
                extractor = StatementExtractor(str(save_path))
                result = extractor.extract()
                bank = result.get("bank", "Unknown")
                transactions = result.get("transactions", [])

                self.upload_status = self.upload_status + [f"✅ Bank: {bank}"]
                self.upload_status = self.upload_status + [f"✅ Extracted {len(transactions)} transactions"]
                yield

                # Step 2: Categorize
                for txn in transactions:
                    amount_float = None
                    try:
                        amt_str = str(txn.get("amount", "")).replace(",", "")
                        amount_float = float(amt_str) if amt_str else None
                    except (ValueError, TypeError):
                        pass
                    cat, subcat = categorize(txn.get("description", ""), amount_float)
                    txn["category"] = cat
                    txn["subcategory"] = subcat

                # Step 3: Store in database with member tag
                # Use selected_member if not "All", otherwise default to "Self"
                member = self.selected_member if self.selected_member != "All" else "Self"
                
                period = result.get("statement_period", {})
                statement_id = db.insert_statement(
                    bank=bank,
                    file_name=filename,
                    period_from=period.get("from", ""),
                    period_to=period.get("to", ""),
                )
                
                # Add member to each transaction before inserting
                for txn in transactions:
                    txn["member"] = member
                
                db.insert_transactions(statement_id, transactions)

                # Step 4: Extract metadata
                try:
                    meta_extractor = MetadataExtractor(str(save_path), bank=bank)
                    metadata = meta_extractor.extract()
                    db.update_statement_metadata(statement_id, metadata)

                    if metadata.get("total_amount_due"):
                        self.upload_status = self.upload_status + [
                            f"✅ Total Due: ₹{metadata['total_amount_due']:,.2f}"
                        ]

                    # Step 5: Validate
                    total_due = metadata.get("total_amount_due")
                    if total_due and total_due > 0:
                        debit_sum = sum(
                            float(str(t.get("amount", "0")).replace(",", ""))
                            for t in transactions if t.get("type") == "debit"
                        )
                        credit_sum = sum(
                            float(str(t.get("amount", "0")).replace(",", ""))
                            for t in transactions if t.get("type") == "credit"
                        )
                        net = debit_sum - credit_sum
                        diff = abs(net - total_due)

                        if diff < 1.0:
                            val_status = "exact_match"
                            self.upload_status = self.upload_status + ["✅ Validation: exact match"]
                        elif diff < 50.0:
                            val_status = "close_match"
                            self.upload_status = self.upload_status + [f"⚠️ Validation: close match (₹{diff:.2f} off)"]
                        else:
                            val_status = "mismatch"
                            self.upload_status = self.upload_status + [f"❌ Validation: mismatch (₹{diff:.2f} off)"]

                        db.update_validation_status(statement_id, val_status, round(diff, 2))
                    else:
                        db.update_validation_status(statement_id, "no_metadata", 0.0)
                        self.upload_status = self.upload_status + ["⚠️ Validation: total due not found in PDF"]
                except Exception as meta_err:
                    self.upload_status = self.upload_status + [f"⚠️ Metadata: {str(meta_err)[:60]}"]

                self.upload_status = self.upload_status + [f"✅ Saved to database (Member: {member})"]
                yield

            except Exception as e:
                self.upload_status = self.upload_status + [f"❌ Error: {str(e)[:80]}"]
                self.upload_error = str(e)
                yield

        self.upload_processing = False
        self.load_all_data()
        yield

    # ============ CSV/EXCEL IMPORT HANDLERS ============

    async def handle_csv_upload(self, files: list[rx.UploadFile]):
        """Handle CSV/Excel upload, detect format, go to step 2."""
        self.import_processing = True
        self.import_result = {}
        yield

        for file in files:
            try:
                filename = file.filename
                suffix = Path(filename).suffix.lower()
                
                if suffix not in [".csv", ".xlsx", ".xls"]:
                    self.import_result = {"error": f"Unsupported file type: {suffix}"}
                    self.import_processing = False
                    yield
                    return

                # Save uploaded file to data/uploads/
                upload_dir = Path(_DB_PATH).parent / "uploads"
                upload_dir.mkdir(exist_ok=True)
                save_path = upload_dir / filename

                upload_data = await file.read()
                with open(save_path, "wb") as f:
                    f.write(upload_data)

                # Detect format
                importer = CSVImporter(str(save_path))
                detected = importer.detect_format()

                # Populate state
                self.import_file_name = filename
                self.import_detected = detected
                self.import_columns = detected.get("columns", [])
                self.import_preview = detected.get("sample_rows", [])
                
                # Initialize mapping with detected values
                detected_mapping = detected.get("detected_mapping", {})
                self.import_mapping = {
                    "date_column": detected_mapping.get("date_column", ""),
                    "description_column": detected_mapping.get("description_column", ""),
                    "amount_column": detected_mapping.get("amount_column", ""),
                    "type_column": detected_mapping.get("type_column", ""),
                    "debit_column": detected_mapping.get("debit_column", ""),
                    "credit_column": detected_mapping.get("credit_column", ""),
                    "date_format": detected.get("date_format", "%d/%m/%Y"),
                    "skip_rows": detected.get("skip_rows", 0),
                    "bank": "Manual Import",
                    "member": "Self",
                }

                # Load members
                db = self._get_db()
                members = db.get_members()
                self.available_members = ["All"] + [m.get("name", "Self") for m in members]

                # Go to step 2
                self.import_step = 2

            except Exception as e:
                self.import_result = {"error": str(e)}
                self.import_step = 1

        self.import_processing = False
        yield

    def update_mapping(self, field: str, value: str):
        """Update individual mapping field."""
        self.import_mapping[field] = value

    def go_to_import_step(self, step: int):
        """Navigate to a specific import step."""
        self.import_step = step

    def preview_import(self):
        """Apply mapping to first 5 rows, show preview, go to step 3."""
        try:
            # Get the saved file
            upload_dir = Path(_DB_PATH).parent / "uploads"
            save_path = upload_dir / self.import_file_name
            
            if not save_path.exists():
                self.import_result = {"error": "File not found. Please upload again."}
                return

            # Import with current mapping
            importer = CSVImporter(str(save_path))
            transactions, warnings = importer.import_transactions(self.import_mapping)

            if not transactions:
                self.import_result = {
                    "error": "No valid transactions found. Please check your column mapping.",
                    "warnings": warnings,
                }
                return

            # Store full transactions for later
            self.import_transactions_cache = transactions

            # Show first 5 in preview
            self.import_preview = transactions[:5]
            self.import_result = {
                "total_count": len(transactions),
                "warnings": warnings,
            }

            # Go to step 3
            self.import_step = 3

        except Exception as e:
            self.import_result = {"error": str(e)}

    def confirm_import(self):
        """Run full import, store in db, show result, go to step 4."""
        try:
            if not self.import_transactions_cache:
                self.import_result = {"success": False, "error": "No transactions to import"}
                self.import_step = 4
                return

            # Get member and bank from mapping
            member = self.import_mapping.get("member", "Self")
            bank = self.import_mapping.get("bank", "Manual Import")

            # Insert into database
            db = self._get_db()
            inserted = db.insert_csv_transactions(
                transactions=self.import_transactions_cache,
                member=member,
                source="csv",
                bank=bank,
                file_name=self.import_file_name,
            )

            self.import_result = {
                "success": True,
                "imported_count": inserted,
                "skipped_count": len(self.import_transactions_cache) - inserted,
                "total_count": len(self.import_transactions_cache),
            }

            # Go to step 4
            self.import_step = 4

            # Reload data
            self.load_all_data()

        except Exception as e:
            self.import_result = {"success": False, "error": str(e)}
            self.import_step = 4

    def reset_import(self):
        """Clear all import state, go back to step 1."""
        self.import_step = 1
        self.import_file_name = ""
        self.import_detected = {}
        self.import_columns = []
        self.import_preview = []
        self.import_mapping = {}
        self.import_result = {}
        self.import_processing = False
        self.import_transactions_cache = []