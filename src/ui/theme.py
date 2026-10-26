"""Visual design: dark, neon violet, glass.

Tokens and rules come from docs/design/design.md on the ideas/design branch. Glass follows
the rule tested on the phone: anything that scrolls gets the suggested glass (gradient fill
and border, no blur); real blur only on fixed panels, at most one or two per screen.
"""

from collections.abc import Callable

import flet as ft

BG = "#07060A"
TEXT = "#F3EEFC"
TEXT_MUTED = ft.Colors.with_opacity(0.55, TEXT)
VIOLET = "#B026FF"
VIOLET_LIGHT = "#D27BFF"
VIOLET_DEEP = "#5A1BFF"
GLASS_BORDER = ft.Colors.with_opacity(0.18, ft.Colors.WHITE)

FONTS = {
    "Anton": "fonts/Anton-Regular.ttf",
    "Inter": "fonts/Inter-Regular.ttf",
    "Inter SemiBold": "fonts/Inter-SemiBold.ttf",
    "Inter ExtraBold": "fonts/Inter-ExtraBold.ttf",
}
TITLE_FONT = "Anton"
STRONG_FONT = "Inter ExtraBold"  # names and numbers
MEDIUM_FONT = "Inter SemiBold"


def apply(page: ft.Page) -> None:
    page.fonts = FONTS
    page.theme_mode = ft.ThemeMode.DARK
    page.dark_theme = page.theme = ft.Theme(
        font_family="Inter",
        scaffold_bgcolor=BG,
        color_scheme=ft.ColorScheme(
            primary=VIOLET,
            on_primary=ft.Colors.WHITE,
            secondary=VIOLET_LIGHT,
            surface=BG,
            on_surface=TEXT,
            on_surface_variant=TEXT_MUTED,
            outline=GLASS_BORDER,
            outline_variant=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        ),
    )
    page.bgcolor = BG


async def lock_portrait(page: ft.Page) -> None:
    if page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
        await page.set_allowed_device_orientations([ft.DeviceOrientation.PORTRAIT_UP])


def view(
    route: str,
    controls: list[ft.Control],
    scroll: ft.ScrollMode | None = None,
    **kwargs,
) -> ft.View:
    """A screen on the dark background with a violet glow in the top right corner.

    The glow is its own layer behind the content: a gradient in `View.decoration` did not
    show up on the phone, gradients on containers do. Content scrolls without a scrollbar,
    which would otherwise cut into the cards.
    """
    glow = ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        gradient=ft.RadialGradient(
            center=ft.Alignment(1.0, -1.0),
            radius=1.3,
            colors=[
                ft.Colors.with_opacity(0.45, VIOLET),
                ft.Colors.with_opacity(0.12, VIOLET_DEEP),
                ft.Colors.with_opacity(0, BG),
            ],
            stops=[0, 0.45, 1],
        ),
    )
    content = ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        padding=ft.Padding(20, 8, 20, 24),
        content=ft.Column(
            controls,
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # cards use the full width
            scroll=ft.ScrollMode.HIDDEN if scroll else None,
        ),
    )
    return ft.View(
        route=route,
        controls=[ft.Stack([glow, content], expand=True)],
        bgcolor=BG,
        padding=0,
        **kwargs,
    )


def app_bar(actions: list[ft.Control] | None = None) -> ft.AppBar:
    """Transparent bar for the back arrow and actions; the title is a big headline instead."""
    return ft.AppBar(bgcolor=ft.Colors.TRANSPARENT, actions=actions or [])


def headline(text: str, accent: str = "", overline: str = "", size: int = 60) -> ft.Control:
    """Big Anton title in capitals on one line; `accent` follows directly and glows violet.

    headline("Work", "outs") gives WORKOUTS with OUTS in violet. Long titles wrap.
    """
    glow = ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.8, VIOLET))
    base = ft.TextStyle(font_family=TITLE_FONT, size=size, height=1.0, color=TEXT)
    title = ft.Text(
        spans=[
            ft.TextSpan(text.upper(), style=base),
            ft.TextSpan(
                accent.upper(),
                style=ft.TextStyle(
                    font_family=TITLE_FONT, size=size, height=1.0, color=VIOLET_LIGHT, shadow=glow
                ),
            ),
        ]
    )
    if not overline:
        return title
    return ft.Column([label(overline), title], spacing=4)


def title_headline(title: str, overline: str = "") -> ft.Control:
    """A workout or exercise name as a headline; the last word glows violet."""
    *rest, last = title.split() or [""]
    return headline(" ".join(rest) + " " if rest else "", last, overline=overline, size=52)


def label(text: str, color: str = TEXT_MUTED) -> ft.Text:
    """Small capitals with wide spacing, e.g. above a title or a number."""
    return ft.Text(
        text.upper(),
        size=13,
        color=color,
        style=ft.TextStyle(font_family=MEDIUM_FONT, letter_spacing=1.6),
    )


def name(text: str, size: int = 24, color: str = TEXT) -> ft.Text:
    """Workout or exercise name in bold."""
    return ft.Text(text, size=size, color=color, style=ft.TextStyle(font_family=STRONG_FONT))


def muted(text: str, size: int = 17) -> ft.Text:
    return ft.Text(text, size=size, color=TEXT_MUTED)


def chip(text: str, highlight: bool = False) -> ft.Container:
    """Compact pill for a set, e.g. "82.5 × 8"."""
    return ft.Container(
        content=ft.Text(
            text,
            size=16,
            color=TEXT,
            style=ft.TextStyle(font_family=STRONG_FONT),
        ),
        padding=ft.Padding(12, 6, 12, 6),
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.25, VIOLET)
        if highlight
        else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        border=ft.Border.all(1, VIOLET if highlight else GLASS_BORDER),
    )


def chips(texts: list[str]) -> ft.Row:
    return ft.Row([chip(t) for t in texts], wrap=True, spacing=8, run_spacing=8)


def glass_card(
    content: ft.Control,
    on_click: Callable | None = None,
    highlight: bool = False,
    padding: int = 16,
) -> ft.Container:
    """Suggested glass without blur, safe to use in scrolling lists."""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=22,
        border=ft.Border.all(1, VIOLET if highlight else GLASS_BORDER),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                ft.Colors.with_opacity(
                    0.16 if highlight else 0.11, VIOLET if highlight else ft.Colors.WHITE
                ),
                ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
            ],
        ),
        shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.35, VIOLET))
        if highlight
        else None,
        on_click=on_click,
        ink=on_click is not None,
    )


def glass_panel(content: ft.Control) -> ft.Container:
    """Real glass with blur. Only for fixed panels that do not scroll."""
    return ft.Container(
        content=content,
        padding=16,
        border_radius=22,
        border=ft.Border.all(1, GLASS_BORDER),
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        blur=18,
    )


def primary_button(text: str, on_click: Callable, icon: str | None = None) -> ft.Container:
    """Violet button with a glow, full width, easy to hit with the thumb."""
    content: list[ft.Control] = []
    if icon:
        content.append(ft.Icon(icon, color=ft.Colors.WHITE, size=20))
    content.append(
        ft.Text(text, color=ft.Colors.WHITE, size=16, style=ft.TextStyle(font_family=STRONG_FONT))
    )
    return ft.Container(
        content=ft.Row(content, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        bgcolor=VIOLET,
        border_radius=14,
        padding=ft.Padding(0, 16, 0, 16),
        shadow=ft.BoxShadow(blur_radius=22, color=ft.Colors.with_opacity(0.55, VIOLET)),
        on_click=on_click,
        ink=True,
    )


def text_field(**kwargs) -> ft.TextField:
    """Input on a faint glass fill with a violet focus border."""
    return ft.TextField(
        filled=True,
        fill_color=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
        border_radius=14,
        border_color=GLASS_BORDER,
        focused_border_color=VIOLET,
        **kwargs,
    )


def fab(on_click: Callable, tooltip: str) -> ft.FloatingActionButton:
    return ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        tooltip=tooltip,
        bgcolor=VIOLET,
        foreground_color=ft.Colors.WHITE,
        on_click=on_click,
    )
