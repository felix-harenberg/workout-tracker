"""Visual design: black, white, one blue. Same look as the blog felix-harenberg.github.io.

Tokens come from the blog's assets/css/site.css. No glass, no glow, no round corners:
thin lines separate things, blue marks only what matters (today, records, buttons, arrows).
Screen titles are the curly italic serif; workout and exercise names the wide bold sans;
dates, sets and labels the mono font.
"""

from collections.abc import Callable

import flet as ft

BG = "#141414"
TEXT = "#F4F4F1"
TEXT_MUTED = "#B9B9B6"  # running text, secondary lines
DIM = "#6F6F6C"  # small labels
LINE = "#333333"  # hairlines between rows
BLUE = "#1F5FFF"
UP_COLOR = "#3DDC84"  # ▲ more weight next time
DOWN_COLOR = "#FF5A6E"  # ▼ less weight next time
DANGER = DOWN_COLOR  # deleting is the only red action in the app

FONTS = {
    "Instrument Serif": "fonts/InstrumentSerif-Italic.ttf",
    "Archivo Expanded": "fonts/ArchivoExpanded-ExtraBold.ttf",
    "Archivo Expanded Bold": "fonts/ArchivoExpanded-Bold.ttf",
    "Inter Tight": "fonts/InterTight-Regular.ttf",
    "Inter Tight SemiBold": "fonts/InterTight-SemiBold.ttf",
    "JetBrains Mono": "fonts/JetBrainsMono-Regular.ttf",
    "JetBrains Mono Medium": "fonts/JetBrainsMono-Medium.ttf",
}
TITLE_FONT = "Instrument Serif"  # screen titles: "Workouts", "Statistik"
NAME_FONT = "Archivo Expanded"  # workout and exercise names, big numbers
STRONG_FONT = "Archivo Expanded Bold"  # names in lists, values
MEDIUM_FONT = "Inter Tight SemiBold"
MONO_FONT = "JetBrains Mono"  # labels, dates, sets
MONO_MEDIUM_FONT = "JetBrains Mono Medium"  # buttons
SIDE_PADDING = 20  # space between screen edge and content


def apply(page: ft.Page) -> None:
    page.fonts = FONTS
    page.theme_mode = ft.ThemeMode.DARK
    page.dark_theme = page.theme = ft.Theme(
        font_family="Inter Tight",
        scaffold_bgcolor=BG,
        color_scheme=ft.ColorScheme(
            primary=BLUE,
            on_primary=TEXT,
            secondary=BLUE,
            surface=BG,
            on_surface=TEXT,
            on_surface_variant=TEXT_MUTED,
            outline=LINE,
            outline_variant=LINE,
        ),
    )
    page.bgcolor = BG


async def lock_portrait(page: ft.Page) -> None:
    if page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
        await page.set_allowed_device_orientations([ft.DeviceOrientation.PORTRAIT_UP])


def view(
    route: str,
    controls: list[ft.Control],
    bar: ft.Control | None = None,
    scroll: ft.ScrollMode | None = None,
    fab: ft.Control | None = None,
    edge_to_edge: bool = False,
    **kwargs,
) -> ft.View:
    """A full-screen page on plain black: the bar, then the content.

    With `edge_to_edge`, the content uses the full screen width and brings its own side
    padding. Swipe pages need that: they must slide out over the screen edge instead of
    being cut off 20 px inside it.

    Content scrolls without a scrollbar. The floating button (`fab`) sits on top, bottom
    right, with room left below the content so it never covers the last row.
    """
    if fab is not None and scroll:  # pages that scroll themselves leave their own room
        controls = [*controls, ft.Container(height=88)]
    body = ft.Column(
        controls,
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # rows use the full width
        scroll=ft.ScrollMode.HIDDEN if scroll else None,
        expand=True,
    )
    side = 0 if edge_to_edge else SIDE_PADDING
    top = bar or ft.Container(height=8)
    if edge_to_edge:
        top = ft.Container(top, padding=ft.Padding(SIDE_PADDING, 0, SIDE_PADDING, 0))
    content = ft.Container(
        left=0,
        top=0,
        right=0,
        bottom=0,
        content=ft.SafeArea(
            ft.Container(
                ft.Column(
                    [top, body],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=ft.Padding(side, 0, side, 16),
            )
        ),
    )
    layers: list[ft.Control] = [content]
    if fab is not None:
        layers.append(ft.Container(fab, right=20, bottom=32))
    return ft.View(
        route=route,
        controls=[ft.Stack(layers, expand=True)],
        bgcolor=BG,
        padding=0,
        **kwargs,
    )


def icon_button(icon: str, on_click: Callable, tooltip: str) -> ft.Container:
    """Square outlined button for the top bar (back, edit, delete, ...)."""
    return ft.Container(
        content=ft.Icon(icon, size=20, color=TEXT),
        width=44,
        height=44,
        border=ft.Border.all(1, LINE),
        alignment=ft.Alignment.CENTER,
        tooltip=tooltip,
        on_click=on_click,
        ink=True,
    )


def top_bar(
    on_back: Callable | None,
    actions: list[ft.Control] | None = None,
    left: ft.Control | None = None,
) -> ft.Row:
    """Back arrow (or `left`, e.g. tabs) on the left, actions on the right."""
    if left is None:
        left = icon_button(ft.Icons.ARROW_BACK, on_back, "Zurück") if on_back else ft.Container()
    return ft.Row(
        [
            left,
            ft.Row(actions or [], spacing=10),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        height=64,
    )


def count_ring(number: int, caption: str) -> ft.Container:
    """Blue ring with a big number, like the post count on the blog's start page."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    str(number),
                    size=30 if number < 100 else 22,
                    color=BLUE,
                    style=ft.TextStyle(font_family=NAME_FONT, height=1),
                ),
                ft.Text(
                    caption.upper(),
                    size=8,
                    color=BLUE,
                    style=ft.TextStyle(font_family=MONO_FONT, letter_spacing=0.5),
                ),
            ],
            spacing=2,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=76,
        height=76,
        shape=ft.BoxShape.CIRCLE,
        border=ft.Border.all(3, BLUE),
        alignment=ft.Alignment.CENTER,
    )


def headline(
    text: str, overline: str = "", size: int = 64, ring: ft.Control | None = None
) -> ft.Control:
    """Screen title in the curly italic serif, like the blog hero.

    No line below: the first section's top line does that job, so there are never two.

    `ring` (see count_ring) sits on the right of the title.
    """
    title = ft.Text(
        text,
        size=size,
        color=TEXT,
        style=ft.TextStyle(font_family=TITLE_FONT, height=1.0),
    )
    head: ft.Control = title
    if ring is not None:
        # expand only inside the row: in a scrolling column it would break the layout
        head = ft.Row(
            [ft.Container(title, expand=True), ring],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    column = ft.Column([label(overline), head] if overline else [head], spacing=4)
    return ft.Container(
        column,
        padding=ft.Padding(0, 10, 0, 6),
    )


def title_headline(title: str, overline: str = "") -> ft.Control:
    """A workout or exercise name as the page title: wide bold sans in capitals."""
    column = ft.Column(
        [*([label(overline)] if overline else []), card_name(title, size=32)], spacing=6
    )
    return ft.Container(
        column,
        padding=ft.Padding(0, 14, 0, 8),
    )


def label(text: str, color: str = DIM) -> ft.Text:
    """Small mono capitals, e.g. above a title, a date or a table column."""
    return ft.Text(
        text.upper(),
        size=12,
        color=color,
        style=ft.TextStyle(font_family=MONO_FONT, letter_spacing=0.8),
    )


def meta(text: str, color: str = TEXT_MUTED) -> ft.Text:
    """Secondary line under a name in mono capitals, e.g. "6 Übungen · 25 Sätze"."""
    return ft.Text(
        text.upper(),
        size=12,
        color=color,
        style=ft.TextStyle(font_family=MONO_FONT, letter_spacing=0.4),
    )


def name(text: str, size: int = 18, color: str = TEXT) -> ft.Text:
    """Name or value in the wide bold sans, for list rows."""
    return ft.Text(
        text.upper(), size=size, color=color, style=ft.TextStyle(font_family=STRONG_FONT)
    )


def card_name(text: str, size: int = 20, color: str = TEXT) -> ft.Text:
    """Workout or exercise name: wide extra bold sans in capitals."""
    return ft.Text(
        text.upper(),
        size=size,
        color=color,
        style=ft.TextStyle(font_family=NAME_FONT, height=1.05),
    )


def muted(text: str, size: int = 17) -> ft.Text:
    return ft.Text(text, size=size, color=TEXT_MUTED)


def arrow(color: str = BLUE) -> ft.Text:
    """The blog's → at the end of a tappable row."""
    return ft.Text("→", size=22, color=color)


def chip(text: str, highlight: bool = False) -> ft.Container:
    """Square outlined box for a set, e.g. "82.5 × 8"; the PR is blue."""
    return ft.Container(
        content=ft.Text(
            text,
            size=15,
            color=BLUE if highlight else TEXT,
            style=ft.TextStyle(font_family=MONO_FONT),
        ),
        padding=ft.Padding(10, 6, 10, 6),
        border=ft.Border.all(1, BLUE if highlight else LINE),
    )


def chips(texts: list[str], highlighted: int | None = None) -> ft.Row:
    """Set chips; the one at index `highlighted` (e.g. the PR) is blue."""
    return ft.Row(
        [chip(t, highlight=i == highlighted) for i, t in enumerate(texts)],
        wrap=True,
        spacing=6,
        run_spacing=6,
    )


def section(
    content: ft.Control,
    on_click: Callable | None = None,
    highlight: bool = False,
    padding: int | ft.Padding = 16,
    border_color: str | None = None,
) -> ft.Container:
    """A block with a hairline on top, like a post row on the blog. No box around it.

    Only the vertical part of `padding` is used: content lines up with the title.
    `highlight` or `border_color` makes the top line thicker and colored.
    """
    if isinstance(padding, int):
        padding = ft.Padding(0, padding, 0, padding)
    else:
        padding = ft.Padding(0, padding.top, 0, padding.bottom)
    color = border_color or (BLUE if highlight else LINE)
    return ft.Container(
        content=content,
        padding=padding,
        border=ft.Border(top=ft.BorderSide(2 if color != LINE else 1, color)),
        on_click=on_click,
        ink=on_click is not None,
    )


def line_list(rows: list[ft.Control]) -> ft.Container:
    """Rows separated by hairlines, with a line above the first and below the last."""
    separated: list[ft.Control] = []
    for i, row in enumerate(rows):
        if i:
            separated.append(ft.Divider(height=1, thickness=1, color=LINE))
        separated.append(row)
    return ft.Container(
        ft.Column(separated, spacing=0),
        border=ft.Border(top=ft.BorderSide(1, LINE), bottom=ft.BorderSide(1, LINE)),
    )


def list_row(
    title: str,
    subtitle: ft.Control | str | None = None,
    on_click: Callable | None = None,
    trailing: ft.Control | None = None,
    color: str = TEXT,
) -> ft.Container:
    """A row in a line_list: name, small mono line below, blue arrow on the right."""
    if isinstance(subtitle, str):
        subtitle = meta(subtitle)
    texts: list[ft.Control] = [name(title, size=16, color=color)]
    if subtitle is not None:
        texts.append(subtitle)
    if trailing is None and on_click is not None:
        trailing = arrow()
    return ft.Container(
        content=ft.Row(
            [ft.Column(texts, spacing=4, expand=True), *([trailing] if trailing else [])]
        ),
        padding=ft.Padding(0, 14, 0, 14),
        on_click=on_click,
        ink=on_click is not None,
    )


def panel(content: ft.Control) -> ft.Container:
    """Fixed panel at the bottom of a screen: black with a line on top."""
    return ft.Container(
        content=content,
        padding=ft.Padding(0, 14, 0, 4),
        bgcolor=BG,
        border=ft.Border(top=ft.BorderSide(1, LINE)),
    )


def _button_text(text: str, color: str, size: int = 15) -> ft.Text:
    return ft.Text(
        text.upper(),
        size=size,
        color=color,
        style=ft.TextStyle(font_family=MONO_MEDIUM_FONT, letter_spacing=1),
    )


def primary_button(text: str, on_click: Callable, icon: str | None = None) -> ft.Container:
    """Blue block, full width and tall, easy to hit with the thumb."""
    content: list[ft.Control] = []
    if icon:
        content.append(ft.Icon(icon, color=TEXT, size=20))
    content.append(_button_text(text, TEXT, size=16))
    return ft.Container(
        content=ft.Row(content, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        bgcolor=BLUE,
        height=58,
        on_click=on_click,
        ink=True,
    )


def text_field(**kwargs) -> ft.TextField:
    """Input with a thin square border that turns blue on focus."""
    kwargs.setdefault("text_style", ft.TextStyle(size=18, font_family=MEDIUM_FONT))
    return ft.TextField(
        border_radius=0,
        border_color=LINE,
        focused_border_color=BLUE,
        cursor_color=BLUE,
        **kwargs,
    )


def fab(on_click: Callable, tooltip: str, text: str | None = None) -> ft.Container:
    """Blue square with +; with `text` a wide block, e.g. "+ ÜBUNG"."""
    if text is None:
        return ft.Container(
            content=ft.Icon(ft.Icons.ADD, color=TEXT, size=32),
            width=60,
            height=60,
            bgcolor=BLUE,
            alignment=ft.Alignment.CENTER,
            tooltip=tooltip,
            on_click=on_click,
            ink=True,
        )
    return ft.Container(
        content=ft.Row(
            [
                ft.Text("+", size=24, color=TEXT, style=ft.TextStyle(font_family=NAME_FONT)),
                _button_text(text, TEXT),
            ],
            spacing=10,
            tight=True,
        ),
        height=60,
        padding=ft.Padding(22, 0, 24, 0),
        bgcolor=BLUE,
        alignment=ft.Alignment.CENTER,
        tooltip=tooltip,
        on_click=on_click,
        ink=True,
    )


def hint_color(direction: str) -> str:
    return UP_COLOR if direction == "up" else DOWN_COLOR


def hint_glyph(direction: str, size: int = 16) -> ft.Text:
    """Green ▲ or red ▼."""
    return ft.Text("▲" if direction == "up" else "▼", size=size, color=hint_color(direction))


def secondary_button(text: str, on_click: Callable, icon: str | None = None) -> ft.Container:
    """Small blue-outlined box for side actions, e.g. "Alles übernehmen"."""
    content: list[ft.Control] = []
    if icon:
        content.append(ft.Icon(icon, color=BLUE, size=18))
    content.append(_button_text(text, BLUE, size=13))
    return ft.Container(
        content=ft.Row(content, spacing=6, tight=True),
        padding=ft.Padding(12, 8, 14, 8),
        border=ft.Border.all(1, BLUE),
        on_click=on_click,
        ink=True,
    )


def dialog_button(text: str, on_click: Callable, kind: str = "plain") -> ft.Container:
    """Equal-width dialog action. kind: "main" (blue block), "plain" (outlined),
    "danger" (red block), "danger_outline" (red outline, for delete next to Speichern)."""
    fill = {"main": BLUE, "danger": DANGER}.get(kind)
    color = {"main": TEXT, "danger": BG, "danger_outline": DANGER}.get(kind, TEXT)
    border = {"plain": TEXT_MUTED, "danger_outline": DANGER}.get(kind)
    return ft.Container(
        content=_button_text(text, color, size=14),
        expand=True,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(0, 15, 0, 15),
        bgcolor=fill,
        border=ft.Border.all(1, border) if border else None,
        on_click=on_click,
        ink=True,
    )


def name_sentence(name: str, rest: str) -> ft.Text:
    """A sentence that starts with a workout or exercise name in the wide sans."""
    return ft.Text(
        spans=[
            ft.TextSpan(
                name.upper(), style=ft.TextStyle(font_family=STRONG_FONT, size=14, color=TEXT)
            ),
            ft.TextSpan(rest, style=ft.TextStyle(size=16, color=TEXT_MUTED)),
        ]
    )


def dialog(
    kicker: str,
    title: str,
    body: list[ft.Control],
    actions: list[ft.Control],
    danger: bool = False,
) -> ft.AlertDialog:
    """Black box over the dimmed screen, like the rest of the app instead of Android's default.

    A colored line on top (red for deleting, blue otherwise), a small mono `kicker` (e.g.
    "Satz 2 · Benchpress"), the title in the curly serif, then `body` and the `actions`
    (rows of dialog_button).
    """
    accent = DANGER if danger else BLUE
    side = ft.BorderSide(1, LINE)
    card = ft.Container(
        padding=ft.Padding(20, 22, 20, 20),
        bgcolor=BG,
        border=ft.Border(top=ft.BorderSide(2, accent), left=side, right=side, bottom=side),
        content=ft.Column(
            [
                label(kicker, color=DANGER if danger else TEXT_MUTED),
                ft.Text(
                    title,
                    size=40,
                    color=TEXT,
                    style=ft.TextStyle(font_family=TITLE_FONT, height=1.0),
                ),
                *body,
                ft.Container(height=4),
                *actions,
            ],
            tight=True,
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
    )
    return ft.AlertDialog(
        modal=True,
        bgcolor=ft.Colors.TRANSPARENT,
        elevation=0,
        content_padding=0,
        inset_padding=ft.Padding(20, 24, 20, 24),
        barrier_color=ft.Colors.with_opacity(0.72, BG),
        content=card,
    )
