import reflex as rx
from ..state import FinanceState


def upload_log_line(line: str) -> rx.Component:
    """Render a single upload log line with appropriate color."""
    return rx.text(
        line,
        size="2",
        color=rx.cond(
            line.startswith("✅"),
            "var(--green-9)",
            rx.cond(
                line.startswith("❌"),
                "var(--red-9)",
                rx.cond(
                    line.startswith("⚠️"),
                    "var(--amber-9)",
                    "var(--gray-9)",
                ),
            ),
        ),
    )


def upload_zone() -> rx.Component:
    """Upload zone with drag-and-drop support."""
    return rx.upload(
        rx.flex(
            rx.cond(
                FinanceState.upload_processing,
                rx.flex(
                    rx.spinner(size="3", color="var(--accent-9)"),
                    rx.text("Processing...", size="2", color="var(--gray-9)"),
                    direction="column",
                    align="center",
                    gap="3",
                ),
                rx.flex(
                    rx.box(
                        rx.icon("file-up", size=40, color="var(--accent-9)"),
                        background="var(--accent-3)",
                        border_radius="16px",
                        padding="5",
                    ),
                    rx.text("Drop PDF here or click to browse", size="3", weight="medium"),
                    rx.text(
                        "Supports: HDFC, ICICI, Axis, SBI, IDFC First, IndusInd",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    rx.button(
                        rx.icon("upload", size=14),
                        "Select PDF",
                        variant="soft",
                        size="2",
                        mt="2",
                    ),
                    direction="column",
                    align="center",
                    gap="3",
                ),
            ),
            direction="column",
            align="center",
            justify="center",
            min_height="200px",
            width="100%",
        ),
        id="pdf-upload",
        accept={".pdf": ["application/pdf"]},
        max_files=5,
        on_drop=FinanceState.handle_upload(rx.upload_files(upload_id="pdf-upload")),
        border="2px dashed var(--gray-6)",
        border_radius="16px",
        padding="6",
        width="100%",
    )


def processing_log() -> rx.Component:
    """Processing log section."""
    return rx.cond(
        FinanceState.upload_status.length() > 0,
        rx.card(
            rx.flex(
                rx.flex(
                    rx.icon("terminal", size=14, color="var(--gray-9)"),
                    rx.text("Processing Log", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
                rx.separator(size="4", mt="3", mb="3"),
                rx.flex(
                    rx.foreach(FinanceState.upload_status, upload_log_line),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                direction="column",
                gap="0",
                width="100%",
            ),
            size="3",
            variant="surface",
            mb="6",
        ),
        rx.fragment(),
    )


def recent_uploads_table() -> rx.Component:
    """Recent uploads table."""
    return rx.cond(
        FinanceState.statements_with_metadata,
        rx.card(
            rx.flex(
                rx.flex(
                    rx.icon("history", size=14, color="var(--gray-9)"),
                    rx.text("Recent Uploads", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
                rx.separator(size="4", mt="3", mb="3"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("File"),
                            rx.table.column_header_cell("Bank", width="100px"),
                            rx.table.column_header_cell("Txns", width="60px", align="center"),
                            rx.table.column_header_cell("Validation", width="120px"),
                            rx.table.column_header_cell("Diff", width="80px", align="right"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            FinanceState.statements_with_metadata,
                            lambda s: rx.table.row(
                                rx.table.cell(rx.text(s["file_name"], size="1", font="mono")),
                                rx.table.cell(rx.badge(s["bank"], variant="surface", size="1")),
                                rx.table.cell(
                                    rx.text(s["transaction_count"].to_string(), size="1"),
                                    align="center",
                                ),
                                rx.table.cell(
                                    rx.badge(
                                        s["badge_text"],
                                        color_scheme=s["badge_color"],
                                        variant="soft",
                                        size="1",
                                    ),
                                ),
                                rx.table.cell(
                                    rx.cond(
                                        s["has_difference"],
                                        rx.text(s["diff_display"], size="1", font="mono"),
                                        rx.text("—", size="1", color="var(--gray-8)"),
                                    ),
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
                gap="0",
                width="100%",
            ),
            size="3",
            variant="surface",
        ),
        rx.fragment(),
    )


def member_selector() -> rx.Component:
    """Member selector for upload."""
    return rx.flex(
        rx.text("Import for:", size="2", weight="medium", color="var(--gray-9)"),
        rx.select(
            FinanceState.available_members,
            value=FinanceState.selected_member,
            on_change=FinanceState.set_selected_member,
            size="2",
        ),
        rx.cond(
            FinanceState.selected_member != "All",
            rx.badge(
                f"Transactions will be tagged as '{FinanceState.selected_member}'",
                variant="soft",
                size="1",
                color_scheme="indigo",
            ),
            rx.badge(
                "Transactions will be tagged as 'Self'",
                variant="soft",
                size="1",
                color_scheme="gray",
            ),
        ),
        direction="column",
        gap="2",
        width="100%",
    )


def upload_page() -> rx.Component:
    """Upload page with centered content."""
    return rx.box(
        # Header
        rx.flex(
            rx.heading("Upload Statement", size="7", weight="bold"),
            rx.text("Import a new credit card PDF statement", size="2", color="var(--gray-9)"),
            direction="column",
            gap="1",
            mb="6",
        ),
        
        # Member selector
        rx.card(
            member_selector(),
            size="3",
            variant="surface",
            mb="4",
        ),
        
        # Upload zone
        rx.card(
            upload_zone(),
            size="3",
            variant="surface",
            mb="6",
        ),
        
        # Processing log
        processing_log(),
        
        # Recent uploads
        recent_uploads_table(),
        
        padding="6",
        max_width="600px",
        margin_x="auto",
    )