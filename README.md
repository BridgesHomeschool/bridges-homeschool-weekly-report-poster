# Bridges Homeschool Weekly Report Poster

A portrait A4 LaTeX template for the weekly homeschool report poster.

## Layout

- top header with name, title, and date
- cartoon kids artwork area at the top
- small week-at-a-glance stats in the top right
- left-shifted main table for pillars, current skills, activities, minutes, and next step
- right column for books and reading plus work evidence photos
- three bottom reflection boxes for key progress, what worked / didn't, and what's next

## Optional assets

If you add these files, the template will use them automatically:

- `assets/kids-cartoon.png`
- book cover images inside `assets/books/`
- work evidence images inside `assets/evidence/`

## Build

Use pdfLaTeX:

```bash
pdflatex weekly-report-poster.tex
```

The template intentionally sticks to standard packages so it should compile on a basic TeX Live install.
