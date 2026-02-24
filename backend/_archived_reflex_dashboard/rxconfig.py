import reflex as rx

config = rx.Config(
    app_name="finance_dashboard",
    title="FinTrack",
    disable_plugins=['reflex.plugins.sitemap.SitemapPlugin'],
    tailwind={
        "content": ["./finance_dashboard/**/*.py"],
        "darkMode": "class",
        "theme": {
            "extend": {},
        },
    },
)