import reflex as rx


def metric_card(
    title: str,
    value,
    subtitle: str = "",
    icon: str = "wallet",
    subtitle_color: str = "var(--gray-9)",
) -> rx.Component:
    """Metric card using Radix props for reliable styling.
    
    Args:
        title: Label for the metric
        value: The metric value (string or rx.Var)
        subtitle: Optional subtitle text
        icon: Icon name from Lucide icons
        subtitle_color: Color for subtitle text (Radix color token)
    
    Returns:
        rx.Component: A styled metric card
    """
    return rx.card(
        rx.flex(
            # Top row: icon + label
            rx.flex(
                rx.icon(icon, size=16, color="var(--accent-9)"),
                rx.text(title, size="1", weight="medium", color="var(--gray-9)"),
                align="center",
                gap="2",
            ),
            # Value
            rx.text(value, size="6", weight="bold", font="mono", trim="both"),
            # Subtitle
            rx.cond(
                subtitle != "",
                rx.text(subtitle, size="1", color=subtitle_color),
                rx.fragment(),
            ),
            direction="column",
            gap="1",
            align="start",
            width="100%",
        ),
        size="2",
        variant="surface",
    )