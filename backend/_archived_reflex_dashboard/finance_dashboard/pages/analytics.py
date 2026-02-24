import reflex as rx
from ..state import FinanceState


def metric_card(title: str, value: rx.Var, subtitle: str = "", icon_name: str = "wallet") -> rx.Component:
    """Metric card using Radix props for reliable styling."""
    return rx.card(
        rx.flex(
            rx.flex(
                rx.icon(icon_name, size=18, color="var(--accent-9)"),
                rx.text(title, size="1", weight="medium", color="var(--gray-9)"),
                align="center",
                gap="2",
            ),
            rx.text(value, size="6", weight="bold", trim="both", font="mono"),
            rx.cond(
                subtitle != "",
                rx.text(subtitle, size="1", color="var(--gray-9)"),
                rx.fragment(),
            ),
            direction="column",
            gap="1",
        ),
        size="3",
        variant="surface",
    )


def spending_trend_chart() -> rx.Component:
    """Area chart showing monthly spending trend with average reference line."""
    return rx.box(
        rx.recharts.responsive_container(
            rx.recharts.composed_chart(
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
                rx.recharts.area(
                    data_key="amount",
                    stroke="var(--accent-9)",
                    stroke_width=2,
                    fill="var(--accent-3)",
                    fill_opacity=0.3,
                    type_="monotone",
                ),
                rx.recharts.line(
                    data_key="average",
                    stroke="var(--gray-8)",
                    stroke_width=2,
                    stroke_dasharray="5 5",
                    dot=False,
                ),
                data=FinanceState.spending_trend,
            ),
            width="100%",
            height=280,
        ),
        width="100%",
    )


def day_of_week_chart() -> rx.Component:
    """Bar chart showing spending by day of week."""
    return rx.box(
        rx.recharts.responsive_container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(
                    stroke_dasharray="3 3",
                    stroke="var(--gray-4)",
                    horizontal=False,
                ),
                rx.recharts.x_axis(
                    data_key="day",
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
                    },
                ),
                rx.recharts.bar(
                    data_key="amount",
                    fill="var(--accent-9)",
                    radius=[4, 4, 0, 0],
                ),
                data=FinanceState.day_of_week_data,
            ),
            width="100%",
            height=220,
        ),
        width="100%",
    )


def top_merchants_table() -> rx.Component:
    """Table showing top merchants by spend."""
    return rx.cond(
        FinanceState.top_merchants,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Merchant"),
                    rx.table.column_header_cell("Count", width="60px", align="center"),
                    rx.table.column_header_cell("Amount", width="100px", align="right"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    FinanceState.top_merchants,
                    lambda m: rx.table.row(
                        rx.table.cell(rx.text(m["merchant"], size="1")),
                        rx.table.cell(
                            rx.badge(m["count_display"], variant="soft", size="1"),
                            align="center",
                        ),
                        rx.table.cell(
                            rx.text(m["amount_display"], size="1", font="mono", text_align="right"),
                            align="right",
                        ),
                    ),
                ),
            ),
            size="2",
            variant="ghost",
            width="100%",
        ),
        rx.text("No merchant data", size="1", color="var(--gray-9)"),
    )


def recurring_charges_table() -> rx.Component:
    """Table showing recurring charges with annualized cost."""
    return rx.cond(
        FinanceState.recurring_charges,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Description"),
                    rx.table.column_header_cell("Freq", width="60px", align="center"),
                    rx.table.column_header_cell("Avg", width="100px", align="right"),
                    rx.table.column_header_cell("Annual", width="100px", align="right"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    FinanceState.recurring_charges,
                    lambda r: rx.table.row(
                        rx.table.cell(rx.text(r["description"], size="1")),
                        rx.table.cell(
                            rx.badge(r["frequency_display"], color_scheme="indigo", variant="soft", size="1"),
                            align="center",
                        ),
                        rx.table.cell(
                            rx.text(r["avg_display"], size="1", font="mono", text_align="right"),
                            align="right",
                        ),
                        rx.table.cell(
                            rx.text(r["annual_display"], size="1", font="mono", text_align="right", weight="medium"),
                            align="right",
                        ),
                    ),
                ),
            ),
            size="2",
            variant="ghost",
            width="100%",
        ),
        rx.text("No recurring charges detected", size="1", color="var(--gray-9)"),
    )


def largest_transactions_table() -> rx.Component:
    """Table showing largest transactions."""
    return rx.cond(
        FinanceState.largest_transactions,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("#", width="40px"),
                    rx.table.column_header_cell("Date", width="100px"),
                    rx.table.column_header_cell("Description"),
                    rx.table.column_header_cell("Amount", width="100px", align="right"),
                    rx.table.column_header_cell("Bank", width="100px"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    FinanceState.largest_transactions,
                    lambda t: rx.table.row(
                        rx.table.cell(rx.text(t["rank"], size="1", color="var(--gray-9)")),
                        rx.table.cell(rx.text(t["date_display"], size="1")),
                        rx.table.cell(rx.text(t["description_display"], size="1")),
                        rx.table.cell(
                            rx.text(t["amount_display"], size="1", font="mono", weight="bold", text_align="right"),
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
        rx.text("No transactions", size="1", color="var(--gray-9)"),
    )


def analytics_page() -> rx.Component:
    """Analytics page with five sections."""
    return rx.box(
        # Section 1: Header
        rx.heading("Analytics & Insights", size="7", weight="bold", mb="6"),
        
        # Section 2: Four Metric Cards
        rx.grid(
            metric_card(
                "Highest Month",
                FinanceState.highest_month_amount,
                subtitle=FinanceState.highest_month,
                icon_name="trending-up",
            ),
            metric_card(
                "Avg Monthly Spend",
                FinanceState.avg_monthly_display,
                subtitle="per month",
                icon_name="bar-chart-2",
            ),
            metric_card(
                "Biggest Transaction",
                FinanceState.biggest_txn_amount,
                subtitle=FinanceState.biggest_txn_desc,
                icon_name="zap",
            ),
            metric_card(
                "Unique Merchants",
                FinanceState.unique_merchants_display,
                subtitle="distinct payees",
                icon_name="store",
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            gap="4",
            mb="6",
        ),

        # Section 3: Spending Trend
        rx.card(
            rx.flex(
                rx.text("Spending Trend", size="4", weight="bold"),
                rx.text("Monthly spend over time", size="1", color="var(--gray-9)"),
                direction="column",
                gap="1",
                mb="4",
            ),
            spending_trend_chart(),
            size="3",
            variant="surface",
            mb="6",
        ),

        # Section 4: Two-Column Layout
        rx.grid(
            # Day of Week Chart
            rx.card(
                rx.flex(
                    rx.text("Day of Week Pattern", size="4", weight="bold"),
                    rx.text("Total spend by weekday", size="1", color="var(--gray-9)"),
                    direction="column",
                    gap="1",
                    mb="4",
                ),
                day_of_week_chart(),
                size="3",
                variant="surface",
            ),
            # Top Merchants Table
            rx.card(
                rx.flex(
                    rx.text("Top Merchants", size="4", weight="bold"),
                    rx.text("By total spend", size="1", color="var(--gray-9)"),
                    direction="column",
                    gap="1",
                    mb="4",
                ),
                top_merchants_table(),
                size="3",
                variant="surface",
            ),
            columns=rx.breakpoints(initial="1", lg="2"),
            gap="4",
            mb="6",
        ),

        # Section 5: Recurring Charges
        rx.card(
            rx.flex(
                rx.flex(
                    rx.icon("repeat", size=16, color="var(--accent-9)"),
                    rx.text("Recurring Charges", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
                rx.text(
                    "Transactions appearing 2+ times with consistent amounts (within 20% variance)",
                    size="1",
                    color="var(--gray-9)",
                ),
                rx.separator(size="4", mb="4"),
                recurring_charges_table(),
                direction="column",
                gap="2",
                width="100%",
            ),
            size="3",
            variant="surface",
            mb="6",
        ),

        # Section 6: Largest Transactions
        rx.card(
            rx.flex(
                rx.flex(
                    rx.icon("arrow-up-right", size=16, color="var(--red-9)"),
                    rx.text("Largest Transactions", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
                rx.separator(size="4", mb="4"),
                largest_transactions_table(),
                direction="column",
                gap="2",
                width="100%",
            ),
            size="3",
            variant="surface",
        ),

        padding="6",
    )