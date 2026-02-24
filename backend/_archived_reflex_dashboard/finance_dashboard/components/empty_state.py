import reflex as rx


def empty_state(
    icon: str = "inbox",
    title: str = "No data found",
    description: str = "",
) -> rx.Component:
    return rx.vstack(
        rx.icon(icon, size=48, class_name="text-zinc-700"),
        rx.text(title, class_name="text-zinc-400 font-medium text-base"),
        rx.text(description, class_name="text-zinc-600 text-sm text-center max-w-xs") if description else rx.fragment(),
        spacing="3",
        align="center",
        justify="center",
        class_name="py-16 w-full",
    )
