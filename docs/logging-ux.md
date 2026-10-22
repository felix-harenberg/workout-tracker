# Logging-UX: Leitfaden für das Eintragen und Bearbeiten

Stand: 22. Oktober 2026. Grundlage: wie Strong, Hevy, StrengthLog, Setgraph und Hyrox-Apps (RunStation, Hyro, Sweat) das Loggen lösen, dazu allgemeine Input-UX-Richtlinien (NN/g, Material, Shopify).

## Der Kern in einem Satz

**Die schnellste Eingabe ist keine Eingabe:** Die App schlägt den Wert vor (letztes Mal oder voriger Satz), und du bestätigst mit einem Tap. Tippen ist nur für Abweichungen da, ±-Buttons nur für kleine Korrekturen.

## Was sich bewährt hat

### 1. Vorbefüllen statt Eintippen

- Jeder neue Satz ist mit dem gleichnamigen Satz vom letzten Mal vorbefüllt. Gibt es den nicht, wird der vorige Satz von heute übernommen. Hevy und Strong zeigen dafür eine Spalte **"Vorher"** neben jedem Satz, und ein Tap darauf übernimmt den Wert. RepCount befüllt komplett vor.
- Der Normalfall im Gym ist "gleich wie letztes Mal" oder "+2.5 kg". Für diesen Fall muss es **ein Tap** sein.
- Status bei uns: `suggest_next_set` macht genau das schon. ✅

### 2. Satz-Tabelle statt Einzelformular

Strong und Hevy zeigen pro Übung eine kompakte Tabelle, eine Zeile pro Satz:

```
Satz | Vorher     | kg    | Wdh | ✓
 1   | 80 × 8     | [80 ] | [8] | ✓
 2   | 80 × 8     | [80 ] | [8] | ○
 3   | 80 × 6     | [   ] | [ ] | ○
          + Satz hinzufügen
```

- Man sieht sofort, was noch kommt und was letztes Mal war.
- Bearbeiten heisst: direkt in die Zeile tippen. Kein Dialog.
- Bei uns: Die Verlaufszeile oben ("Letztes Mal: …") liefert die Info, aber nicht pro Satz. Bearbeitet wird per Dialog. Das funktioniert, ist aber pro Korrektur 2 bis 3 Taps mehr. Inline-Editing ist das Ziel, sobald Phase 2 "Workout bearbeiten" drankommt.

### 3. Hybrid-Eingabe: Ziffernblock plus ±-Buttons

| Methode | Gut für | Schlecht für |
| --- | --- | --- |
| Ziffernblock (Numpad) | neue Werte, grosse Sprünge (60 → 100 kg) | kleine Korrekturen auf dem Handy, fehleranfällig |
| ±-Stepper | ±2.5 kg, ±1 Wdh | grosse Bereiche (40 Taps von 0 auf 100 kg) |
| Slider | grobe Einstellungen ohne exakten Wert | **Gewicht/Wdh: ungeeignet** |
| Scroll-Rad (Picker) | kleine, feste Auswahl | Gewicht, lange Dauern (alle bekannten Beschwerden betreffen das) |

Empfehlung:

- **Primär das Numpad** (`KeyboardType.NUMBER`), Feld beim Antippen komplett markiert, damit man direkt überschreibt.
- **Optional ±-Buttons** neben kg (Schritt 2.5) und Wdh (Schritt 1), für den häufigsten Fall "ein bisschen mehr".
- **Keine Slider.** Bei Gewichten von 0 bis 200 kg ist ein Pixel mehrere Kilo, verschwitzte Finger treffen nicht exakt, und keine der grossen Apps benutzt welche. NN/g und Shopify empfehlen Stepper nur für kleine Werte und Eingabefelder für grosse.

### 4. Tastatur-Flow ohne Umwege

- kg → "Weiter" → Wdh → "Fertig" speichert den Satz. Danach steht der nächste Satz vorbefüllt da und die Tastatur bleibt offen. Status bei uns: ✅ (`on_submit`-Kette plus `autofocus`).
- Komma und Punkt akzeptieren, denn deutsche Tastaturen liefern ein Komma. Status bei uns: ✅ (`parse_weight`).
- Fehler direkt am Feld anzeigen, nicht als Popup.

### 5. Löschen: schnell und rückgängig machbar

- Ein Satz wird per Wischen oder Long-Press gelöscht, danach erscheint eine **Snackbar "Satz gelöscht · Rückgängig"** für ca. 5 Sekunden.
- Bestätigungsdialoge nur für Zerstörerisches im grossen Stil (ganzes Workout löschen).
- Satznummern danach neu durchzählen.

### 6. Nichts geht verloren

- Jeder Satz wird sofort gespeichert. Es gibt keinen "Workout speichern"-Button, an dem Daten hängen.
- App wird beendet oder das Handy klingelt: Beim nächsten Öffnen geht es genau da weiter. Status bei uns: ✅, weil jeder Satz direkt in SQLite landet.

### 7. Gym-taugliche Bedienung

- Tap-Ziele mindestens **48 dp** (Material) bzw. 44 pt. Lieber grösser, man hat oft zittrige Hände.
- Grosse Schrift für die Zahlen, gut lesbar auf Armlänge.
- Wichtige Buttons (✓, Satz hinzufügen) im unteren Bildschirmdrittel, einhändig erreichbar.
- Wenig Optionen sichtbar. Strong hat viele Satz-Typen und Varianten, gilt dadurch aber als "dicht" für Einsteiger. Hevy gewinnt bei Einfachheit.

### 8. Körpergewicht

- Leeres kg-Feld heisst Körpergewicht. Anzeige "BW × 12". Status bei uns: ✅.
- Später denkbar: Zusatzgewicht als "BW + 10". Dafür wäre ein Modellfeld nötig, also ein `later`-Issue.

## Was sich nicht bewährt

- **Slider und Scroll-Räder** für Gewicht, Wdh oder Dauer: langsam und ungenau.
- **Ein Dialog pro Satz** zum Anlegen: zu viele Taps, Kontext weg.
- **Pflichtfelder** über kg und Wdh hinaus (RPE, Notiz, Satz-Typ): bremsen jeden Satz. Wenn überhaupt, optional und versteckt.
- **Bestätigungsdialoge** für jede kleine Aktion. Undo ist besser.
- **Fehlende Vorher-Werte:** Man muss sich merken oder nachschauen, was man letztes Mal gemacht hat. Das ist der häufigste Grund, warum Leute zurück zum Notizbuch wechseln.
- **Speichern am Ende:** Ein Absturz oder ein versehentliches "Zurück" kostet das ganze Training.

## Laufen (Phase 3)

- **Dauer als ein Ziffernfeld**, das automatisch formatiert: Eingabe `2530` wird zu `25:30`, `10512` wird zu `1:05:12`. Das ist schneller als getrennte Felder für h/min/s und viel schneller als ein Scroll-Rad. Wheel-only-Dauerpicker sind ein bekannter Beschwerdepunkt.
- **Distanz** als Dezimalfeld in km, Komma erlaubt.
- **Pace sofort live anzeigen**, während man tippt (`5:12 min/km`). Das ist gleichzeitig eine Plausibilitätskontrolle für Tippfehler.
- Parser und Formatter für die Dauer gehören in `core/` und sind mit pytest getestet.

## Hyrox (Phase 4)

Die Hyrox-Apps sind sich einig: **feste Struktur, ein Abschnitt nach dem anderen.**

- Die 16 Abschnitte (Lauf 1, SkiErg, Lauf 2, Sled Push, …) stehen schon als Liste da. Man trägt nur die Zeiten ein, mit demselben Dauerfeld wie beim Laufen.
- "Weiter" auf der Tastatur springt zum nächsten Abschnitt.
- Gesamtzeit wird live summiert.
- Teil-Simulation: Abschnitte ohne Zeit zählen einfach nicht mit. Keinen extra Modus bauen.
- In der Detailansicht Splits nebeneinander zeigen, damit man sieht, wo Zeit verloren ging.
- Live-Stoppuhr mit "Tap = nächste Station" (RunStation, Sweat) ist ein Timer, also laut Plan nicht in 1.0 → `later`-Issue.

## Bewusst nicht jetzt (`later`-Issues)

Diese Features haben die grossen Apps, sie sind laut `PLAN.md` aber nicht in 1.0:

- Pausentimer, der beim Abhaken eines Satzes automatisch startet (Strong, StrengthLog): #6
- RPE/RIR pro Satz: #7
- Supersätze: #8
- Satz-Typen (Aufwärmen, Drop-Set, bis zum Versagen) und Scheibenrechner: bewusst verworfen, kein Issue
- Zusatzgewicht bei Körpergewichtsübungen ("BW + 10")
- Freitext-Parser ("Bank 80x8, 80x6")

## Checkliste für jeden neuen Eingabe-Screen

- [ ] Ist der wahrscheinlichste Wert vorbefüllt?
- [ ] Ist der Normalfall in einem Tap erledigt?
- [ ] Numpad statt Slider/Rad, Komma erlaubt?
- [ ] Kann man ohne Dialog korrigieren?
- [ ] Löschen mit Undo statt Bestätigungsdialog?
- [ ] Wird sofort gespeichert?
- [ ] Tap-Ziele mindestens 48 dp, Zahlen gross?
- [ ] Bedienbar mit einer Hand, Daumen unten?
- [ ] Liegt die Logik (Parsen, Vorschlag, Berechnung) in `core/` und ist getestet?

## Quellen

- [Hevy: Previous Workout Values](https://help.hevyapp.com/hc/en-us/articles/36011896355479-How-to-Use-Previous-Workout-Values-to-Improve-Performance-in-Hevy)
- [Hevy: Track Exercises](https://www.hevyapp.com/features/track-exercises/)
- [Setgraph: Hevy vs Strong](https://setgraph.app/ai-blog/hevy-vs-strong) (Konkurrent, mit Vorsicht lesen)
- [StrengthLog Screens](https://screensdesign.com/showcase/strengthlog-workout-tracker)
- [Setgraph Screens](https://screensdesign.com/showcase/setgraph-workout-training-log)
- [NN/g: Input Steppers](https://nngroup.com/articles/input-steppers)
- [Shopify: Number field](https://shopify.dev/docs/api/pos-ui-extensions/latest/web-components/forms/number-field)
- [Brad Frost: You probably don't need input type="number"](https://bradfrost.com/blog/post/you-probably-dont-need-input-typenumber/)
- [Material: Time pickers](https://m2.material.io/components/time-pickers)
- [ICDS: Time input](https://design.sis.gov.uk/components/inputs/time-input)
- [Feature-Request: besserer Duration-Picker](https://bydesign.featurebase.app/p/better-duration-picker-on-mobile)
- [Corona-Warn-App Issue: nur noch Picker](https://github.com/corona-warn-app/cwa-app-ios/issues/2209)
- [RunStation](https://alternativeto.net/software/runstation/about/), [Hyro](https://apps.apple.com/app/id6753948941), [Hevy Hyrox](https://www.hevyapp.com/hyrox-training/)
