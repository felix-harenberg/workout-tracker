# Throwaway spike: does the style-B glass effect run smoothly on the phone?
# Not the real app. Lives only on branch spike/glas-test.

import flet as ft

BG = "#07060A"
TEXT = "#F3EEFC"
MUTED = "#8CF3EEFC"  # text at 55 %
VIOLET = "#B026FF"
VIOLET_LIGHT = "#D27BFF"
VIOLET_DEEP = "#5A1BFF"
GLASS = "#0FFFFFFF"  # white at 6 %
GLASS_BORDER = "#24FFFFFF"  # white at 14 %
BLUR = 18


def glow(color: str, size: int, **position: int) -> ft.Container:
    """Soft colored light spot for the background."""
    return ft.Container(
        width=size,
        height=size,
        gradient=ft.RadialGradient(colors=[color, "#00000000"], radius=0.5),
        **position,
    )


def main(page: ft.Page) -> None:
    page.title = "Glas-Test"
    page.bgcolor = BG
    page.padding = 0

    cards: list[ft.Container] = []

    def glass(content: ft.Control) -> ft.Container:
        card = ft.Container(
            content=content,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            bgcolor=GLASS,
            border=ft.Border.all(1, GLASS_BORDER),
            border_radius=20,
            blur=BLUR,
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

    status = ft.Text(f"Unschärfe an ({len(cards)} Glas-Karten)", color=MUTED, size=12)

    def toggle(e: ft.Event) -> None:
        on = e.control.value
        for card in cards:
            card.blur = BLUR if on else None
        status.value = f"Unschärfe {'an' if on else 'aus'} ({len(cards)} Glas-Karten)"
        page.update()

    switch = ft.Switch(value=True, active_color=VIOLET, on_change=toggle)
    items.insert(2, ft.Row([switch, status]))

    page.add(
        ft.Stack(
            [
                ft.Container(bgcolor=BG, left=0, top=0, right=0, bottom=0),
                glow(VIOLET, 420, right=-160, top=-140),
                glow(VIOLET_DEEP, 380, left=-170, bottom=40),
                ft.ListView(
                    items,
                    spacing=12,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=40),
                    left=0,
                    top=0,
                    right=0,
                    bottom=0,
                ),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
