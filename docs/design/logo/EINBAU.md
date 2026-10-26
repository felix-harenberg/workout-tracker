# App-Icon einbauen (für die Haupt-Session)

Gewählt: Logo R (eckiger Bizeps, weiss) auf Hintergrund F (Verlauf Schwarz/Violett).

## Schritte

1. Auf `main` den Ordner `src/assets/` anlegen (gibt es noch nicht).
2. `icon_android.png` aus diesem Ordner nach `src/assets/icon_android.png` kopieren:
   ```bash
   git show origin/ideas/design:docs/design/logo/icon_android.png > src/assets/icon_android.png
   ```
3. Committen, z.B. `Add app icon`. Der nächste APK-Build in GitHub Actions nimmt das Icon automatisch.
4. APK installieren und auf dem Homescreen prüfen.

## Warum so

- Flet sucht beim Build in `src/assets/` zuerst nach `icon_android.png`, danach nach `icon.png`. Eine Datei mit `_android` im Namen wird **genau so** übernommen, ohne dass Flet Ränder dazurechnet.
- Flet kann kein SVG als Icon verwenden, deshalb eine PNG mit 1024 × 1024 px.
- Der Bizeps ist auf 60 % verkleinert, damit Android ihn beim Zuschneiden (Kreis, abgerundetes Quadrat) nicht anschneidet.

## Wenn es nicht passt

- Bizeps zu klein oder zu gross: in `icon-android-render.html` den Wert `scale(.6)` ändern und neu rendern (Edge headless, Fenster 1024 × 1024).
- Andere Variante: Die SVGs `icon-*.svg` daneben sind die anderen Versionen.
