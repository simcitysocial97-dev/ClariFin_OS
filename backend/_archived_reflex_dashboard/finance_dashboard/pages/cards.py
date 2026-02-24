import reflex as rx
from ..state import FinanceState


def validation_badge(s: rx.Var[dict]) -> rx.Component:
    """Render validation badge using pre-computed badge_text and badge_color."""
    return rx.badge(
        s["badge_text"],
        color_scheme=s["badge_color"],
        variant="soft",
        size="1",
    )


def statement_card(s: rx.Var[dict]) -> rx.Component:
    """Statement card component using pre-formatted values from state."""
    return rx.card(
        # Bank header with colored top border
        rx.flex(
            rx.flex(
                rx.icon("credit-card", size=16, color="var(--accent-9)"),
                rx.text(s["bank"], size="2", weight="bold"),
                align="center",
                gap="2",
            ),
            rx.cond(
                s["has_card"],
                rx.text(s["card_display"], size="1", font="mono", color="var(--gray-9)"),
                rx.fragment(),
            ),
            justify="between",
            width="100%",
        ),
        rx.separator(size="4", mt="3", mb="3"),
        # File + period
        rx.flex(
            rx.text(s["file_name"], size="1", font="mono"),
            rx.cond(
                s["has_period"],
                rx.text(s["period_display"], size="1", color="var(--gray-9)"),
                rx.fragment(),
            ),
            direction="column",
            gap="1",
            width="100%",
        ),
        # Transaction counts + amounts
        rx.flex(
            rx.flex(
                rx.text(s["transaction_count"].to_string(), size="5", weight="bold"),
                rx.text("transactions", size="1", color="var(--gray-9)"),
                direction="column",
                gap="0",
                align="center",
            ),
            rx.flex(
                rx.text(s["total_debit_display"], size="2", weight="medium", font="mono"),
                rx.text("debit", size="1", color="var(--gray-9)"),
                direction="column",
                gap="0",
                align="center",
            ),
            rx.flex(
                rx.text(s["total_credit_display"], size="2", weight="medium", font="mono", color="var(--green-9)"),
                rx.text("credit", size="1", color="var(--gray-9)"),
                direction="column",
                gap="0",
                align="center",
            ),
            justify="between",
            width="100%",
            mt="3",
        ),
        # Validation box
        rx.box(
            rx.flex(
                rx.flex(
                    rx.flex(
                        rx.text("Statement Total", size="1", color="var(--gray-9)"),
                        rx.cond(
                            s["has_metadata"],
                            rx.text(s["total_due_display"], size="2", weight="medium", font="mono"),
                            rx.text("—", size="2", color="var(--gray-8)"),
                        ),
                        direction="column",
                        gap="0",
                    ),
                    rx.flex(
                        rx.text("Extracted", size="1", color="var(--gray-9)"),
                        rx.text(s["extracted_net_display"], size="2", weight="medium", font="mono"),
                        direction="column",
                        gap="0",
                    ),
                    justify="between",
                    width="100%",
                ),
                validation_badge(s),
                rx.cond(
                    s["has_difference"],
                    rx.flex(
                        rx.text("Diff: ", size="1", color="var(--gray-9)"),
                        rx.text(s["diff_display"], size="1", color="var(--gray-9)"),
                        gap="1",
                    ),
                    rx.fragment(),
                ),
                direction="column",
                gap="2",
                width="100%",
            ),
            background="var(--gray-3)",
            border_radius="8px",
            padding="3",
            width="100%",
            mt="3",
        ),
        # Due date + min due
        rx.flex(
            rx.cond(
                s["has_due_date"],
                rx.flex(
                    rx.text("Due Date", size="1", color="var(--gray-9)"),
                    rx.text(s["payment_due_date"], size="1", font="mono"),
                    direction="column",
                    gap="0",
                ),
                rx.fragment(),
            ),
            rx.cond(
                s["has_min_due"],
                rx.flex(
                    rx.text("Min Due", size="1", color="var(--gray-9)"),
                    rx.text(s["min_due_display"], size="1", font="mono"),
                    direction="column",
                    gap="0",
                ),
                rx.fragment(),
            ),
            justify="between",
            width="100%",
            mt="3",
        ),
        rx.separator(size="4", mt="3", mb="3"),
        # Action buttons
        rx.flex(
            rx.link(
                rx.button(
                    rx.icon("receipt", size=12),
                    "View Txns",
                    variant="ghost",
                    size="1",
                ),
                href="/transactions",
            ),
            rx.button(
                rx.icon("trash-2", size=12),
                "Delete",
                variant="ghost",
                size="1",
                color_scheme="red",
                on_click=FinanceState.confirm_delete(s["id"], s["bank"]),
            ),
            justify="between",
            width="100%",
        ),
        size="3",
        variant="surface",
        style={"border_top": f"3px solid {s['bank_color']}"},
    )


def delete_confirm_dialog() -> rx.Component:
    """Delete confirmation dialog using rx.alert_dialog."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(
                rx.flex(
                    rx.icon("triangle-alert", size=20, color="var(--red-9)"),
                    rx.text("Delete Statement", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
            ),
            rx.alert_dialog.description(
                rx.flex(
                    rx.text("Are you sure you want to delete the statement from ", size="2"),
                    rx.text(FinanceState.delete_confirm_bank, size="2", weight="bold"),
                    rx.text("? This will permanently remove all associated transactions.", size="2"),
                    wrap="wrap",
                ),
            ),
            rx.flex(
                rx.button(
                    "Cancel",
                    on_click=FinanceState.cancel_delete,
                    variant="soft",
                    size="2",
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Delete",
                    on_click=FinanceState.delete_statement,
                    variant="solid",
                    color_scheme="red",
                    size="2",
                ),
                gap="3",
                justify="end",
                width="100%",
                mt="4",
            ),
            max_width="400px",
        ),
        open=FinanceState.delete_confirm_show,
    )


def cards_page() -> rx.Component:
    """Cards & Statements page."""
    return rx.box(
        # Delete confirmation dialog
        delete_confirm_dialog(),
        
        # Header
        rx.flex(
            rx.flex(
                rx.heading("Cards & Statements", size="7", weight="bold"),
                rx.badge(
                    FinanceState.card_count.to_string(),
                    color_scheme="indigo",
                    variant="soft",
                    size="2",
                ),
                align="center",
                gap="2",
            ),
            rx.button(
                rx.icon("refresh-cw", size=14),
                "Refresh",
                on_click=FinanceState.load_all_data,
                variant="ghost",
                size="1",
            ),
            justify="between",
            width="100%",
            align="start",
            mb="6",
        ),
        
        # Cards grid
        rx.cond(
            FinanceState.statements_with_metadata,
            rx.grid(
                rx.foreach(
                    FinanceState.statements_with_metadata,
                    statement_card,
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                gap="4",
            ),
            rx.flex(
                rx.icon("credit-card", size=48, color="var(--gray-7)"),
                rx.text("No statements imported yet", size="3", color="var(--gray-9)"),
                rx.link(
                    rx.button(
                        rx.icon("upload", size=14),
                        "Upload a Statement",
                        color_scheme="indigo",
                        size="2",
                    ),
                    href="/upload",
                ),
                direction="column",
                align="center",
                gap="4",
                padding="8",
            ),
        ),
        
        padding="6",
    )