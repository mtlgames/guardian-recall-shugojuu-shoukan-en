# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/LiberationSerif-Bold.ttf, -BoldItalic.ttf, -Regular.ttf | github.com/liberationfonts/liberation-fonts 2.1.5 | SIL OFL 1.1 (fonts/LICENSE-Liberation.txt) | yes | title/location/condition cards (tools/gfx.py) | - |
| fonts/LiberationSans-Bold.ttf | github.com/liberationfonts/liberation-fonts 2.1.5 (same release, 2026-11-25) | SIL OFL 1.1 (fonts/LICENSE-Liberation.txt) | yes | FMV subtitles (tools/fmv_subs.py, D18) | - |
| fonts/vwf12.txt | drawn for this project (2026-11-23) | MIT, same as repo | yes | English VWF in the game's 12x14 glyph font (tools/font.py draws it into the font TIM) | - |
