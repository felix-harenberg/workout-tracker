# Throwaway spike: does the style-B glass effect run smoothly on the phone?
# Not the real app. Lives only on branch spike/glas-test.
#
# Three modes to compare on the device:
#   Echt        - real backdrop blur on every card and on the bottom panel
#   Angedeutet  - no blur anywhere, glass is faked with fill, border and gradient
#   Mischung    - faked glass on scrolling cards, real blur only on the fixed panel

import flet as ft

BG = "#07060A"
TEXT = "#F3EEFC"
MUTED = "#8CF3EEFC"  # text at 55 %
VIOLET = "#B026FF"
VIOLET_LIGHT = "#D27BFF"
VIOLET_DEEP = "#5A1BFF"
GLASS = "#0FFFFFFF"  # white at 6 %
GLASS_BORDER = "#24FFFFFF"  # white at 14 %
FAKE_BORDER = "#2EFFFFFF"  # white at 18 %, a bit brighter to sell the glass edge
BLUR = 18

FAKE_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment.TOP_LEFT,
    end=ft.Alignment.BOTTOM_RIGHT,
    colors=["#1CFFFFFF", "#08FFFFFF"],  # white 11 % -> 3 %
)

MODES = ["Echt", "Angedeutet", "Mischung"]


def glow(color: str, size: int, **position: int) -> ft.Container:
    """Soft colored light spot for the background."""
    return ft.Container(
        width=size,
        height=size,
        gradient=ft.RadialGradient(colors=[color, "#00000000"], radius=0.5),
        **position,
    )


def style_glass(box: ft.Container, real: bool) -> None:
    """Switch a container between real blurred glass and faked glass."""
    if real:
        box.blur = BLUR
        box.bgcolor = GLASS
        box.gradient = None
        box.border = ft.Border.all(1, GLASS_BORDER)
    else:
        box.blur = None
        box.bgcolor = None
        box.gradient = FAKE_GRADIENT
        box.border = ft.Border.all(1, FAKE_BORDER)


def main(page: ft.Page) -> None:
    page.title = "Glas-Test"
    page.bgcolor = BG
    page.padding = 0

    cards: list[ft.Container] = []

    def glass(content: ft.Control) -> ft.Container:
        card = ft.Container(
            content=content,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=20,
        )
        cards.append(card)
        return card

    def set_row(n: int, kg: str, reps: int) -> ft.Control:
        return ft.Row(
            [
                ft.Text(str(n), size=17, weight=ft.FontWeight.W_600, color=TEXT, width=30),
                ft.Text(f"{kg} kg", size=17, weight=ft.FontWeight.W_600, color=TEXT, expand=True),
                ft.Text(f"× {reps}", size=17, weight=ft.FontWeight.W_600, color=TEXT),
                ft.Container(
                    width=28,
                    height=28,
                    border_radius=14,
                    bgcolor=VIOLET,
                    shadow=ft.BoxShadow(blur_radius=14, color=VIOLET),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("✓", color="#FFFFFF", size=14),
                ),
            ]
        )

    def field(label: str, value: str) -> ft.Control:
        return ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=14,
            bgcolor="#14FFFFFF",
            border=ft.Border.all(1, "#2EFFFFFF"),
            content=ft.Column(
                [
                    ft.Text(label, size=10, color=MUTED, weight=ft.FontWeight.W_600),
                    ft.Text(value, size=28, color=TEXT, weight=ft.FontWeight.W_800),
                ],
                spacing=0,
            ),
        )

    # Fixed bottom panel, like the set input sheet. Cards scroll underneath it.
    panel = ft.Container(
        left=12,
        right=12,
        bottom=16,
        padding=14,
        border_radius=22,
        content=ft.Row(
            [
                field("KG", "82.5"),
                field("WDH", "7"),
                ft.Container(
                    width=60,
                    height=60,
                    border_radius=14,
                    bgcolor=VIOLET,
                    shadow=ft.BoxShadow(blur_radius=24, color="#99B026FF"),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("✓", color="#FFFFFF", size=26),
                ),
            ],
            spacing=10,
        ),
    )

    exercises = ["Bankdrücken", "Schulterdrücken", "Dips", "Kniebeugen", "Kreuzheben", "Klimmzüge"]
    items: list[ft.Control] = [
        ft.Text("GLAS", size=60, weight=ft.FontWeight.W_900, color=TEXT),
        ft.Text(
            "TEST",
            size=60,
            weight=ft.FontWeight.W_900,
            color=VIOLET_LIGHT,
            style=ft.TextStyle(shadow=ft.BoxShadow(blur_radius=18, color=VIOLET)),
        ),
    ]
    for _ in range(4):
        for name in exercises:
            items.append(
                glass(
                    ft.Column(
                        [
                            ft.Text(name.upper(), size=20, weight=ft.FontWeight.W_900, color=TEXT),
                            *[set_row(i + 1, "82.5", 8 - i) for i in range(3)],
                        ],
                        spacing=6,
                    )
                )
            )

    status = ft.Text("", color=MUTED, size=12)
    mode_buttons: list[ft.Container] = []

    def apply(mode: str) -> None:
        for card in cards:
            style_glass(card, real=mode == "Echt")
        style_glass(panel, real=mode in ("Echt", "Mischung"))
        blurred = (len(cards) if mode == "Echt" else 0) + (1 if mode != "Angedeutet" else 0)
        status.value = f"{mode}: {blurred} Elemente mit echter Unschärfe"
        for button in mode_buttons:
            on = button.data == mode
            button.bgcolor = VIOLET if on else "#12FFFFFF"
            button.shadow = ft.BoxShadow(blur_radius=16, color="#99B026FF") if on else None
        page.update()

    for mode in MODES:
        mode_buttons.append(
            ft.Container(
                data=mode,
                expand=True,
                height=40,
                border_radius=14,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(mode, color=TEXT, size=13, weight=ft.FontWeight.W_700),
                on_click=lambda e: apply(e.control.data),
            )
        )
    items.insert(2, ft.Row(mode_buttons, spacing=6))
    items.insert(3, status)

    page.add(
        ft.Stack(
            [
                ft.Container(bgcolor=BG, left=0, top=0, right=0, bottom=0),
                glow(VIOLET, 420, right=-160, top=-140),
                glow(VIOLET_DEEP, 380, left=-170, bottom=40),
                ft.ListView(
                    items,
                    spacing=12,
                    # Bottom padding so the last card can scroll out from under the panel.
                    padding=ft.Padding.only(left=16, top=40, right=16, bottom=130),
                    left=0,
                    top=0,
                    right=0,
                    bottom=0,
                ),
                panel,
            ],
            expand=True,
        )
    )
    apply("Echt")


if __name__ == "__main__":
    ft.run(main)
