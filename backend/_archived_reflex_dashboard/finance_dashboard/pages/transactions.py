import reflex as rx
from ..state import FinanceState


def transaction_row(txn: rx.Var[dict]) -> rx.Component:
    """Transaction table row using Radix props with large transaction highlighting."""
    return rx.table.row(
        rx.table.cell(
            rx.text(txn["date_display"], size="2"),
            width="110px",
        ),
        rx.table.cell(
            rx.badge(txn["bank"], variant="surface", size="1"),
            width="120px",
        ),
        rx.table.cell(
            rx.text(txn["description_display"], size="2"),
        ),
        rx.table.cell(
            rx.text(
                txn["amount_display"],
                size="2",
                weight=rx.cond(txn["is_large"], "bold", "medium"),
                text_align="right",
                font="mono",
                color=rx.cond(txn["is_large"], "var(--amber-9)", "var(--gray-12)"),
            ),
            align="right",
            width="120px",
        ),
        rx.table.cell(
            rx.badge(
                txn["type"],
                color_scheme=rx.cond(
                    txn["type"] == "credit",
                    "green",
                    "gray",
                ),
                variant="soft",
                size="1",
            ),
            width="80px",
        ),
        rx.table.cell(
            rx.badge(txn["category"], variant="outline", size="1"),
            width="150px",
        ),
    )


def transactions_table() -> rx.Component:
    """Transactions table using Radix props."""
    return rx.cond(
        FinanceState.display_transactions,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date", width="110px"),
                    rx.table.column_header_cell("Bank", width="120px"),
                    rx.table.column_header_cell("Description"),
                    rx.table.column_header_cell("Amount", width="120px", align="right"),
                    rx.table.column_header_cell("Type", width="80px"),
                    rx.table.column_header_cell("Category", width="150px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    FinanceState.display_transactions,
                    transaction_row,
                ),
            ),
            size="2",
            variant="surface",
            width="100%",
        ),
        rx.flex(
            rx.icon("inbox", size=32, color="var(--gray-8)"),
            rx.text("No transactions match your filters", size="2", color="var(--gray-9)"),
            direction="column",
            align="center",
            gap="2",
            padding="6",
        ),
    )


def filter_pills() -> rx.Component:
    """Smart filter pills for quick filtering."""
    return rx.flex(
        rx.badge(
            "Large (>₹5K)",
            variant="surface",
            size="2",
            cursor="pointer",
            on_click=lambda: [
                FinanceState.set_min_amount("5000"),
                FinanceState.set_max_amount("999999999"),
            ],
        ),
        rx.badge(
            "Recurring",
            variant="surface",
            size="2",
            cursor="pointer",
            on_click=lambda: FinanceState.set_search(""),
        ),
        rx.badge(
            "This Month",
            variant="surface",
            size="2",
            cursor="pointer",
            on_click=lambda: [
                FinanceState.set_date_start(""),
                FinanceState.set_date_end(""),
            ],
        ),
        rx.badge(
            "Uncategorized",
            variant="surface",
            size="2",
            cursor="pointer",
            on_click=lambda: FinanceState.set_category_filter("Uncategorized"),
        ),
        gap="2",
        wrap="wrap",
    )


def transactions_page() -> rx.Component:
    """Transactions page using Radix component props."""
    return rx.box(
        # Header row
        rx.flex(
            rx.flex(
                rx.heading("Transactions", size="7", weight="bold"),
                rx.badge(
                    FinanceState.transaction_count.to_string(),
                    color_scheme="indigo",
                    variant="soft",
                    size="2",
                ),
                align="center",
                gap="2",
            ),
            rx.button(
                rx.icon("download", size=14),
                "Export CSV",
                variant="soft",
                size="2",
                on_click=FinanceState.export_csv,
            ),
            justify="between",
            width="100%",
            mb="6",
        ),

        # Filter bar inside card
        rx.card(
            rx.flex(
                rx.input(
                    rx.input.slot(rx.icon("search", size=14)),
                    placeholder="Search transactions...",
                    value=FinanceState.search_query,
                    on_change=FinanceState.set_search,
                    size="2",
                    flex="2",
                ),
                rx.select(
                    FinanceState.available_banks,
                    value=FinanceState.selected_bank,
                    on_change=FinanceState.set_bank_filter,
                    size="2",
                    placeholder="Bank",
                ),
                rx.select(
                    FinanceState.available_categories,
                    value=FinanceState.selected_category,
                    on_change=FinanceState.set_category_filter,
                    size="2",
                    placeholder="Category",
                ),
                rx.select(
                    ["All", "debit", "credit"],
                    value=FinanceState.selected_type,
                    on_change=FinanceState.set_type_filter,
                    size="2",
                    placeholder="Type",
                ),
                gap="3",
                align="center",
                width="100%",
            ),
            size="3",
            variant="surface",
            mb="4",
        ),

        # Smart filter pills
        rx.box(
            filter_pills(),
            mb="4",
        ),

        # Transaction table
        rx.card(
            transactions_table(),
            size="3",
            variant="surface",
            mb="4",
        ),

        # Showing X of Y text
        rx.flex(
            rx.text(
                "Showing ",
                rx.text(FinanceState.display_transactions.length().to_string(), weight="medium"),
                " of ",
                rx.text(FinanceState.total_filtered_count.to_string(), weight="medium"),
                " transactions",
                size="1",
                color="var(--gray-9)",
            ),
            justify="center",
            width="100%",
        ),

        padding="6",
    )