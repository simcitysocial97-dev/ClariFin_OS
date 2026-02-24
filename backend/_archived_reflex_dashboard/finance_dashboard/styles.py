import reflex as rx

# Color palette — premium dark fintech theme
COLORS = {
    "bg_primary": "#09090B",
    "bg_card": "#18181B",
    "bg_card_hover": "#27272A",
    "bg_elevated": "#1E1E24",
    "border": "rgba(63, 63, 70, 0.5)",
    "border_hover": "rgba(99, 102, 241, 0.3)",
    "text_primary": "#FAFAFA",
    "text_secondary": "#A1A1AA",
    "text_muted": "#71717A",
    "accent": "#6366F1",
    "accent_hover": "#818CF8",
    "accent_subtle": "rgba(99, 102, 241, 0.1)",
    "green": "#22C55E",
    "green_subtle": "rgba(34, 197, 94, 0.1)",
    "red": "#EF4444",
    "red_subtle": "rgba(239, 68, 68, 0.1)",
    "amber": "#F59E0B",
    "cyan": "#06B6D4",
}

CHART_COLORS = [
    "#6366F1", "#8B5CF6", "#EC4899", "#F59E0B",
    "#22C55E", "#06B6D4", "#F97316", "#14B8A6",
    "#EF4444", "#A78BFA", "#34D399", "#FBBF24",
]

CARD_STYLE = (
    "bg-zinc-900/80 backdrop-blur-xl border border-zinc-700/50 "
    "rounded-xl shadow-lg"
)

CARD_HOVER_STYLE = (
    "bg-zinc-900/80 backdrop-blur-xl border border-zinc-700/50 "
    "rounded-xl shadow-lg hover:shadow-xl hover:shadow-indigo-500/5 "
    "hover:border-indigo-500/30 transition-all duration-200"
)

METRIC_CARD_STYLE = (
    "bg-gradient-to-br from-zinc-900 to-zinc-800/80 "
    "border border-zinc-700/30 rounded-xl p-6 "
    "hover:shadow-xl hover:shadow-indigo-500/5 transition-all duration-200"
)

PAGE_CONTAINER_STYLE = "p-8 min-h-screen bg-zinc-950"

HEADING_STYLE = "text-2xl font-bold text-zinc-50 tracking-tight"

SUBHEADING_STYLE = "text-lg font-semibold text-zinc-200"

LABEL_STYLE = "text-xs font-medium text-zinc-400 uppercase tracking-wider"

AMOUNT_STYLE = "text-2xl font-bold text-zinc-50 font-mono tracking-tight"

AMOUNT_SMALL_STYLE = "text-sm font-semibold text-zinc-50 font-mono"

MUTED_TEXT_STYLE = "text-sm text-zinc-500"

SEPARATOR_STYLE = "border-zinc-800 my-6"

SIDEBAR_STYLE = (
    "w-64 min-h-screen bg-zinc-900/50 backdrop-blur-xl "
    "border-r border-zinc-800/50 p-4 flex flex-col"
)

SIDEBAR_ITEM_STYLE = (
    "flex items-center gap-3 px-3 py-2.5 rounded-lg "
    "text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50 "
    "transition-all duration-150 cursor-pointer text-sm font-medium w-full"
)

SIDEBAR_ITEM_ACTIVE_STYLE = (
    "flex items-center gap-3 px-3 py-2.5 rounded-lg "
    "text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 "
    "text-sm font-medium w-full"
)

# Bank badge colors
BANK_COLORS = {
    "HDFC Bank": "blue",
    "ICICI Bank": "orange",
    "Axis Bank": "red",
    "SBI Card": "blue",
    "IDFC First Bank": "green",
    "IndusInd Bank": "purple",
}


def get_theme() -> rx.Component:
    return rx.theme(
        appearance="inherit",  # Now respects toggle
        accent_color="indigo",
        gray_color="slate",
        radius="medium",
        scaling="100%",
    )
