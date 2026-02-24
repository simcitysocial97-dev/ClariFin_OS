import reflex as rx
from .state import FinanceState
from .styles import get_theme
from .components.sidebar import sidebar
from .pages.overview import overview_page
from .pages.transactions import transactions_page
from .pages.categories import categories_page
from .pages.analytics import analytics_page
from .pages.cards import cards_page
from .pages.upload import upload_page
from .pages.import_data import import_data_page


def layout(page_content: rx.Component) -> rx.Component:
    """App shell: sidebar + main content."""
    return rx.flex(
        sidebar(),
        rx.box(
            page_content,
            class_name="flex-1 overflow-auto min-h-screen bg-zinc-950",
        ),
        class_name="flex min-h-screen bg-zinc-950",
    )


@rx.page(route="/", title="Overview — FinTrack", on_load=FinanceState.load_all_data)
def index() -> rx.Component:
    return layout(overview_page())


@rx.page(route="/transactions", title="Transactions — FinTrack", on_load=FinanceState.load_all_data)
def transactions() -> rx.Component:
    return layout(transactions_page())


@rx.page(route="/categories", title="Categories — FinTrack", on_load=FinanceState.load_all_data)
def categories() -> rx.Component:
    return layout(categories_page())


@rx.page(route="/analytics", title="Analytics — FinTrack", on_load=FinanceState.load_all_data)
def analytics() -> rx.Component:
    return layout(analytics_page())


@rx.page(route="/cards", title="Cards — FinTrack", on_load=FinanceState.load_all_data)
def cards() -> rx.Component:
    return layout(cards_page())


@rx.page(route="/upload", title="Upload — FinTrack", on_load=FinanceState.load_all_data)
def upload() -> rx.Component:
    return layout(upload_page())


@rx.page(route="/import", title="Import — FinTrack", on_load=FinanceState.load_all_data)
def import_data() -> rx.Component:
    return layout(import_data_page())


app = rx.App(
    theme=get_theme(),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap",
    ],
)
