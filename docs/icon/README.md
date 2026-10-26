# App icon and splash

The images in `src/assets/` are rendered from the HTML files in this folder. `flet build` picks them up by name:

| Source | Output | Used as |
| --- | --- | --- |
| `icon-android.html` | `src/assets/icon_android.png` | Android app icon, used exactly as is (no extra margin) |
| `splash-android.html` | `src/assets/splash_android.png` | Splash image, transparent, on the color from `[tool.flet.splash]` in `pyproject.toml` |

Design: angular biceps (logo R) from the `ideas/design` branch, background F (violet gradient).

## Render

With Microsoft Edge headless, 1024 × 1024 px. Use a fresh `--user-data-dir` each time: if an Edge process still holds the profile, the call exits 0 without writing a file.

```bash
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
"$EDGE" --headless=new --user-data-dir="$TEMP/edge-$RANDOM" --no-first-run --disable-gpu \
  --hide-scrollbars --default-background-color=00000000 --window-size=1024,1024 \
  --screenshot="C:\path\to\out.png" "file:///C:/path/to/docs/icon/icon-android.html"
```

## Size

The biceps size is the `scale(...)` in the `transform` of the path: `.5` for the icon (Android crops icons to a circle or rounded square), `.6` for the splash (Android 12+ shows it inside a circle).
