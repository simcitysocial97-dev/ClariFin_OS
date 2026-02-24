import reflex as rx
from ..state import FinanceState
from ..styles import PAGE_CONTAINER_STYLE, HEADING_STYLE, MUTED_TEXT_STYLE, CARD_STYLE, SUBHEADING_STYLE


def statements_page() -> rx.Component:
    return rx.box(
        # Header
        rx.hstack(
            rx.vstack(
                rx.text("Statements", class_name=HEADING_STYLE),
                rx.hstack(
                    rx.text(FinanceState.bank_count.to_string(), class_name="text-indigo-400 text-sm font-semibold"),
                    rx.text("banks imported", class_name=MUTED_TEXT_STYLE),
                    spacing="1",
                    align="center",
                ),
                spacing="1",
            ),
            justify="between",
            width="100%",
            class_name="mb-8",
        ),

        # Statements table
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("file-text", size=16, class_name="text-indigo-400"),
                    rx.text("Imported Statements", class_name=SUBHEADING_STYLE),
                    spacing="2",
                    align="center",
                ),
                rx.separator(class_name="border-zinc-800 w-full"),
                rx.cond(
                    FinanceState.statements_list,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Bank", class_name="text-zinc-500 text-xs font-medium"),
                                rx.table.column_header_cell("File", class_name="text-zinc-500 text-xs font-medium"),
                                rx.table.column_header_cell("Period From", class_name="text-zinc-500 text-xs font-medium"),
                                rx.table.column_header_cell("Period To", class_name="text-zinc-500 text-xs font-medium"),
                                rx.table.column_header_cell("Txns", class_name="text-zinc-500 text-xs font-medium text-center"),
                                rx.table.column_header_cell("Total Debit", class_name="text-zinc-500 text-xs font-medium text-right"),
                                rx.table.column_header_cell("Total Credit", class_name="text-zinc-500 text-xs font-medium text-right"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                FinanceState.statements_list,
                                lambda s: rx.table.row(
                                    rx.table.cell(
                                        rx.badge(s["bank"], variant="soft", size="1"),
                                    ),
                                    rx.table.cell(
                                        rx.text(s["file_name"], class_name="text-zinc-400 text-xs font-mono"),
                                    ),
                                    rx.table.cell(
                                        rx.text(
                                            rx.cond(s["statement_period_from"], s["statement_period_from"], "—"),
                                            class_name="text-zinc-400 text-xs",
                                        ),
                                    ),
                                    rx.table.cell(
                                        rx.text(
                                            rx.cond(s["statement_period_to"], s["statement_period_to"], "—"),
                                            class_name="text-zinc-400 text-xs",
                                        ),
                                    ),
                                    rx.table.cell(
                                        rx.badge(
                                            s["transaction_count"].to_string(),
                                            color_scheme="indigo",
                                            variant="soft",
                                            size="1",
                                        ),
                                        class_name="text-center",
                                    ),
                                    rx.table.cell(
                                        rx.text(
                                            "₹" + s["total_debit"].to_string(),
                                            class_name="text-zinc-50 text-xs font-mono text-right",
                                        ),
                                    ),
                                    rx.table.cell(
                                        rx.text(
                                            "₹" + s["total_credit"].to_string(),
                                            class_name="text-green-400 text-xs font-mono text-right",
                                        ),
                                    ),
                                    class_name="hover:bg-zinc-800/50 transition-colors",
                                ),
                            ),
                        ),
                        variant="ghost",
                        size="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.icon("inbox", size=40, class_name="text-zinc-700"),
                        rx.text("No statements imported yet", class_name="text-zinc-500 text-sm"),
                        spacing="3",
                        align="center",
                        class_name="py-12",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            class_name=f"{CARD_STYLE} p-6 mb-6",
        ),

        # Statement Health (Coming Soon)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("shield-check", size=16, class_name="text-blue-400"),
                    rx.text("Statement Health", class_name=SUBHEADING_STYLE),
                    rx.badge("Coming Soon", color_scheme="blue", variant="soft", size="1"),
                    spacing="2",
                    align="center",
                ),
                rx.separator(class_name="border-zinc-800 w-full"),
                rx.vstack(
                    rx.text("Metadata extraction will validate:", class_name="text-zinc-400 text-sm font-medium"),
                    rx.vstack(
                        rx.hstack(rx.icon("circle-check", size=14, class_name="text-zinc-600"), rx.text("Total Due vs extracted transaction sum", class_name="text-zinc-500 text-sm"), spacing="2"),
                        rx.hstack(rx.icon("circle-check", size=14, class_name="text-zinc-600"), rx.text("Payment Due Date", class_name="text-zinc-500 text-sm"), spacing="2"),
                        rx.hstack(rx.icon("circle-check", size=14, class_name="text-zinc-600"), rx.text("Minimum Amount Due", class_name="text-zinc-500 text-sm"), spacing="2"),
                        rx.hstack(rx.icon("circle-check", size=14, class_name="text-zinc-600"), rx.text("Card number (last 4 digits)", class_name="text-zinc-500 text-sm"), spacing="2"),
                        spacing="2",
                        align="start",
                    ),
                    rx.hstack(
                        rx.icon("clock", size=14, class_name="text-blue-400"),
                        rx.text("Status: Awaiting metadata extractor implementation", class_name="text-blue-400 text-sm"),
                        spacing="2",
                        align="center",
                        class_name="mt-2",
                    ),
                    spacing="3",
                    align="start",
                ),
                spacing="3",
                width="100%",
            ),
            class_name="bg-blue-500/5 border border-blue-500/20 rounded-xl p-6 mb-6",
        ),

        # Import instructions
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("terminal", size=16, class_name="text-zinc-400"),
                    rx.text("Import New Statement", class_name=SUBHEADING_STYLE),
                    spacing="2",
                    align="center",
                ),
                rx.separator(class_name="border-zinc-800 w-full"),
                rx.text("Run the following command from the python-parser directory:", class_name=MUTED_TEXT_STYLE),
                rx.code_block(
                    "python src/ingest.py path/to/statement.pdf",
                    language="bash",
                    class_name="bg-zinc-950 border border-zinc-800 rounded-lg text-sm",
                ),
                rx.text(
                    "Supported banks: HDFC, ICICI, Axis, SBI, IDFC First, IndusInd",
                    class_name="text-zinc-600 text-xs",
                ),
                spacing="3",
                width="100%",
            ),
            class_name=f"{CARD_STYLE} p-6",
        ),

        class_name=PAGE_CONTAINER_STYLE,
    )
