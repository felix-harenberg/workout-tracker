# Hyrox Tracker: Projektplan

Stand: 8. Oktober 2026 · Felix

> Source of truth für den Plan. Checkboxen hier abhaken, nicht im Claude Doc.

## Ziel und Rahmen

Eine Android-App in Python, mit der du Krafttraining, Läufe und Hyrox-Einheiten loggst, offline auf dem Handy. Öffentlich auf GitHub, mit Anleitung zum Nachbauen. Budget: 3 Stunden pro Woche, Version 1.0 in ca. 13 Wochen (Mitte Januar 2027).

**Der eine Meilenstein, der zählt:** v0.1 nach ca. 5 Wochen. Ab da loggst du jedes Training in deiner eigenen App. Alles danach baut auf einer App auf, die du schon benutzt.

**Bewusst nicht in 1.0:**

- Kein Login, kein Server, kein Cloud-Sync
- Kein iOS
- Keine Trainingspläne, Timer oder Social-Features
- Kein Play Store (Installation per APK aus GitHub Releases)

Kommt dir während dem Bauen eine neue Feature-Idee, landet sie als GitHub Issue mit Label `later`. Nicht im Code.

## Tech-Entscheide

Python mit Flet als UI, SQLite als Speicher, die Logik strikt getrennt vom UI. Diese Trennung ist das, was das Projekt fürs CV wertvoll macht.

| Bereich | Entscheid | Warum |
| --- | --- | --- |
| Sprache | Python 3.12 | Dein Wunsch, später ML mit denselben Daten |
| UI / App | [Flet](https://flet.dev) | Python-Code, baut eine echte Android-APK (`flet build apk`) |
| Speicher | SQLite (`sqlite3` aus der Standardbibliothek) | Offline, eine Datei, später direkt mit pandas lesbar |
| Tests | pytest | Die Logik läuft ohne Handy und UI testbar |
| Code-Qualität | ruff (Linter + Formatter) | Ein Tool, null Konfiguration |
| CI | GitHub Actions | Bei jedem Push Tests; bei jedem Release baut GitHub die APK |
| Verteilung | GitHub Releases | Andere laden die APK herunter und installieren sie |

**Architektur in einem Satz:** `core/` enthält Modelle, Datenbank-Zugriff und Berechnungen (z.B. PRs, Volumen) und importiert nie Flet. `ui/` enthält nur die Screens und ruft `core/` auf. So testest du 90 % des Codes auf dem Laptop.

**Grösstes Risiko:** Flet ist eine Nische. Deshalb kommt in Phase 1 zuerst ein Test, ob eine Mini-App mit SQLite auf deinem Handy läuft. Klappt das nicht, wechseln wir früh, bevor Arbeit verloren geht.

## Phasen

Sieben Phasen, jede endet mit etwas, das funktioniert. Die Wochen sind Richtwerte bei 3 Stunden pro Woche.

### Phase 0: Blueprint (Woche 1)

- [x] Public Repo `hyrox-tracker` auf GitHub erstellen, mit README-Entwurf (Was, Warum, Status: in Arbeit)
- [x] Datenmodell für V1 skizzieren: `Exercise`, `Workout`, `StrengthSet` (Satznummer, Wiederholungen, Gewicht in kg)
- [x] 3 Screens auf Papier zeichnen: Workout-Liste, Workout erfassen, Workout-Details
- [x] Skizzen als Foto in `docs/` ablegen und committen
- [x] Issues anlegen für Phase 1 und 2

### Phase 1: Setup und Machbarkeitstest (Woche 2 bis 3)

- [x] Python-Umgebung mit `venv`, Flet installieren, Repo-Struktur anlegen (siehe unten)
- [x] Mini-App: ein Button speichert einen Eintrag in SQLite, eine Liste zeigt ihn an
- [x] Mit `flet build apk` bauen und auf dem Handy installieren
- [x] **Gate:** Läuft die Mini-App auf dem Handy und überlebt der Eintrag einen Neustart der App? Nein → Stack überdenken, bevor es weitergeht
- [x] pytest und ruff einrichten, GitHub Actions Workflow für Tests

### Phase 2: Kraft-MVP, v0.1 (Woche 3 bis 5)

- [x] `core/`: Datenbank-Schema, Funktionen zum Speichern und Laden von Workouts und Sätzen, mit Tests
- [x] Screen: Workout starten, Übung wählen oder neu anlegen, Sätze eintragen
- [x] Screen: Liste vergangener Workouts, Tippen öffnet Details
- [x] Workout bearbeiten und löschen
- [x] Export aller Daten als CSV (Backup, weil alles nur auf dem Handy liegt, und Grundlage für spätere ML-Auswertung)
- [x] Release v0.1 auf GitHub, APK installiert
- [x] **Ab jetzt jedes Training in der App loggen.** Was im Gym nervt, wird ein Issue

### Phase 3: Laufen, v0.2 (Woche 6 bis 7)

- [ ] Workout-Typ `run`: Distanz in km, Dauer, berechnete Pace in min/km
- [ ] Optional: Splits pro Kilometer
- [ ] Tests für die Pace-Berechnung
- [ ] Release v0.2

### Phase 4: Hyrox, v0.3 (Woche 8 bis 9)

- [ ] Workout-Typ `hyrox`: 8 Laufsplits und die 8 Stationen in fester Reihenfolge (SkiErg, Sled Push, Sled Pull, Burpee Broad Jumps, Rowing, Farmers Carry, Sandbag Lunges, Wall Balls)
- [ ] Zeit pro Abschnitt eintragen, Gesamtzeit wird berechnet
- [ ] Auch Teil-Simulationen erlauben (z.B. nur 4 Stationen)
- [ ] Release v0.3

### Phase 5: Auswertung, v0.4 (Woche 10 bis 11)

- [ ] `core/`: Berechnung von PRs (bestes Gewicht, geschätztes 1RM), Wochenvolumen, Pace-Verlauf, mit Tests
- [ ] Screen mit Fortschrittsgraphen pro Übung und für Lauf-Pace
- [ ] Release v0.4

### Phase 6: Öffentlicher Release 1.0 (Woche 12 bis 13)

- [ ] README fertig: Screenshots, Features, Installation per APK, Build aus dem Quellcode
- [ ] GitHub Actions baut die APK automatisch beim Release-Tag
- [ ] Abschnitt "Was ich gelernt habe" bzw. Architekturentscheide im README
- [ ] Lizenz (MIT)
- [ ] Release 1.0, Projekt im CV und auf LinkedIn eintragen
- [ ] Blogpost über das Projekt

## Repo-Struktur und Definition of Done

Das Repo ist ab Tag 1 öffentlich. Eine saubere Commit-Historie über drei Monate zeigt mehr als ein einzelner grosser Upload am Ende.

```
hyrox-tracker/
├── src/
│   ├── main.py          # Einstiegspunkt der App
│   ├── core/            # Modelle, Datenbank, Berechnungen (kein Flet!)
│   └── ui/              # Flet-Screens
├── tests/               # pytest, testet core/
├── docs/                # Skizzen, Screenshots
├── .github/workflows/   # Tests + APK-Build
├── pyproject.toml
├── README.md
└── LICENSE
```

**1.0 ist fertig, wenn:**

- Ein Fremder ohne Hilfe die APK aus den Releases installieren kann
- Ein Fremder mit den README-Schritten die App selbst aus dem Code bauen kann
- Alle Tests in GitHub Actions grün sind
- Du sie seit mindestens 6 Wochen selbst im Training benutzt

## Regeln, damit es fertig wird

1. **Fixer Slot:** 3 Stunden zu festen Zeiten im Kalender, z.B. zweimal 90 Minuten. Nicht "wenn ich Zeit habe".
2. **Jede Session endet mit einem Commit**, auch wenn es nur ein halbes Feature ist. Und mit einer Notiz im Issue, wo du das nächste Mal weitermachst.
3. **Phasen nicht überspringen.** Graphen gibt es erst, wenn Hyrox steht.
4. **Neue Ideen = Issue mit Label `later`.** Nie sofort einbauen.
5. **Prüfungsphase:** Wenn die ETH Vorrang braucht, pausierst du bewusst und schreibst das ins README. Pausieren ist erlaubt, stilles Liegenlassen nicht.
6. **Blog läuft weiter:** Ein Post pro Woche bleibt. Der Fortschritt am Tracker ist gutes Material dafür.
