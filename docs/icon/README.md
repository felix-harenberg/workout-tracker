# App icon and splash

The images in `src/assets/` are rendered from the HTML files in this folder. `flet build` picks them up by name:

| Source | Output | Used as |
| --- | --- | --- |
| `icon-android.html` | `src/assets/icon_android.png` | Android app icon, used exactly as is (no extra margin) |
| `splash-android.html` | `src/assets/splash_android.png` | Splash image, transparent, on the color from `[tool.flet.splash]` in `pyproject.toml` |

Design: angular biceps (logo R) from the `ideas/design` branch, redrawn for the blog look on 2026-10-28: blue outline (#1F5FFF), no fill, inside a blue square. The biceps is stretched to 110 x 110 units so the gap to the square is the same on all four sides. Icon on #141414, splash on transparent.

## Render

With Microsoft Edge headless, 1024 × 1024 px. Use a fresh `--user-data-dir` each time: if an Edge process still holds the profile, the call exits 0 without writing a file. Edge may also return before the screenshot is written, so wait a few seconds before checking for the file.

```bash
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
"$EDGE" --headless=new --user-data-dir="$TEMP/edge-$RANDOM" --no-first-run --disable-gpu \
  --hide-scrollbars --default-background-color=00000000 --window-size=1024,1024 \
  --screenshot="C:\path\to\out.png" "file:///C:/path/to/docs/icon/icon-android.html"
```

## Size

The biceps size is the `scale(...)` in the `transform` of the path, and the square sits 10 units (at icon scale) around it. Icon: biceps `.5`, square side 75 (Android crops icons to a circle or rounded square). Splash: everything scaled down to a square side of 68 (Android 12+ shows the splash inside a circle of about 2/3 of the image; the square's corners must stay inside it). Keep both stroke widths equal on screen.
