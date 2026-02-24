import reflex as rx
from ..state import FinanceState
from ..styles import CARD_STYLE


def filter_bar() -> rx.Component:
    input_cls = (
        "bg-zinc-800 border border-zinc-700 text-zinc-50 rounded-lg px-3 py-2 "
        "text-sm focus:border-indigo-500 focus:outline-none w-full"
    )
    select_cls = (
        "bg-zinc-800 border border-zinc-700 text-zinc-50 rounded-lg px-3 py-2 "
        "text-sm focus:border-indigo-500 focus:outline-none"
    )
    return rx.box(
        rx.flex(
            # Search
            rx.box(
                rx.hstack(
                    rx.icon("search", size=14, class_name="text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2"),
                    rx.input(
                        placeholder="Search transactions...",
                        value=FinanceState.search_query,
                        on_change=FinanceState.set_search,
                        class_name="bg-zinc-800 border border-zinc-700 text-zinc-50 rounded-lg pl-9 pr-3 py-2 text-sm focus:border-indigo-500 focus:outline-none w-full",
                    ),
                    class_name="relative w-full",
                    spacing="0",
                ),
                class_name="flex-1 min-w-48",
            ),
            # Bank filter
            rx.select(
                FinanceState.available_banks,
                value=FinanceState.selected_bank,
                on_change=FinanceState.set_bank_filter,
                placeholder="Bank",
                class_name=select_cls,
            ),
            # Category filter
            rx.select(
                FinanceState.available_categories,
                value=FinanceState.selected_category,
                on_change=FinanceState.set_category_filter,
                placeholder="Category",
                class_name=select_cls,
            ),
            # Type filter
            rx.select(
                ["All", "debit", "credit"],
                value=FinanceState.selected_type,
                on_change=FinanceState.set_type_filter,
                placeholder="Type",
                class_name=select_cls,
            ),
            # Amount range
            rx.hstack(
                rx.input(
                    placeholder="Min ₹",
                    value=FinanceState.min_amount_str,
                    on_change=FinanceState.set_min_amount,
                    class_name="bg-zinc-800 border border-zinc-700 text-zinc-50 rounded-lg px-3 py-2 text-sm w-24 focus:border-indigo-500 focus:outline-none",
                ),
                rx.input(
                    placeholder="Max ₹",
                    value=FinanceState.max_amount_str,
                    on_change=FinanceState.set_max_amount,
                    class_name="bg-zinc-800 border border-zinc-700 text-zinc-50 rounded-lg px-3 py-2 text-sm w-24 focus:border-indigo-500 focus:outline-none",
                ),
                spacing="2",
            ),
            # Clear button
            rx.button(
                rx.icon("x", size=14),
                "Clear",
                on_click=FinanceState.clear_filters,
                class_name="bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-50 border border-zinc-700 rounded-lg px-3 py-2 text-sm flex items-center gap-1 transition-colors",
            ),
            wrap="wrap",
            gap="3",
            align="center",
        ),
        class_name=f"{CARD_STYLE} p-4",
    )
