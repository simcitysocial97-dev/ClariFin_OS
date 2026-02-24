import reflex as rx
from ..state import FinanceState

# Chart colors for category bars
CHART_COLORS = [
    "#6366F1",  # Indigo
    "#8B5CF6",  # Violet
    "#EC4899",  # Pink
    "#F43F5E",  # Rose
    "#F97316",  # Orange
    "#EAB308",  # Yellow
    "#22C55E",  # Green
    "#14B8A6",  # Teal
]


def category_card(cat: rx.Var[dict]) -> rx.Component:
    """Category summary card with pre-formatted display strings."""
    return rx.card(
        # Header: category name + percentage badge
        rx.flex(
            rx.text(cat["category"], size="2", weight="bold"),
            rx.badge(cat["percentage_display"], variant="soft", size="1"),
            justify="between",
            align="center",
            width="100%",
        ),
        # Amount in large mono font
        rx.text(cat["amount_display"], size="6", weight="bold", font="mono"),
        # Count in small gray text
        rx.text(cat["count_display"], size="1", color="var(--gray-9)"),
        # Progress bar
        rx.progress(value=cat["percentage"], color_scheme="indigo", size="1", width="100%"),
        size="3",
        variant="surface",
        cursor="pointer",
        on_click=FinanceState.drill_into_category(cat["category"]),
    )


def category_cards_grid() -> rx.Component:
    """Responsive grid of category cards."""
    return rx.cond(
        FinanceState.category_summary,
        rx.grid(
            rx.foreach(
                FinanceState.category_summary,
                category_card,
            ),
            columns=rx.breakpoints(initial="1", sm="2", md="3", lg="4"),
            gap="4",
            width="100%",
        ),
        rx.flex(
            rx.icon("pie-chart", size=32, color="var(--gray-8)"),
            rx.text("No category data", size="2", color="var(--gray-9)"),
            direction="column",
            align="center",
            gap="2",
            padding="6",
        ),
    )


def monthly_category_chart() -> rx.Component:
    """Simple bar chart showing monthly spending for selected category."""
    return rx.box(
        rx.recharts.responsive_container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="var(--gray-4)"),
                rx.recharts.x_axis(
                    data_key="month",
                    tick={"fill": "var(--gray-9)", "fontSize": 11},
                ),
                rx.recharts.y_axis(
                    tick={"fill": "var(--gray-9)", "fontSize": 11},
                ),
                rx.recharts.tooltip(
                    content_style={
                        "background": "var(--gray-2)",
                        "border": "1px solid var(--gray-6)",
                        "borderRadius": "8px",
                        "color": "var(--gray-12)",
                    },
                ),
                rx.recharts.bar(
                    data_key="amount",
                    fill="var(--accent-9)",
                    radius=[4, 4, 0, 0],
                ),
                data=FinanceState.category_monthly_data,
            ),
            width="100%",
            height=280,
        ),
        width="100%",
    )


def drill_down_table() -> rx.Component:
    """Table showing transactions for selected category."""
    return rx.cond(
        FinanceState.category_drill_transactions,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date", width="110px"),
                    rx.table.column_header_cell("Description"),
                    rx.table.column_header_cell("Amount", width="120px", align="right"),
                    rx.table.column_header_cell("Bank", width="120px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    FinanceState.category_drill_transactions,
                    lambda t: rx.table.row(
                        rx.table.cell(rx.text(t["date_display"], size="1")),
                        rx.table.cell(rx.text(t["description_display"], size="1")),
                        rx.table.cell(
                            rx.text(t["amount_display"], size="1", font="mono", text_align="right"),
                            align="right",
                        ),
                        rx.table.cell(rx.badge(t["bank"], variant="surface", size="1")),
                    ),
                ),
            ),
            size="2",
            variant="surface",
            width="100%",
        ),
        rx.flex(
            rx.icon("search", size=24, color="var(--gray-8)"),
            rx.text("Select a category card above to see transactions", size="2", color="var(--gray-9)"),
            direction="column",
            align="center",
            gap="2",
            padding="6",
        ),
    )


def uncategorized_patterns_table() -> rx.Component:
    """Table showing uncategorized transaction patterns using rx.callout."""
    return rx.cond(
        FinanceState.uncategorized_patterns.length() > 0,
        rx.callout.root(
            rx.callout.icon(rx.icon("triangle-alert", size=16)),
            rx.flex(
                rx.callout.text(
                    "Uncategorized Patterns",
                    size="3",
                    weight="bold",
                ),
                rx.text(
                    "These transactions couldn't be categorized. Add keywords to categorizer.py to fix them.",
                    size="1",
                    color="var(--gray-9)",
                ),
                rx.separator(size="2", margin_top="2", margin_bottom="2"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Description"),
                            rx.table.column_header_cell("Count", width="80px", align="center"),
                            rx.table.column_header_cell("Total Amount", width="120px", align="right"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            FinanceState.uncategorized_patterns,
                            lambda p: rx.table.row(
                                rx.table.cell(rx.text(p["description"], size="1", font="mono")),
                                rx.table.cell(
                                    rx.badge(p["count"], color_scheme="amber", variant="soft", size="1"),
                                    align="center",
                                ),
                                rx.table.cell(
                                    rx.text(p["total_display"], size="1", font="mono", text_align="right"),
                                    align="right",
                                ),
                            ),
                        ),
                    ),
                    size="2",
                    variant="ghost",
                    width="100%",
                ),
                direction="column",
                gap="2",
                width="100%",
            ),
            color="amber",
            variant="soft",
            width="100%",
        ),
        rx.fragment(),
    )


def categories_page() -> rx.Component:
    """Categories page with four sections."""
    return rx.box(
        # Section 1: Category Summary Cards
        rx.flex(
            rx.heading("Categories", size="7", weight="bold"),
            rx.text("Spending breakdown by category", size="2", color="var(--gray-9)"),
            direction="column",
            gap="1",
            mb="6",
        ),
        category_cards_grid(),
        
        # Section 2: Monthly Category Chart
        rx.box(
            rx.card(
                rx.flex(
                    rx.heading("Monthly Category Breakdown", size="4", weight="bold"),
                    rx.text("Spending by category over time", size="1", color="var(--gray-9)"),
                    direction="column",
                    gap="1",
                    mb="4",
                ),
                monthly_category_chart(),
                size="3",
                variant="surface",
            ),
            mb="6",
        ),
        
        # Section 3: Category Drill-Down
        rx.box(
            rx.card(
                rx.flex(
                    rx.flex(
                        rx.heading("Category Detail", size="4", weight="bold"),
                        rx.select(
                            FinanceState.available_categories,
                            value=FinanceState.selected_category_drill,
                            on_change=FinanceState.drill_into_category,
                            size="2",
                            placeholder="Select category...",
                        ),
                        justify="between",
                        align="center",
                        width="100%",
                    ),
                    rx.separator(size="4", mb="4"),
                    drill_down_table(),
                    direction="column",
                    gap="0",
                    width="100%",
                ),
                size="3",
                variant="surface",
            ),
            mb="6",
        ),
        
        # Section 4: Uncategorized Patterns
        uncategorized_patterns_table(),
        
        padding="6",
    )