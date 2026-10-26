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
UP_COLOR = "#3DDC84"  # ▲ more weight next time
DOWN_COLOR = "#FF5A6E"  # ▼ less weight next time

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


def _glow(center: ft.Alignment, radius: float, color: str, opacity: float) -> ft.Container:
    return ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        gradient=ft.RadialGradient(
            center=center,
            radius=radius,
            colors=[ft.Colors.with_opacity(opacity, color), ft.Colors.with_opacity(0, color)],
        ),
    )


def view(
    route: str,
    controls: list[ft.Control],
    bar: ft.Control | None = None,
    scroll: ft.ScrollMode | None = None,
    **kwargs,
) -> ft.View:
    """A full-screen page: glow spots top right and bottom left, then the bar and the content.

    The glow sits in its own layers behind everything, including the bar, so there is no
    edge below the bar (a Flet AppBar paints its own background, and a gradient in
    `View.decoration` did not render on the phone). Content scrolls without a scrollbar,
    which would otherwise cut into the cards.
    """
    body = ft.Column(
        controls,
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # cards use the full width
        scroll=ft.ScrollMode.HIDDEN if scroll else None,
        expand=True,
    )
    content = ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        content=ft.SafeArea(
            ft.Container(
                ft.Column(
                    [bar or ft.Container(height=8), body],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=ft.Padding(20, 0, 20, 16),
            )
        ),
    )
    return ft.View(
        route=route,
        controls=[
            ft.Stack(
                [
                    _glow(ft.Alignment(1.0, -1.0), 1.3, VIOLET, 0.45),
                    _glow(ft.Alignment(-1.0, 1.0), 1.2, VIOLET_DEEP, 0.30),
                    content,
                ],
                expand=True,
            )
        ],
        bgcolor=BG,
        padding=0,
        **kwargs,
    )


def top_bar(on_back: Callable | None, actions: list[ft.Control] | None = None) -> ft.Row:
    """Back arrow on the left (if `on_back`), actions on the right. Lives inside the glow."""
    return ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=on_back, tooltip="Zurück")
            if on_back
            else ft.Container(),
            ft.Row(actions or [], spacing=0),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        height=56,
    )


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
    border_color: str | None = None,
) -> ft.Container:
    """Suggested glass without blur, safe to use in scrolling lists."""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=22,
        border=ft.Border.all(1, border_color or (VIOLET if highlight else GLASS_BORDER)),
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


def hint_color(direction: str) -> str:
    return UP_COLOR if direction == "up" else DOWN_COLOR


def hint_glyph(direction: str, size: int = 16) -> ft.Text:
    """Green ▲ or red ▼."""
    return ft.Text("▲" if direction == "up" else "▼", size=size, color=hint_color(direction))
