# Design-Vorlage

Stand: 22. Oktober 2026. Gewählt aus drei Richtungen: **dunkel, Neon-Violett, Milchglas**. Vorschau: [vorlage.html](vorlage.html) im Browser öffnen.

Ziel: Die App soll so aussehen, dass man Lust hat, ins Gym zu gehen. Inspiration: plakative Schrift und eine einzige starke Farbe (DesignInspo 1–3), Glas-Effekt (DesignInspo 4). Die App ist fest im Hochformat.

## Farben

| Token | Wert | Wofür |
| --- | --- | --- |
| `bg` | `#07060A` | Hintergrund, fast schwarz |
| `text` | `#F3EEFC` | Text |
| `text-muted` | `#F3EEFC` mit 55 % Deckkraft | Labels, Vorher-Werte |
| `violet` | `#B026FF` | Akzent: Häkchen, Speichern-Button, Leuchten |
| `violet-light` | `#D27BFF` | Akzent-Schrift (z.B. zweites Wort im Titel), mit Glow |
| `violet-deep` | `#5A1BFF` | zweiter Leucht-Fleck im Hintergrund |
| `glass` | Weiss mit 6 % Deckkraft | Karten |
| `glass-border` | Weiss mit 14 % Deckkraft | 1 px Rand der Karten |

Violett nur für Akzente und Aktionen, nie für Flächen mit Text.

## Schrift

- **Titel:** Anton, Grossbuchstaben, sehr gross (ca. 64 px), enge Zeilenhöhe. Ein Wort in `violet-light` mit Glow.
- **Alles andere:** Inter. Zahlen in Fett (800) und mit Tabellenziffern, damit Spalten sauber stehen.
- **Labels:** 10 px, Grossbuchstaben, weite Laufweite, `text-muted`.

## Bausteine

- **Hintergrund:** zwei grosse, stark verschwommene Kreise (oben rechts `violet`, unten links `violet-deep`) hinter dem Inhalt.
- **Glas-Karte:** `glass` als Füllung, 1 px `glass-border`, Hintergrund-Unschärfe ca. 18, Eckenradius 22.
- **Primär-Button:** `violet`, weisse Schrift, violetter Schatten als Leuchten, Radius 14.
- **Häkchen:** erledigt = gefüllter violetter Kreis mit Glow; offen = weisser Ring mit 40 % Deckkraft.
- **Vorbefüllte Werte** (noch nicht bestätigt): 35 % Deckkraft.

## Umsetzung in Flet

Was in der Vorschau CSS ist, gibt es in Flet so:

- Glas: `Container(bgcolor=..., border=..., border_radius=22, blur=18)`. Die Unschärfe wirkt auf das, was hinter dem Container liegt. Nur sparsam einsetzen, siehe „Glas: getestet auf dem Handy“ unten.
- Leucht-Flecken: Container mit Kreisform und starker Unschärfe in einem `Stack` hinter dem Inhalt.
- Glow: `BoxShadow` mit violetter Farbe und grossem Blur-Radius.
- Anton: TTF-Datei in die Assets legen und über `page.fonts` registrieren, damit sie offline funktioniert.
- Hochformat: `page.set_allowed_device_orientations([DeviceOrientation.PORTRAIT_UP])`, nur auf Mobilgeräten aufrufen.

## Glas: getestet auf dem Handy (26. Oktober 2026)

Test-App mit 24 scrollenden Karten und einem festen Panel unten, drei Modi verglichen:

| Modus | Ergebnis |
| --- | --- |
| Echt: Unschärfe auf allen Karten | ruckelt beim Scrollen, spürbar |
| Angedeutet: keine Unschärfe | flüssig |
| Mischung: Karten angedeutet, echte Unschärfe nur beim festen Panel | flüssig |

**Regel daraus:**

- **Alles, was scrollt** (Karten, Listen-Einträge): angedeutetes Glas ohne `blur`. Füllung als Verlauf von Weiss 11 % oben links zu Weiss 3 % unten rechts, Rand 1 px Weiss 18 %, Radius wie gehabt.
- **Echte Unschärfe** (`blur=18`) nur für feste Elemente, die sich nicht mitbewegen, z.B. das Eingabe-Panel unten im Satz-Screen. Maximal ein bis zwei pro Screen.
- **Leucht-Flecken im Hintergrund** als `RadialGradient` statt als weichgezeichnete Kreise. Das sieht gleich aus und kostet nichts.

Code der Test-App mit allen drei Modi: [glas-test/main.py](glas-test/main.py) (Funktion `style_glass`). Lief auf dem inzwischen gelöschten Branch `spike/glas-test`.
