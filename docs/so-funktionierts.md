# So funktioniert's: der Workout Tracker von innen

Stand: 26. Oktober 2026 (v0.3 + Design). Ein Rundgang durch den Code, damit du jeden Teil selbst erklären kannst, im Bewerbungsgespräch genauso wie im README-Abschnitt "What I learned".

**So liest du das hier am besten:** In VS Code öffnen (Vorschau mit `Ctrl+Shift+V`) und den Links in den Code folgen. Pro Abschnitt etwa 10 Minuten. Am Ende stehen Fragen zum Selbsttest.

---

## 1. Das grosse Bild

```
src/
├── main.py          Einstiegspunkt: Theme setzen, Datenbank öffnen, App starten
├── core/            Logik und Daten. Importiert NIE flet.
│   ├── models.py        Datenklassen: Exercise, Workout, WorkoutSet, Run
│   ├── db.py            Verbindung + Migrationen (Datenbank-Schema)
│   ├── repository.py    Speichern und Laden (SQL)
│   ├── training.py      Eingaben parsen, formatieren, Vorschläge
│   ├── templates.py     "Wie letztes Mal"
│   ├── stats.py         PRs, Wochenvolumen
│   ├── scale.py         Achsen-Mathe für Diagramme
│   ├── export.py        CSV-Export
│   └── run.py           Läufe (nur noch zum Anzeigen alter Läufe)
├── ui/              Flet-Screens. Rufen core/ auf, enthalten keine Logik.
│   ├── app.py           Router: welche Route zeigt welchen Screen
│   ├── theme.py         Farben, Schriften, Bausteine (Glas-Karte, Button, ...)
│   └── *.py             ein Screen pro Datei
└── assets/          Icon, Splash, Schriften
tests/               pytest, testet nur core/
```

**Was beim Start passiert** ([main.py](../src/main.py#L21)):

1. Flet ruft `main(page)` auf. `page` ist das Fenster bzw. der Handy-Bildschirm.
2. `theme.apply(page)` setzt Farben und Schriften, `lock_portrait` sperrt das Querformat.
3. `connect(db_path())` öffnet die SQLite-Datei. Auf dem Handy liegt sie im privaten App-Ordner (`FLET_APP_STORAGE_DATA`), am PC in `data/`.
4. `App(page, conn).start()` zeigt den ersten Screen.

## 2. Die wichtigste Entscheidung: `core/` und `ui/` getrennt

`core/` weiss nichts von Flet. Es bekommt Zahlen und Texte rein und gibt Zahlen, Texte und Datenklassen raus.

**Warum das wichtig ist:**

- **Testbar ohne Handy.** Alle 181 Tests laufen in drei Sekunden auf dem Laptop und in GitHub Actions. Eine UI zu testen ist viel aufwendiger.
- **Austauschbar.** Würde Flet morgen sterben, könntest du `core/` mit einer anderen UI weiterverwenden. Auch für die spätere ML-Auswertung mit pandas brauchst du nur `core/` und die Datenbank.
- **Klare Verantwortung.** Ein Bug in einer Berechnung? Dann suchst du in `core/`. Etwas sieht komisch aus? Dann in `ui/`.

**Ein Beispiel:** Die Eingabe "82,5" im Gewichtsfeld wird nicht im Screen umgewandelt, sondern in [`parse_weight`](../src/core/training.py#L8). Der Screen ruft nur die Funktion auf und zeigt bei einem Fehler eine Meldung an ([exercise_sets.py](../src/ui/exercise_sets.py#L178)).

## 3. Die Daten: Modelle und Tabellen

### Modelle ([models.py](../src/core/models.py))

Vier `@dataclass(frozen=True)`-Klassen. `frozen` heisst: Ein Objekt kann man nach dem Erstellen nicht mehr ändern. Das verhindert eine ganze Klasse von Bugs, bei denen irgendwo still ein Wert überschrieben wird. Willst du etwas ändern, speicherst du es in der Datenbank und lädst ein neues Objekt.

`WorkoutSet.weight_kg` darf `None` sein: Das heisst Körpergewicht. `is_bodyweight` ist eine `@property`, also ein berechneter Wert ohne eigene Spalte.

### Tabellen ([db.py](../src/core/db.py#L8))

| Tabelle | Inhalt | Besonderheit |
| --- | --- | --- |
| `exercise` | id, name | `UNIQUE COLLATE NOCASE`: "Bench" und "bench" sind dieselbe Übung |
| `workout` | id, name, date, notes, type | Datum als Text `2026-10-26` (ISO), sortiert sich dadurch richtig |
| `workout_set` | workout_id, exercise_id, set_number, reps, weight_kg | `CHECK (reps > 0)`: die Datenbank selbst lehnt Unsinn ab |
| `run` | workout_id, distance_km, duration_s | nur noch für alte Läufe |

**Fremdschlüssel:** `workout_set.workout_id REFERENCES workout(id) ON DELETE CASCADE`. Löschst du ein Workout, löscht SQLite seine Sätze automatisch mit. Aber nur, weil [`connect`](../src/core/db.py#L54) `PRAGMA foreign_keys = ON` setzt. SQLite hat das aus historischen Gründen standardmässig aus.

**Eine Falle, in die wir getreten sind:** `COLLATE NOCASE` kennt nur ASCII. "BANKDRÜCKEN" und "bankdrücken" wären für SQLite verschieden. Deshalb vergleicht [`get_or_create_exercise`](../src/core/repository.py#L11) die Namen in Python mit `casefold()`. Der Kommentar dort erklärt das.

## 4. Migrationen: die Datenbank auf dem Handy umbauen

Das ist der Teil, auf den du im Gespräch am meisten stolz sein kannst.

**Das Problem:** Deine Datenbank liegt auf dem Handy, mit echten Trainings. Mit v0.2 kam die Spalte `type` und die Tabelle `run` dazu. Die App muss die alte Datenbank beim ersten Start umbauen, ohne Daten zu verlieren.

**Die Lösung** ([db.py](../src/core/db.py#L8)):

- `MIGRATIONS` ist eine Liste von SQL-Skripten. Eintrag 0 legt die Tabellen an, Eintrag 1 fügt die Läufe hinzu.
- SQLite hat ein eingebautes Zahlenfeld `PRAGMA user_version`. Darin steht, wie viele Migrationen schon gelaufen sind.
- [`_migrate`](../src/core/db.py#L59) liest die Zahl und führt nur die fehlenden Skripte aus. Neue Datenbank: alle. Datenbank von v0.1: nur Eintrag 1. Aktuelle Datenbank: keins.
- Jedes Skript läuft in `BEGIN ... COMMIT`. Bricht etwas ab, bleibt die Datenbank im alten Zustand statt halb umgebaut.

**Die goldene Regel** (steht als Kommentar über der Liste): Ein veröffentlichtes Skript ändert man **nie**. Auf deinem Handy ist es schon gelaufen und würde nicht nochmal laufen. Änderungen kommen immer als neuer Eintrag ans Ende.

**Der Test dazu:** [`test_v1_database_is_upgraded_without_data_loss`](../tests/test_repository.py#L353) baut eine Datenbank wie in v0.1 nach, füllt sie mit Daten, öffnet sie mit dem aktuellen Code und prüft, dass alles noch da ist.

## 5. Speichern und Laden: das Repository

[repository.py](../src/core/repository.py) ist die einzige Stelle mit SQL für Workouts und Sätze. Drei Muster, die überall vorkommen:

**1. `?`-Platzhalter statt f-Strings:**
```python
conn.execute("SELECT ... WHERE id = ?", (workout_id,))
```
Nie `f"... WHERE id = {workout_id}"`. Mit Platzhaltern kann ein Wert nie als SQL-Code interpretiert werden (Stichwort **SQL-Injection**). Bei einer Offline-App ohne fremde Eingaben ist das weniger kritisch, aber es ist die Regel, und Recruiter achten darauf.

**2. `with conn:` als Transaktion:**
```python
with conn:
    conn.execute("DELETE ...")
    conn.execute("UPDATE ...")
```
Alles im Block wird gemeinsam gespeichert (commit) oder bei einem Fehler gemeinsam verworfen (rollback). Beispiel: [`delete_set`](../src/core/repository.py#L166) löscht einen Satz **und** nummeriert die folgenden neu. Beides oder nichts.

**3. Zeilen in Datenklassen umwandeln:** SQL liefert Tupel wie `(1, "Push", "2026-10-26", "", "strength")`. [`_workout_from_row`](../src/core/repository.py#L104) macht daraus ein `Workout` mit echtem `date`-Objekt. Der Rest der App sieht nie rohe Tupel.

**Ein gutes Beispiel für eine schlaue Abfrage:** [`last_sets_for_exercise`](../src/core/repository.py#L221) findet "das letzte Workout vor diesem, in dem diese Übung vorkam". Mit Unterabfrage (`id IN (SELECT ...)`) und einer Regel für zwei Workouts am selben Tag (die frühere ID gilt als früher).

## 6. Die Logik, die du im Gym spürst

| Funktion | Was sie tut |
| --- | --- |
| [`suggest_next_set`](../src/core/training.py#L72) | Vorschlag für den nächsten Satz: gleiche Satznummer wie letztes Mal, sonst der vorige Satz von heute |
| [`pending_exercises`](../src/core/templates.py#L53) | "Vom letzten Mal": Übungen des letzten gleichnamigen Workouts, die heute noch fehlen |
| [`exercise_pr`](../src/core/stats.py#L32) | Schwerster Satz; bei gleichem Gewicht gewinnt der mit mehr Wiederholungen. Trick: `max(..., key=lambda: (gewicht, wdh))` vergleicht Tupel von links nach rechts |
| [`weekly_volume`](../src/core/stats.py#L61) | Sätze pro Kalenderwoche, inklusive Wochen ohne Training (sonst würden Pausen im Diagramm fehlen) |
| [`date_from_picker`](../src/core/training.py#L48) | Ein echter Bug-Fix, siehe Abschnitt 10 |
| [`axis_range`](../src/core/scale.py#L20) | Runde Achsenschritte für Diagramme, siehe Abschnitt 10 |

Lies dir zu jeder Funktion auch ihre Tests an, zum Beispiel in [test_training.py](../tests/test_training.py). Tests sind die beste Dokumentation: Sie zeigen, was rein- und was rauskommt.

## 7. Die UI: Screens und Navigation

### Router ([app.py](../src/ui/app.py#L10))

Jeder Screen hat eine Adresse (Route), wie eine Webseite: `/`, `/workout/12`, `/workout/12/exercise/3`, `/stats`.

[`render`](../src/ui/app.py#L27) baut aus der Route einen **Stapel** von Screens. Für `/workout/12/exercise/3` liegen drei Screens übereinander: Liste, Workout 12, Übung 3. Drückt man auf Android "Zurück" oder auf den Pfeil oben links, wird der oberste entfernt ([`back`](../src/ui/app.py#L73)), und man landet automatisch auf dem richtigen Screen darunter.

Das `match parts:` ist Pythons **Structural Pattern Matching** (seit 3.10): `case ["workout", workout_id, *rest]` passt auf jede Liste, die mit `"workout"` beginnt, und speichert den Rest in Variablen.

### Screens

Jeder Screen ist eine Funktion, die ein `ft.View` zurückgibt, zum Beispiel [`workout_detail_view`](../src/ui/workout_detail.py#L14). Sie holt Daten aus `core/`, baut daraus Controls und hängt Klick-Funktionen an.

**Nach einer Änderung wird alles neu gebaut:** Speicherst du einen Satz, ruft der Screen `app.render()` auf ([exercise_sets.py](../src/ui/exercise_sets.py#L94)), und der ganze Stapel wird aus der Datenbank neu aufgebaut. Das ist einfacher und fehlerfreier, als einzelne Texte zu aktualisieren, und bei dieser Datenmenge schnell genug.

**Threads:** Flet führt Klick-Funktionen in Hintergrund-Threads aus. SQLite erlaubt eine Verbindung normalerweise nur im Thread, der sie geöffnet hat. Deshalb `check_same_thread=False` in [`connect`](../src/core/db.py#L53). Das ist sicher, weil die App immer nur eine Sache gleichzeitig macht.

### Design ([theme.py](../src/ui/theme.py))

Alle Farben und Bausteine an einer Stelle. Screens rufen `theme.glass_card(...)` auf, statt jedes Mal Farben anzugeben. Willst du das Violett ändern, änderst du eine Zeile.

**Die Glas-Regel aus deinem Handy-Test:** Echte Unschärfe (`blur`) kostet Leistung, weil bei jedem Bild alles dahinter neu weichgezeichnet wird. Deshalb haben scrollende Karten nur angedeutetes Glas (Verlauf + Rand), und echte Unschärfe gibt es nur beim festen Eingabe-Panel ([`glass_panel`](../src/ui/theme.py#L239)).

## 8. Tests

```bash
pytest            # alle Tests
pytest -k pr      # nur Tests mit "pr" im Namen
pytest -x         # beim ersten Fehler aufhören
```

Drei pytest-Werkzeuge, die überall vorkommen:

- **Fixture** `conn`: Jeder Test bekommt eine frische, leere Datenbank in einem Temp-Ordner (`tmp_path`). Tests beeinflussen sich so nie gegenseitig.
- **`@pytest.mark.parametrize`**: Ein Test, viele Eingaben. Siehe [`test_parse_duration`](../tests/test_run.py#L33): eine Funktion, zehn Fälle.
- **`pytest.raises(ValueError)`**: prüft, dass falsche Eingaben wirklich abgelehnt werden.

**Arbeitsweise:** Bei den meisten Features stand zuerst der Test, dann der Code (Test-Driven Development). Der Test schlägt erst fehl, weil die Funktion noch nicht existiert, und wird dann grün. So weiss man, dass der Test auch wirklich etwas prüft.

## 9. Vom Code zur App auf dem Handy

Zwei Workflows in [.github/workflows/](../.github/workflows/):

- **[tests.yml](../.github/workflows/tests.yml):** bei jedem Push `ruff check`, `ruff format --check` und `pytest`. Der grüne Haken im Repo.
- **[build-apk.yml](../.github/workflows/build-apk.yml):** bei Änderungen an `src/` oder `pyproject.toml` baut `flet build apk` die App. Flet lädt dafür Flutter, Java und das Android SDK selbst herunter.

**Signieren:** Android erkennt Updates an Paket-ID **und** Signatur. Der Schlüssel liegt als GitHub Secret vor, der Workflow schreibt ihn in eine temporäre Datei und gibt ihn über Umgebungsvariablen an Flet. Ohne festen Schlüssel hätte jeder Build eine andere Signatur, und Android würde Updates verweigern.

**Build-Nummer:** `--build-number ${{ github.run_number }}`. Jeder Build bekommt eine höhere Nummer, Android erkennt ihn als neuer.

## 10. Bugs, aus denen man lernt

Das ist Material für "What I learned" im README:

1. **Datum einen Tag zu früh.** Der Datumswähler schickt "Mitternacht Ortszeit" als UTC-Zeit: 22.10. 00:00 in Zürich = 21.10. 22:00 UTC. `.date()` gab den 21. Lösung: auf den nächsten Tag runden ([`date_from_picker`](../src/core/training.py#L48)). Lehre: **Zeitzonen sind überall**, auch wenn man "nur ein Datum" will.
2. **Fehlende Achsenbeschriftung.** Die Diagramm-Bibliothek fragt Beschriftungen nur an ihren eigenen Rasterpunkten ab. Labels bei krummen Werten wie 96 kg wurden still verschluckt. Lösung: Achse auf runde Schritte legen ([scale.py](../src/core/scale.py)). Lehre: **Doku der Bibliothek lesen**, wenn etwas nur manchmal klappt.
3. **Altes Logo beim Start.** Flet sucht den Splash unter `splash_android.png`, `splash.png` oder `icon.png`, nicht unter `icon_android.png`. Gefunden durch Lesen des Flet-Quellcodes in `.venv`.
4. **Hintergrund-Leuchten fehlte.** Ein Verlauf in `View.decoration` wurde auf dem Handy nicht gezeichnet, Verläufe auf Containern schon. Lösung: das Leuchten als eigene Ebene hinter den Inhalt legen.
5. **Features gestrichen:** Hyrox (Roxfit macht das), Läufe (Uhr + Strava), geschätztes 1RM (du wolltest dein echtes Maximum). Lehre: **Weglassen ist eine Entscheidung**, und eine gute App macht wenige Dinge richtig.

## 11. Fragen zum Selbsttest

Kannst du die beantworten, ohne nachzuschauen? Wenn nicht, ist der passende Abschnitt oben verlinkt.

1. Warum importiert `core/` nie `flet`? (Abschnitt 2)
2. Was passiert mit den Sätzen, wenn man ein Workout löscht, und warum? (3)
3. Du willst eine Spalte `rpe` zu `workout_set` hinzufügen. Was genau musst du tun, und was darfst du auf keinen Fall tun? (4)
4. Woher weiss die App beim Start, welche Migrationen schon gelaufen sind? (4)
5. Warum `?` statt f-String im SQL? (5)
6. Was macht `with conn:`? Nenne ein Beispiel, wo es wichtig ist. (5)
7. Wie entscheidet die App, was im kg-Feld vorausgefüllt ist? (6)
8. Was passiert technisch, wenn du auf Android "Zurück" drückst? (7)
9. Warum ist echte Unschärfe nur im Eingabe-Panel? (7)
10. Warum kann man ein Update installieren, ohne die App zu löschen? (9)
11. Erzähl einen Bug, den du gefunden und gelöst hast. (10)
