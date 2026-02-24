import reflex as rx
from ..state import FinanceState


NAV_ITEMS = [
    ("/", "layout-dashboard", "Overview"),
    ("/transactions", "receipt", "Transactions"),
    ("/categories", "pie-chart", "Categories"),
    ("/analytics", "trending-up", "Analytics"),
    ("/cards", "credit-card", "Cards"),
    ("/upload", "upload", "Upload"),
    ("/import", "file-spreadsheet", "Import"),
]


def nav_item(href: str, icon: str, label: str) -> rx.Component:
    """Navigation item with active state highlighting using Radix props."""
    is_active = rx.State.router.page.path == href
    return rx.link(
        rx.flex(
            rx.icon(icon, size=16),
            rx.text(label, size="2", weight="medium"),
            align="center",
            gap="2",
            padding="2",
            border_radius="var(--radius-2)",
            width="100%",
            bg=rx.cond(is_active, "var(--accent-3)", "transparent"),
            color=rx.cond(is_active, "var(--accent-11)", "var(--gray-11)"),
            _hover={
                "bg": rx.cond(is_active, "var(--accent-3)", "var(--gray-3)"),
                "color": rx.cond(is_active, "var(--accent-11)", "var(--gray-12)"),
            },
        ),
        href=href,
        underline="none",
        width="100%",
    )


def color_picker() -> rx.Component:
    """Color picker for new member."""
    return rx.grid(
        rx.foreach(
            FinanceState.MEMBER_COLORS,
            lambda color: rx.box(
                width="24px",
                height="24px",
                border_radius="4px",
                background=color,
                cursor="pointer",
                border=rx.cond(
                    FinanceState.new_member_color == color,
                    "2px solid var(--gray-12)",
                    "2px solid transparent",
                ),
                on_click=lambda: FinanceState.set_new_member_color(color),
            ),
        ),
        columns="4",
        gap="2",
    )


def add_member_dialog() -> rx.Component:
    """Dialog for adding a new family member."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(
                rx.flex(
                    rx.icon("user-plus", size=18, color="var(--accent-9)"),
                    rx.text("Add Family Member", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
            ),
            rx.alert_dialog.description(
                rx.flex(
                    rx.text("Name", size="2", weight="medium"),
                    rx.input(
                        placeholder="e.g., Spouse, Child, Parent",
                        value=FinanceState.new_member_name,
                        on_change=FinanceState.set_new_member_name,
                        size="2",
                    ),
                    rx.text("Color", size="2", weight="medium", margin_top="3"),
                    color_picker(),
                    direction="column",
                    gap="2",
                    width="100%",
                ),
            ),
            rx.flex(
                rx.button(
                    "Cancel",
                    on_click=FinanceState.close_add_member_dialog,
                    variant="soft",
                    size="2",
                ),
                rx.button(
                    rx.icon("plus", size=14),
                    "Add Member",
                    on_click=FinanceState.add_new_member,
                    variant="solid",
                    color_scheme="indigo",
                    size="2",
                    is_disabled=FinanceState.new_member_name == "",
                ),
                gap="3",
                justify="end",
                width="100%",
                margin_top="4",
            ),
            max_width="320px",
        ),
        open=FinanceState.show_add_member_dialog,
    )


def sidebar() -> rx.Component:
    """Compact sidebar with brand, navigation, member selector, and controls."""
    return rx.box(
        # Add member dialog
        add_member_dialog(),
        
        rx.flex(
            # ── Brand Section ─────────────────────────────────────
            rx.flex(
                rx.flex(
                    rx.icon("indian-rupee", size=20, color="var(--accent-9)"),
                    rx.text("FinTrack", size="4", weight="bold"),
                    align="center",
                    gap="2",
                ),
                rx.text("Personal Finance", size="1", color="var(--gray-9)"),
                direction="column",
                gap="0",
            ),
            rx.separator(size="3", margin_top="3", margin_bottom="3"),
            
            # ── Navigation Section ─────────────────────────────────
            rx.flex(
                *[nav_item(href, icon, label) for href, icon, label in NAV_ITEMS],
                direction="column",
                gap="1",
                width="100%",
            ),
            
            rx.separator(size="3", margin_top="3", margin_bottom="3"),
            
            # ── Member Selector Section ───────────────────────────
            rx.flex(
                rx.flex(
                    rx.text("Member", size="1", weight="medium", color="var(--gray-9)"),
                    rx.flex(
                        rx.select(
                            FinanceState.available_members,
                            value=FinanceState.selected_member,
                            on_change=FinanceState.set_selected_member,
                            size="1",
                            width="100%",
                        ),
                        rx.button(
                            rx.icon("plus", size=12),
                            variant="ghost",
                            size="1",
                            color_scheme="indigo",
                            on_click=FinanceState.open_add_member_dialog,
                            padding="1",
                        ),
                        align="center",
                        gap="1",
                        width="100%",
                    ),
                    direction="column",
                    gap="1",
                    width="100%",
                ),
                width="100%",
            ),
            
            # ── Spacer ────────────────────────────────────────────
            rx.spacer(),
            
            # ── Bottom Section ───────────────────────────────────
            rx.separator(size="3", margin_top="3", margin_bottom="3"),
            rx.flex(
                rx.flex(
                    rx.color_mode.button(size="1"),
                    rx.button(
                        rx.icon("refresh-cw", size=12),
                        variant="ghost",
                        size="1",
                        on_click=FinanceState.load_all_data,
                        padding="1",
                    ),
                    gap="1",
                    align="center",
                ),
                rx.flex(
                    rx.text(
                        f"{FinanceState.transaction_count} txns",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    rx.text("•", size="1", color="var(--gray-9)"),
                    rx.text(
                        f"{FinanceState.bank_count} banks",
                        size="1",
                        color="var(--gray-9)",
                    ),
                    gap="1",
                    align="center",
                ),
                direction="column",
                gap="1",
                width="100%",
            ),
            
            direction="column",
            height="100%",
            padding="3",
        ),
        width="200px",
        min_height="100vh",
        max_height="100vh",
        bg="var(--gray-1)",
        border_right="1px solid var(--gray-4)",
        overflow="auto",
    )