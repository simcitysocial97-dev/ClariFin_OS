import reflex as rx
from ..styles import CARD_STYLE, SUBHEADING_STYLE, MUTED_TEXT_STYLE


def chart_card(
    title: str,
    subtitle: str = "",
    chart: rx.Component = None,
    height: str = "h-72",
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(title, class_name=SUBHEADING_STYLE),
                rx.text(subtitle, class_name=MUTED_TEXT_STYLE),
                justify="between",
                width="100%",
                align="center",
            ),
            rx.separator(class_name="border-zinc-800 w-full"),
            rx.box(
                chart if chart is not None else rx.text("No data", class_name="text-zinc-500 text-sm"),
                class_name=f"w-full {height}",
            ),
            spacing="3",
            width="100%",
        ),
        class_name=f"{CARD_STYLE} p-6",
    )
