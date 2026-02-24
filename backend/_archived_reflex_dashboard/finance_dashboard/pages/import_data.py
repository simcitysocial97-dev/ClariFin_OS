"""
Import Data Page
================
Multi-step import flow for CSV/Excel files.

Steps:
1. Upload - drag and drop CSV/Excel files
2. Column Mapping - configure which columns map to which fields
3. Preview & Confirm - see how transactions will be imported
4. Result - import summary
"""

import reflex as rx
from ..state import FinanceState


# ============================================================
# Step Components
# ============================================================

def step_indicator() -> rx.Component:
    """Step indicator showing current progress."""
    return rx.flex(
        rx.flex(
            rx.cond(
                FinanceState.import_step >= 1,
                rx.box("1", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500 text-white text-sm font-medium"),
                rx.box("1", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 text-gray-400 text-sm font-medium"),
            ),
            rx.text("Upload", size="2", color=rx.cond(FinanceState.import_step >= 1, "var(--gray-11)", "var(--gray-8)")),
            direction="column",
            align="center",
            gap="1",
        ),
        rx.box(class_name="flex-1 h-0.5 bg-gray-700 self-center mx-2"),
        rx.flex(
            rx.cond(
                FinanceState.import_step >= 2,
                rx.box("2", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500 text-white text-sm font-medium"),
                rx.box("2", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 text-gray-400 text-sm font-medium"),
            ),
            rx.text("Mapping", size="2", color=rx.cond(FinanceState.import_step >= 2, "var(--gray-11)", "var(--gray-8)")),
            direction="column",
            align="center",
            gap="1",
        ),
        rx.box(class_name="flex-1 h-0.5 bg-gray-700 self-center mx-2"),
        rx.flex(
            rx.cond(
                FinanceState.import_step >= 3,
                rx.box("3", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500 text-white text-sm font-medium"),
                rx.box("3", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 text-gray-400 text-sm font-medium"),
            ),
            rx.text("Preview", size="2", color=rx.cond(FinanceState.import_step >= 3, "var(--gray-11)", "var(--gray-8)")),
            direction="column",
            align="center",
            gap="1",
        ),
        rx.box(class_name="flex-1 h-0.5 bg-gray-700 self-center mx-2"),
        rx.flex(
            rx.cond(
                FinanceState.import_step >= 4,
                rx.box("4", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500 text-white text-sm font-medium"),
                rx.box("4", class_name="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 text-gray-400 text-sm font-medium"),
            ),
            rx.text("Done", size="2", color=rx.cond(FinanceState.import_step >= 4, "var(--gray-11)", "var(--gray-8)")),
            direction="column",
            align="center",
            gap="1",
        ),
        justify="center",
        gap="2",
        margin_bottom="6",
    )


def upload_step() -> rx.Component:
    """Step 1: Upload CSV/Excel file."""
    return rx.flex(
        rx.upload(
            rx.flex(
                rx.cond(
                    FinanceState.import_processing,
                    rx.flex(
                        rx.spinner(size="3", color="var(--indigo-9)"),
                        rx.text("Detecting format...", size="2", color="var(--gray-9)"),
                        direction="column",
                        align="center",
                        gap="3",
                    ),
                    rx.flex(
                        rx.box(
                            rx.icon("file-spreadsheet", size=40, color="var(--indigo-9)"),
                            background="var(--indigo-3)",
                            border_radius="16px",
                            padding="5",
                        ),
                        rx.text("Drop CSV or Excel file here", size="3", weight="medium"),
                        rx.text(
                            "Supports: .csv, .xlsx, .xls",
                            size="1",
                            color="var(--gray-9)",
                        ),
                        rx.button(
                            rx.icon("upload", size=14),
                            "Select File",
                            variant="soft",
                            size="2",
                            margin_top="2",
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
            id="csv-upload",
            accept={
                ".csv": ["text/csv", "application/vnd.ms-excel"],
                ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
                ".xls": ["application/vnd.ms-excel"],
            },
            max_files=1,
            on_drop=FinanceState.handle_csv_upload(rx.upload_files(upload_id="csv-upload")),
            border="2px dashed var(--gray-6)",
            border_radius="16px",
            padding="6",
            width="100%",
        ),
        direction="column",
        gap="4",
    )


def mapping_step() -> rx.Component:
    """Step 2: Configure column mapping."""
    return rx.flex(
        # File info
        rx.card(
            rx.flex(
                rx.icon("file-text", size=16, color="var(--indigo-9)"),
                rx.text(FinanceState.import_file_name, size="2", weight="medium"),
                rx.text(f"({FinanceState.import_detected.get('row_count', 0)} rows)", size="1", color="var(--gray-9)"),
                align="center",
                gap="2",
            ),
            size="2",
            margin_bottom="4",
        ),
        
        # Sample data preview
        rx.text("Sample Data", size="3", weight="bold", margin_bottom="2"),
        rx.card(
            rx.box(
                rx.text("Preview data will appear after file upload", size="2", color="var(--gray-9)"),
                padding="4",
            ),
            size="2",
            margin_bottom="4",
        ),
        
        # Column mapping
        rx.text("Column Mapping", size="3", weight="bold", margin_bottom="2"),
        rx.card(
            rx.flex(
                # Date column
                rx.flex(
                    rx.text("Date Column", size="2", weight="medium"),
                    rx.select(
                        FinanceState.import_columns,
                        value=FinanceState.import_mapping.get("date_column", ""),
                        on_change=lambda v: FinanceState.update_mapping("date_column", v),
                        placeholder="Select date column",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                # Description column
                rx.flex(
                    rx.text("Description Column", size="2", weight="medium"),
                    rx.select(
                        FinanceState.import_columns,
                        value=FinanceState.import_mapping.get("description_column", ""),
                        on_change=lambda v: FinanceState.update_mapping("description_column", v),
                        placeholder="Select description column",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                # Amount column
                rx.flex(
                    rx.text("Amount Column", size="2", weight="medium"),
                    rx.select(
                        FinanceState.import_columns,
                        value=FinanceState.import_mapping.get("amount_column", ""),
                        on_change=lambda v: FinanceState.update_mapping("amount_column", v),
                        placeholder="Select amount column",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                # Type column (optional)
                rx.flex(
                    rx.text("Type Column (optional)", size="2", weight="medium"),
                    rx.select(
                        FinanceState.import_columns,
                        value=FinanceState.import_mapping.get("type_column", ""),
                        on_change=lambda v: FinanceState.update_mapping("type_column", v),
                        placeholder="Select type column",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                # Date format
                rx.flex(
                    rx.text("Date Format", size="2", weight="medium"),
                    rx.select(
                        ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y", "%d %b %Y"],
                        value=FinanceState.import_mapping.get("date_format", "%d/%m/%Y"),
                        on_change=lambda v: FinanceState.update_mapping("date_format", v),
                        placeholder="Select date format",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                # Bank name
                rx.flex(
                    rx.text("Bank/Source Name", size="2", weight="medium"),
                    rx.input(
                        value=FinanceState.import_mapping.get("bank", "Manual Import"),
                        on_change=lambda v: FinanceState.update_mapping("bank", v),
                        placeholder="e.g., HDFC Bank, Manual Import",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                # Member
                rx.flex(
                    rx.text("Member", size="2", weight="medium"),
                    rx.select(
                        FinanceState.available_members,
                        value=FinanceState.import_mapping.get("member", "Self"),
                        on_change=lambda v: FinanceState.update_mapping("member", v),
                        placeholder="Select member",
                        size="2",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                direction="row",
                gap="4",
                flex_wrap="wrap",
            ),
            size="2",
            margin_bottom="4",
        ),
        
        # Navigation buttons
        rx.flex(
            rx.button(
                rx.icon("arrow-left", size=14),
                "Back",
                variant="outline",
                size="2",
                on_click=FinanceState.reset_import,
            ),
            rx.button(
                "Preview Import",
                rx.icon("arrow-right", size=14),
                size="2",
                on_click=FinanceState.preview_import,
                is_disabled=rx.cond(
                    FinanceState.import_mapping.get("date_column", ""),
                    rx.cond(
                        FinanceState.import_mapping.get("description_column", ""),
                        False,
                        True,
                    ),
                    True,
                ),
            ),
            justify="between",
            width="100%",
        ),
        
        direction="column",
        gap="4",
    )


def preview_step() -> rx.Component:
    """Step 3: Preview transactions before import."""
    return rx.flex(
        # Summary
        rx.card(
            rx.flex(
                rx.icon("eye", size=16, color="var(--indigo-9)"),
                rx.text("Preview transactions", size="2", weight="medium"),
                align="center",
                gap="2",
            ),
            size="2",
            margin_bottom="4",
        ),
        
        # Preview info
        rx.text("Transactions ready for import", size="3", weight="bold", margin_bottom="2"),
        rx.card(
            rx.box(
                rx.text("Review your column mapping and click Import to proceed", size="2", color="var(--gray-9)"),
                padding="4",
            ),
            size="2",
            margin_bottom="4",
        ),
        
        # Navigation buttons
        rx.flex(
            rx.button(
                rx.icon("arrow-left", size=14),
                "Back",
                variant="outline",
                size="2",
                on_click=FinanceState.go_to_import_step(2),
            ),
            rx.button(
                rx.icon("check", size=14),
                "Import Transactions",
                size="2",
                on_click=FinanceState.confirm_import,
            ),
            justify="between",
            width="100%",
        ),
        
        direction="column",
        gap="4",
    )


def result_step() -> rx.Component:
    """Step 4: Import result summary."""
    return rx.flex(
        rx.card(
            rx.flex(
                rx.icon("circle-check", size=48, color="var(--green-9)"),
                rx.heading("Import Complete!", size="5", weight="bold"),
                rx.text(
                    "Your transactions have been imported successfully",
                    size="2",
                    color="var(--gray-9)",
                ),
                direction="column",
                align="center",
                gap="3",
            ),
            size="2",
            margin_bottom="4",
        ),
        
        # Action buttons
        rx.flex(
            rx.button(
                rx.icon("plus", size=14),
                "Import Another File",
                variant="outline",
                size="2",
                on_click=FinanceState.reset_import,
            ),
            rx.link(
                rx.button(
                    rx.icon("receipt", size=14),
                    "View Transactions",
                    size="2",
                ),
                href="/transactions",
            ),
            justify="center",
            gap="4",
            width="100%",
        ),
        
        direction="column",
        gap="4",
    )


# ============================================================
# Main Page
# ============================================================

def import_data_page() -> rx.Component:
    """Import data page with multi-step flow."""
    return rx.box(
        # Header
        rx.flex(
            rx.heading("Import Data", size="7", weight="bold"),
            rx.text("Import transactions from CSV or Excel files", size="2", color="var(--gray-9)"),
            direction="column",
            gap="1",
            margin_bottom="6",
        ),
        
        # Step indicator
        step_indicator(),
        
        # Step content
        rx.cond(
            FinanceState.import_step == 1,
            upload_step(),
            rx.cond(
                FinanceState.import_step == 2,
                mapping_step(),
                rx.cond(
                    FinanceState.import_step == 3,
                    preview_step(),
                    result_step(),
                ),
            ),
        ),
        
        padding="6",
        max_width="800px",
        margin_x="auto",
    )