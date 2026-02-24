import reflex as rx
from ..state import FinanceState


# ─────────────────────────────────────────────────────────────────────────────
# Metric Card Component
# ─────────────────────────────────────────────────────────────────────────────

def metric_card(
    title: str,
    value: rx.Var,
    subtitle: str = "",
    icon_name: str = "wallet",
    subtitle_color: str = "var(--gray-9)",
) -> rx.Component:
    """Metric card using Radix props for reliable styling."""
    return rx.card(
        rx.flex(
            # Label row with icon
            rx.flex(
                rx.icon(icon_name, size=16, color="var(--accent-9)"),
                rx.text(title, size="1", weight="medium", color="var(--gray-9)"),
                align="center",
                gap="2",
            ),
            # Value
            rx.text(value, size="6", weight="bold", font="mono", trim="both"),
            # Subtitle
            rx.cond(
                subtitle != "",
                rx.text(subtitle, size="1", color=subtitle_color),
                rx.fragment(),
            ),
            direction="column",
            gap="1",
        ),
        size="2",
        variant="surface",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chart Components
# ─────────────────────────────────────────────────────────────────────────────

def chart_card(title: str, chart: rx.Component, height: int = 280) -> rx.Component:
    """Chart wrapper using Radix props."""
    return rx.card(
        rx.flex(
            rx.text(title, size="4", weight="bold"),
            rx.separator(size="4"),
            rx.box(
                rx.recharts.responsive_container(
                    chart,
                    width="100%",
                    height=height,
                ),
                width="100%",
                min_height=f"{height}px",
            ),
            direction="column",
            gap="3",
        ),
        size="3",
        variant="surface",
    )


def monthly_bar_chart() -> rx.Component:
    """Monthly spending bar chart with Radix color tokens."""
    return rx.recharts.bar_chart(
        rx.recharts.cartesian_grid(
            stroke_dasharray="3 3",
            stroke="var(--gray-4)",
            vertical=False,
        ),
        rx.recharts.x_axis(
            data_key="month",
            tick={"fill": "var(--gray-9)", "fontSize": 11},
            axis_line=False,
            tick_line=False,
        ),
        rx.recharts.y_axis(
            tick={"fill": "var(--gray-9)", "fontSize": 11},
            axis_line=False,
            tick_line=False,
        ),
        rx.recharts.tooltip(
            content_style={
                "backgroundColor": "var(--gray-2)",
                "border": "1px solid var(--gray-6)",
                "borderRadius": "8px",
                "color": "var(--gray-12)",
                "fontSize": "12px",
            },
        ),
        rx.recharts.bar(
            data_key="amount",
            fill="var(--accent-9)",
            radius=[4, 4, 0, 0],
        ),
        data=FinanceState.monthly_chart_data,
    )


def category_bar_chart() -> rx.Component:
    """Category horizontal bar chart with Radix color tokens."""
    return rx.recharts.bar_chart(
        rx.recharts.cartesian_grid(
            stroke_dasharray="3 3",
            stroke="var(--gray-4)",
            horizontal=True,
            vertical=False,
        ),
        rx.recharts.y_axis(
            data_key="name",
            type_="category",
            tick={"fill": "var(--gray-9)", "fontSize": 11},
            width=120,
            axis_line=False,
            tick_line=False,
        ),
        rx.recharts.x_axis(
            type_="number",
            tick={"fill": "var(--gray-9)", "fontSize": 11},
            axis_line=False,
            tick_line=False,
        ),
        rx.recharts.tooltip(
            content_style={
                "backgroundColor": "var(--gray-2)",
                "border": "1px solid var(--gray-6)",
                "borderRadius": "8px",
                "color": "var(--gray-12)",
                "fontSize": "12px",
            },
        ),
        rx.recharts.bar(
            data_key="value",
            fill="var(--accent-9)",
            radius=[0, 4, 4, 0],
        ),
        data=FinanceState.category_chart_data,
        layout="vertical",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Behavioral Insights
# ─────────────────────────────────────────────────────────────────────────────

def insight_card(insight: rx.Var[dict]) -> rx.Component:
    """Behavioral insight card with colored left border."""
    return rx.card(
        rx.flex(
            rx.flex(
                rx.icon("sparkles", size=16, color=insight["border_color"]),
                rx.text(insight["title"], size="2", weight="bold"),
                align="center",
                gap="2",
            ),
            rx.text(insight["description"], size="2", color="var(--gray-9)"),
            direction="column",
            gap="2",
        ),
        size="2",
        variant="surface",
        style={"borderLeft": f"3px solid {insight['border_color']}"},
    )


def insights_section() -> rx.Component:
    """Grid of behavioral insight cards."""
    return rx.cond(
        FinanceState.behavioral_insights.length() > 0,
        rx.flex(
            rx.flex(
                rx.icon("lightbulb", size=18, color="var(--accent-9)"),
                rx.text("Spending Insights", size="4", weight="bold"),
                align="center",
                gap="2",
            ),
            rx.grid(
                rx.foreach(
                    FinanceState.behavioral_insights,
                    insight_card,
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                gap="3",
            ),
            direction="column",
            gap="3",
        ),
        rx.fragment(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Recent Transactions Table
# ─────────────────────────────────────────────────────────────────────────────

def recent_transactions_table() -> rx.Component:
    """Recent transactions table using Radix table props."""
    return rx.cond(
        FinanceState.recent_transactions,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Date", width="100px"),
                    rx.table.column_header_cell("Description"),
                    rx.table.column_header_cell("Amount", width="120px", align="right"),
                    rx.table.column_header_cell("Type", width="80px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    FinanceState.recent_transactions,
                    lambda txn: rx.table.row(
                        rx.table.cell(txn["date_display"]),
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
                        ),
                    ),
                ),
            ),
            size="2",
            variant="surface",
        ),
        rx.flex(
            rx.icon("inbox", size=32, color="var(--gray-8)"),
            rx.text("No transactions yet", size="2", color="var(--gray-9)"),
            direction="column",
            align="center",
            gap="2",
            padding="6",
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Error Banner
# ─────────────────────────────────────────────────────────────────────────────

def error_banner() -> rx.Component:
    """Error banner using Radix callout."""
    return rx.cond(
        FinanceState.error_message != "",
        rx.callout.root(
            rx.callout.icon(rx.icon("triangle-alert", size=16)),
            rx.callout.text(FinanceState.error_message),
            color="red",
            variant="soft",
        ),
        rx.fragment(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Financial Summary Banner (Hero Section)
# ─────────────────────────────────────────────────────────────────────────────

def financial_summary_banner() -> rx.Component:
    """Large hero banner showing this month's spend as the focal point."""
    return rx.card(
        rx.flex(
            # Left side: This Month's Spend (Hero)
            rx.flex(
                rx.text("Net Spend This Month", size="1", color="var(--gray-9)", weight="medium"),
                rx.text(
                    FinanceState.this_month_spend,
                    size="8",
                    weight="bold",
                    font="mono",
                    trim="both",
                ),
                rx.text(
                    FinanceState.above_avg_display,
                    size="2",
                    color=FinanceState.above_avg_color,
                ),
                direction="column",
                gap="1",
            ),
            # Right side: Total Spend context
            rx.flex(
                rx.flex(
                    rx.text("Total Spend", size="1", color="var(--gray-9)", weight="medium"),
                    rx.text(
                        FinanceState.total_spend,
                        size="5",
                        weight="bold",
                        font="mono",
                    ),
                    rx.text(
                        FinanceState.total_months_display,
                        size="1",
                        color="var(--gray-9)",
                    ),
                    direction="column",
                    gap="1",
                    align="end",
                ),
                direction="column",
                align="end",
            ),
            justify="between",
            align="start",
            width="100%",
        ),
        size="4",
        variant="surface",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Overview Page
# ─────────────────────────────────────────────────────────────────────────────

def overview_page() -> rx.Component:
    """Premium Overview page using Radix component props."""
    return rx.box(
        # ── Row 0: Header + Member Badge + Toggle ─────────────────────
        rx.flex(
            rx.flex(
                rx.heading("Overview", size="7", weight="bold"),
                rx.cond(
                    FinanceState.selected_member != "All",
                    rx.badge(
                        FinanceState.selected_member,
                        variant="soft",
                        size="2",
                        color_scheme="indigo",
                    ),
                    rx.fragment(),
                ),
                align="center",
                gap="2",
            ),
            rx.spacer(),
            rx.flex(
                rx.text("Exclude Transfers", size="1", color="var(--gray-9)"),
                rx.switch(
                    checked=FinanceState.exclude_transfers,
                    on_change=FinanceState.toggle_exclude_transfers,
                    size="1",
                ),
                align="center",
                gap="2",
            ),
            align="center",
            width="100%",
            mb="6",
        ),
        
        # ── Error Banner ───────────────────────────────────────────────
        error_banner(),
        
        # ── Row 1: Financial Summary Banner (Hero) ─────────────────────
        rx.box(
            financial_summary_banner(),
            mb="6",
        ),
        
        # ── Row 2: Metric Cards Grid ───────────────────────────────────
        rx.grid(
            metric_card(
                "Last Month",
                FinanceState.last_month_spend,
                FinanceState.month_change,
                "calendar-check",
                subtitle_color=rx.cond(
                    FinanceState.month_change.contains("-"),
                    "var(--green-9)",
                    rx.cond(
                        FinanceState.month_change.contains("+"),
                        "var(--amber-9)",
                        "var(--gray-9)",
                    ),
                ),
            ),
            metric_card(
                "Avg Monthly",
                FinanceState.avg_monthly_display,
                FinanceState.total_months_display,
                "trending-up",
            ),
            metric_card(
                "Transactions",
                FinanceState.analytics_count_display,
                FinanceState.avg_txn_display,
                "receipt",
            ),
            metric_card(
                "Active Banks",
                FinanceState.bank_count_display,
                FinanceState.card_count_display,
                "credit-card",
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            gap="4",
            mb="6",
        ),
        
        # ── Row 3: Behavioral Insights ─────────────────────────────────
        rx.cond(
            FinanceState.behavioral_insights.length() > 0,
            rx.box(
                insights_section(),
                mb="6",
            ),
            rx.fragment(),
        ),
        
        # ── Row 4: Charts ──────────────────────────────────────────────
        rx.grid(
            chart_card("Monthly Spending", monthly_bar_chart()),
            chart_card("Category Split", category_bar_chart()),
            columns=rx.breakpoints(initial="1", lg="2"),
            gap="4",
            mb="6",
        ),
        
        # ── Row 5: Recent Transactions ─────────────────────────────────
        rx.card(
            rx.flex(
                rx.text("Recent Transactions", size="4", weight="bold"),
                rx.separator(size="4"),
                recent_transactions_table(),
                direction="column",
                gap="3",
            ),
            size="3",
            variant="surface",
        ),
        
        padding="6",
    )