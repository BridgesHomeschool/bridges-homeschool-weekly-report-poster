# Bridges Homeschool Weekly Learning Summary

A portrait A4 LaTeX template for a child-centered weekly homeschool learning summary.

## Layout

- child name as the primary title
- grouped Week at a Glance panel with dashboard counts
- main six-pillar table using Current Level, Activities This Week, and Total Minutes
- activity summaries with counts for repeated work types
- total minutes per pillar, with support for `---` / not recorded when logs lack duration
- right-hand rail for Books & Reading, Work Evidence thumbnails, and Weekly Pattern
- next week's focus strip with four numbered cards
- end-of-week summary / parent notes box

## Optional assets

If you add these files, the template will use them automatically:

- `assets/student-photo.png`
- `assets/children/<child>/reference.jpg`
- book covers in `assets/books/`
- evidence thumbnails in `assets/evidence/`

## Build

Use LuaLaTeX and point `TEXINPUTS` at the Bridges brand system.

Linux / macOS:

```bash
export TEXMFHOME="$HOME/texmf"
export TEXINPUTS="/home/lachlan/repos/BridgesHomeschool/core/bridges-brand-system/assets/bridges/tex/classes//:/home/lachlan/repos/BridgesHomeschool/core/bridges-brand-system/assets/bridges/tex/packages//:"
lualatex -interaction=nonstopmode -halt-on-error weekly-report-poster.tex
```

Windows / PowerShell:

```powershell
$brand = 'F:/vault/projects/homeschool/core/bridges-brand-system/assets/bridges/tex'
$env:TEXINPUTS = "$brand/classes//;$brand/packages//;"
lualatex -interaction=nonstopmode -halt-on-error weekly-report-poster.tex
```

The template expects the sibling `bridges-brand-system` repo to be present. It uses the shared Bridges class, fonts, colors, and logo assets.

## Local layout fixture

For layout testing, the repo includes a saved Charles snapshot at
`fixtures/charles-current-week.yaml`. It mirrors the current poster content
based on the actual homeschool logs and can be used as a stable test fixture
when iterating on spacing or typography.

## Child reference assets

The repo also keeps reusable child reference images under
`assets/children/<child>/`. The Charles layout fixture currently points at
`assets/children/charles/reference.jpg` so the reference portrait appears beside
his name.
