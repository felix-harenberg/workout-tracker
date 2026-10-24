# Ideen-Roadmap

Ideensammlung für später, auf dem Branch `ideas/design`. Nichts davon ist im App-Code umgesetzt. Die Umsetzung passiert in der Haupt-Session nach `PLAN.md`.

Stand: 22. Oktober 2026

## Erledigt

- [x] Logging-UX recherchiert: wie Strong, Hevy & Co. das Eintragen lösen → [logging-ux.md](logging-ux.md)
- [x] Stil gewählt: dunkel, Neon-Violett, Milchglas → [design/design.md](design/design.md), [design/vorlage.html](design/vorlage.html)
- [x] `later`-Issues: #6 Pausentimer, #7 RPE/RIR, #8 Supersätze

## Themen

1. [x] **Restliche Screens im neuen Stil:** Workout-Liste, Neues Workout, Workout-Details, Übung wählen → [design/screens.html](design/screens.html). Entwurf gefällt. Ausdrücklich gewünscht: letzter Satz unter jeder Übung in der Auswahl. Offen: Wochen-Leiste, Namens-Chips, PR-Rand.
2. [x] **Lauf-Screens** (Entwurf passt so, Pause bewusst in Metern) → [design/laufen.html](design/laufen.html). Felix macht kein Hyrox-Training, sondern läuft: Intervalle, Long Run (Zone 2), kurzer schneller Lauf. Details trackt Strava, die App braucht nur das Wesentliche: Distanz, Dauer oder Pace (der dritte Wert wird berechnet), optional Zone. Bei Intervallen zählen Anzahl, Intervall-Distanz und Pausen-Distanz.
   - **Offene Frage für die Haupt-Session:** Phase 4 (Hyrox) in `PLAN.md` passt nicht zum eigenen Training. Ersetzen oder streichen?
3. [x] **Fortschritt-Screen** (Graph passt so; Wunsch: Ziel-Linie nie am Rand, y-Achse oben und unten mit Luft) → [design/fortschritt.html](design/fortschritt.html). Kein Graph pro Übung nötig, Kraft als einfache Zeilen („Bankdrücken 75 → 82.5 kg“).
   - **Neue Idee (nicht in `PLAN.md`):** Körpergewicht 1× pro Woche eintragen, Graph mit violetter Ziel-Linie. Richtung egal (ab- oder zunehmen), die Punkte laufen auf die Linie zu. Datenmodell: Tabelle mit Datum + kg, dazu ein Zielgewicht. → Issue #18.
4. [ ] **Kleine Momente** → [design/momente-und-icon.html](design/momente-und-icon.html). Wunsch: kurzer Rekord-Screen, nicht fancy, trockener Ton („Was hast du anderes erwartet?“). Bei verdächtig grossem Sprung (> ca. 20 % über Bestwert) erst „Vertippt?“ fragen.
5. [ ] **Leere Zustände:** keine Workouts, Übung zum ersten Mal
6. [ ] **App-Icon und Name** → vier Icon-Richtungen im selben Entwurf (Monogramm, Neon-Hantel, Puls, Glas-Häkchen)
7. [ ] **README-Auftritt:** Screenshots, Aufbau der GitHub-Seite
8. [ ] **Glas-Effekt-Test:** Ruckelt die Unschärfe in Flet auf dem Handy?

## Wo wir stehen

Themen 1 bis 3 erledigt. Themen 4 und 6 laufen: Entwurf Rekord-Screen und Icons liegt vor, Feedback steht aus.
