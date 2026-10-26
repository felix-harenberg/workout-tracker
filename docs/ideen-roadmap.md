# Ideen-Roadmap

Ideensammlung für später, auf dem Branch `ideas/design`. Nichts davon ist im App-Code umgesetzt. Die Umsetzung passiert in der Haupt-Session nach `PLAN.md`.

Stand: 22. Oktober 2026

## Erledigt

- [x] Logging-UX recherchiert: wie Strong, Hevy & Co. das Eintragen lösen → [logging-ux.md](logging-ux.md)
- [x] Stil gewählt: dunkel, Neon-Violett, Milchglas → [design/design.md](design/design.md), [design/vorlage.html](design/vorlage.html)
- [x] `later`-Issues: #6 Pausentimer, #7 RPE/RIR, #8 Supersätze

## Themen

1. [x] **Restliche Screens im neuen Stil:** Workout-Liste, Neues Workout, Workout-Details, Übung wählen → [design/screens.html](design/screens.html). Entwurf gefällt. Ausdrücklich gewünscht: letzter Satz unter jeder Übung in der Auswahl. Offen: Wochen-Leiste, Namens-Chips, PR-Rand.
2. [x] ~~**Lauf-Screens**~~ **Entscheid 26. Okt 2026: Läufe werden nicht gespeichert.** Die App ist nur fürs Krafttraining. Entwurf bleibt als Archiv, wird nicht umgesetzt. (Vorher: Entwurf passt so, Pause bewusst in Metern) → [design/laufen.html](design/laufen.html). Felix macht kein Hyrox-Training, sondern läuft: Intervalle, Long Run (Zone 2), kurzer schneller Lauf. Details trackt Strava, die App braucht nur das Wesentliche: Distanz, Dauer oder Pace (der dritte Wert wird berechnet), optional Zone. Bei Intervallen zählen Anzahl, Intervall-Distanz und Pausen-Distanz.
   - **Offene Frage für die Haupt-Session:** Phase 4 (Hyrox) in `PLAN.md` passt nicht zum eigenen Training. Ersetzen oder streichen?
3. [x] **Fortschritt-Screen** (Graph passt so; Wunsch: Ziel-Linie nie am Rand, y-Achse oben und unten mit Luft) → [design/fortschritt.html](design/fortschritt.html). Kein Graph pro Übung nötig, Kraft als einfache Zeilen („Bankdrücken 75 → 82.5 kg“).
   - **Neue Idee (nicht in `PLAN.md`):** Körpergewicht 1× pro Woche eintragen, Graph mit violetter Ziel-Linie. Richtung egal (ab- oder zunehmen), die Punkte laufen auf die Linie zu. Datenmodell: Tabelle mit Datum + kg, dazu ein Zielgewicht. → Issue #18.
4. [x] **Kleine Momente** (Rekord-Screen und „Vertippt?“-Frage passen so; Abhak-Animation und Abschluss-Screen nicht weiter verfolgt) → [design/momente-und-icon.html](design/momente-und-icon.html). Wunsch: kurzer Rekord-Screen, nicht fancy, trockener Ton („Was hast du anderes erwartet?“). Bei verdächtig grossem Sprung (> ca. 20 % über Bestwert) erst „Vertippt?“ fragen.
5. [x] **Leere Zustände** → [design/leere-zustaende.html](design/leere-zustaende.html). Kleiner Anstoss mit 4 rotierenden Sprüchen, alle vier passen vorerst, später anpassbar.
   - **Wunsch:** am liebsten echte Markus-Rühl-Sprüche. Nur wörtlich belegte Zitate verwenden (Quelle notieren), nichts erfinden und ihm nicht in den Mund legen. Kurze Zitate mit Namensnennung, aber Name und Bild nicht als Branding der App nutzen.
6. [x] **App-Icon** – **Entscheid: Logo R (eckiger Bizeps, nur rechte Winkel), weiss, auf E (Violett) oder F (App-Hintergrund).** Favorit: **F (Verlauf) mit weissem Bizeps**, mehr Kontrast. Vier Versionen in [design/logo/](design/logo/), Übersicht in `vorschau.html`: `icon-violett-leer.svg` (Violett pur), `icon-hintergrund.svg` (F + weisser Bizeps, Favorit), `icon-violett.svg` (Bizeps auf Violett), `icon-neon.svg` (violetter Bizeps leuchtend auf Schwarz), dazu `logo.svg` (nur Bizeps). Name der App noch offen.
   - Verlauf: zuerst Wunsch nach kein Logo, kein Text, nur Farbe bzw. violettes Muster wie im App-Hintergrund mit Schwarz. Entwurf [design/icon-v2.html](design/icon-v2.html): E reines Violett, F App-Hintergrund, G ein Leuchten, H Verlauf. **Finalisten: E und F**, G und H raus. Entscheidung erst in Phase 6, wenn die App im neuen Look läuft. (Erste Runde mit Logos in momente-und-icon.html verworfen.)
   - **Neue Logo-Idee:** Bizeps wie 💪 aus Höhenlinien (Topografie), der Bizeps ist der höchste Hügel → [design/logo-topo.html](design/logo-topo.html). Varianten I–L: weiss auf schwarz, Neon-Linien, auf Icon F, auf Icon E. Erzeugter Konzept-Entwurf; ein finales Logo würde man sauber als Vektor nachzeichnen. Felix: sieht nicht so gut aus wie gedacht.
   - **Runde 2** → [design/logo-ideen.html](design/logo-ideen.html): M Bizeps aus Dreiecken gefüllt (Low-Poly wie Elefant-Beispiel), N Sternbild (nur Linien + Punkte, Neon), O „68“ Neon, P „68“ als Kontur auf Violett. 68 = F (6.) + H (8.) Buchstabe. Verworfen: 247 und 1441 (bestehende Marken), „Do it“ (zu nah an Nike). Felix: Dreiecke gefallen nicht.
   - **Runde 3** → [design/logo-eckig.html](design/logo-eckig.html): eckiger Bizeps nach Felix' Skizze, weiss gefüllt, simpel. Formen Q (wie Skizze), R (nur rechte Winkel), S (mit Bizeps-Spitze), jeweils auf Schwarz, F und E.
7. [x] **README-Auftritt** (Aufbau passt so) → [design/readme/README-entwurf.md](design/readme/README-entwurf.md), Titelbild [design/readme/hero.png](design/readme/hero.png). Zielgruppe: Nutzer und Recruiter gleichermassen. Aufbau: Icon, Name, Einzeiler, Badges, Titelbild, Sprungmarken; danach Why, Features, Install (für Nutzer), dann How it's built, Run from source, What I learned (für Recruiter/Entwickler). Sprache Englisch. Titelbild zeigt Konzept-Entwürfe, vor 1.0 durch echte Screenshots ersetzen.
8. [x] **Glas-Effekt-Test:** **Ergebnis: Mischung.** Echt ruckelt, Angedeutet und Mischung laufen flüssig. Regel in [design/design.md](design/design.md) („Glas: getestet auf dem Handy“), Code in [design/glas-test/main.py](design/glas-test/main.py). Spike-Branch gelöscht.
   - Aufbau: Test-App auf Wegwerf-Branch `spike/glas-test` (eigene Paket-ID `io.github.felixharenberg.glastest`, installiert sich neben der echten App). 24 Glas-Karten zum Scrollen, Schalter für Unschärfe an/aus. APK per GitHub Actions.
   - Runde 1: Mit echter Unschärfe auf allen Karten merkt man beim Scrollen einen Unterschied, nicht ganz flüssig. Grund: jede Karte zeichnet bei jedem Bild alles dahinter neu weich.
   - Runde 2: Drei Modi zum Vergleichen: **Echt** (alles echt), **Angedeutet** (keine Unschärfe, Glas nur mit Fläche, Rand und Verlauf), **Mischung** (Karten angedeutet, echte Unschärfe nur beim festen Eingabe-Panel unten).

## Weitere Ideen

- [x] **Indikator: nächstes Mal hoch oder runter** → [design/indikator.html](design/indikator.html). Grünes Dreieck ▲ = mehr Gewicht, rotes ▼ = weniger. Nur Erinnerung, die Vorbefüllung bleibt unverändert. Setzen unter den Sätzen (nochmal tippen = weg), sichtbar in „Übung wählen“ und oben im Satz-Screen beim nächsten Mal, verschwindet nach dem ersten Satz. Datenmodell: ein Feld pro Übung (hoch / runter / nichts). Entwurf passt so, Details werden beim Bau des UI angepasst.

## Wo wir stehen

Alle 8 Themen erledigt. Offen: App-Name. Entscheid: keine Läufe in der App (nur Krafttraining). Gewichts-Indikator als Entwurf festgehalten.
