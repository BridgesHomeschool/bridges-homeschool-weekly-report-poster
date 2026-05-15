#!/usr/bin/env python3
"""Build a weekly report poster PDF from structured YAML input."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

POSTER_ROOT = Path(__file__).resolve().parent
TEMPLATE = POSTER_ROOT / "weekly-report-poster.tex"
BRAND_TEX = POSTER_ROOT.parent / "bridges-brand-system" / "assets" / "bridges" / "tex"

SECTION_STYLE = {
    "Languages": ("Sky!35", "SoftBlue", r"\IconBook", "Languages"),
    "Mathematics": ("Paper", "SoftGreen", r"\IconCalc", "Mathematical and Scientific Reasoning"),
    "English": ("Sky!35", "SoftBlue", r"\IconBook", "Languages"),
    "Humanities": ("Peach!36", "SoftOrange", r"\IconGlobe", "Humanities"),
    "Practical / Life": ("Mint!42", "SoftTeal", r"\IconHome", "Practical Life and Household Competence"),
    "Health / Physical": ("Sky!28", "SoftRed", r"\IconRun", "Health and Physical Readiness"),
    "Arts and Making": ("Lavender!38", "SoftPurple", r"\IconPalette", "Arts and Making"),
}

ROW_ORDER = [
    "Languages",
    "Mathematics",
    "Humanities",
    "Arts and Making",
    "Health / Physical",
    "Practical / Life",
]


def tex_escape(value: Any) -> str:
    text = str(value or "")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def tex_path(path: Any, input_path: Path) -> str:
    if not path:
        return "assets/missing-image.png"
    raw = str(path)
    candidate = Path(raw)
    if not candidate.is_absolute():
        for base in (input_path.parent, POSTER_ROOT, POSTER_ROOT.parent / "bridges-homeschool-core"):
            resolved = (base / raw).resolve()
            if resolved.exists():
                return resolved.as_posix()
    return candidate.resolve().as_posix() if candidate.exists() else raw.replace("\\", "/")


def short(value: Any, limit: int = 82) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,.;:") + "."


def bullets_from_text(value: Any, count: int = 3) -> list[str]:
    if isinstance(value, list):
        items = [short(item) for item in value if str(item or "").strip()]
    else:
        text = str(value or "").strip()
        items = [short(part) for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return items[:count]


def activities(value: Any, count: int = 3) -> list[str]:
    items = value if isinstance(value, list) else []
    result = [short(item, 74).replace(" â€” ", ": ").replace(" — ", ": ") for item in items if str(item or "").strip()]
    while len(result) < count:
        result.append("")
    return result[:count]


def minutes_cell(value: Any) -> str:
    if value is None or value == "":
        return r"{\NoMinutes\par{\tiny not recorded}}"
    try:
        minutes = int(value)
    except Exception:
        return r"{\NoMinutes\par{\tiny not recorded}}"
    return r"{{\fontsize{18}{18}\selectfont\bfseries\color{Navy}" + str(minutes) + r"}\par{\tiny min}}"


def level_notes_cell(notes: list[str]) -> str:
    if not notes:
        notes = ["No activity logged this week."]
    lines = [rf"    {{\color{{Gold}}$\bullet$}} {tex_escape(note)}\par" for note in notes[:3]]
    return (
        r"{\begin{minipage}[c][1.68cm][c]{\linewidth}" + "\n"
        r"    \begingroup\setlength{\parskip}{0.04em}%" + "\n"
        + "\n".join(lines)
        + "\n"
        + r"    \endgroup" + "\n"
        + r"  \end{minipage}}"
    )


def template_preamble() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    return text.split(r"\begin{document}", 1)[0]


def render_glance(stats: dict[str, Any], main_thread: str) -> str:
    pillars = stats.get("pillars_covered_count") or str(stats.get("pillars_covered") or "0").split("/")[0]
    activities_count = stats.get("total_activities") or 0
    minutes = stats.get("total_minutes")
    minutes_text = "---" if minutes is None else str(minutes)
    books = stats.get("books_read") or 0
    return rf"""
\renewcommand{{\GlancePanel}}{{%
  \begin{{tcolorbox}}[
    title={{Week at a Glance}},
    colback=Sky,
    colframe=Line,
    coltitle=white,
    colbacktitle=Navy,
    fonttitle=\scriptsize\bfseries,
    arc=2mm,
    boxrule=0.4pt,
    left=2mm,
    right=2mm,
    top=0.9mm,
    bottom=0.9mm
  ]
    \Metric{{SoftBlue}}{{\MetricPillarsIcon}}{{{tex_escape(pillars)}}}{{Pillars}}\MetricSep
    \Metric{{SoftGreen}}{{\MetricActivitiesIcon}}{{{tex_escape(activities_count)}}}{{Activities}}\MetricSep
    \Metric{{SoftRed}}{{\MetricMinutesIcon}}{{{tex_escape(minutes_text)}}}{{Minutes}}\MetricSep
    \Metric{{SoftOrange}}{{\MetricBooksIcon}}{{{tex_escape(books)}}}{{Books}}\par
    \vspace{{0.2em}}
    \begin{{tcolorbox}}[
      colback=Paper,
      colframe=Sky,
      boxrule=0pt,
      arc=1.8mm,
      left=1.6mm,
      right=1.6mm,
      top=0.45mm,
      bottom=0.45mm
    ]
      \tiny\textbf{{\color{{Navy}}Main thread:}} {tex_escape(short(main_thread, 98))}
    \end{{tcolorbox}}
  \end{{tcolorbox}}%
}}
"""


def render_weekly_pattern(active_days: int, sections: list[dict[str, Any]]) -> str:
    most = "Records"
    populated = [section for section in sections if section.get("activities")]
    if populated:
        most = str(populated[0].get("section") or most)
    return rf"""
\renewcommand{{\WeeklyPatternCard}}{{%
  \begin{{tcolorbox}}[
    title={{\DoodleLeaf\ Weekly Pattern}},
    colback=Mint,
    colframe=Line,
    colbacktitle=Mint,
    coltitle=Navy,
    fonttitle=\bfseries,
    arc=2mm,
    boxrule=0.35pt,
    left=1.8mm,
    right=1.8mm,
    top=0.9mm,
    bottom=0.8mm,
    height=2.55cm
  ]
    \scriptsize
    \PatternRow{{Active days}}{{{tex_escape(active_days)}}}
    \vspace{{0.13em}}
    \PatternRow{{Most consistent}}{{{tex_escape(most)}}}
    \vspace{{0.13em}}
    \PatternRow{{Records focus}}{{Minutes + samples}}
  \end{{tcolorbox}}%
}}
"""


def section_lookup(sections: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup = {str(item.get("section") or ""): item for item in sections}
    if "Languages" not in lookup and "English" in lookup:
        lookup["Languages"] = lookup["English"]
    return lookup


def render_row(section_name: str, section: dict[str, Any]) -> str:
    row_color, mark_color, icon, display = SECTION_STYLE[section_name]
    notes = bullets_from_text(section.get("current_skills"), 3)
    acts = activities(section.get("activities"), 3)
    return rf"""
  \rowcolor{{{row_color}}}
  \PillarRow
    {{\PillarMark{{{mark_color}}}{{{icon}}}{{{tex_escape(display)}}}}}
    {level_notes_cell(notes)}
    {{\ActivityNotes{{{tex_escape(acts[0])}}}{{{tex_escape(acts[1])}}}{{{tex_escape(acts[2])}}}}}
    {minutes_cell(section.get("minutes"))}
"""


def render_books(books: list[dict[str, Any]], input_path: Path) -> str:
    if not books:
        books = [{"title": "Reading Log", "subtitle": "Current week", "note": "No standalone book logged.", "evidence_ref": ""}]
    rendered = []
    for book in books[:2]:
        rendered.append(
            rf"\BookItem{{{tex_escape(tex_path(book.get('evidence_ref'), input_path))}}}"
            rf"{{{tex_escape(short(book.get('title'), 40))}}}"
            rf"{{{tex_escape(short(book.get('subtitle') or book.get('date'), 28))}}}"
            rf"{{{tex_escape(short(book.get('section') or '', 22))}}}"
            rf"{{{tex_escape(short(book.get('note') or 'Logged this week.', 54))}}}"
        )
    return "\n    ".join(rendered)


def render_evidence(items: list[dict[str, Any]], input_path: Path) -> str:
    labels = []
    for item in items[:4]:
        labels.append((tex_path(item.get("path"), input_path), short(item.get("activity_type") or item.get("section") or "Evidence", 18)))
    while len(labels) < 4:
        labels.append(("assets/missing-image.png", "Sample needed"))
    return (
        rf"\EvidenceItem{{{tex_escape(labels[0][0])}}}{{{tex_escape(labels[0][1])}}}{{\hfill}}" "\n    "
        rf"\EvidenceItem{{{tex_escape(labels[1][0])}}}{{{tex_escape(labels[1][1])}}}{{}}\par\vspace{{0.16em}}" "\n    "
        rf"\EvidenceItem{{{tex_escape(labels[2][0])}}}{{{tex_escape(labels[2][1])}}}{{\hfill}}" "\n    "
        rf"\EvidenceItem{{{tex_escape(labels[3][0])}}}{{{tex_escape(labels[3][1])}}}{{}}"
    )


def render_focus(reflection: dict[str, Any]) -> str:
    items = reflection.get("what_next") or []
    defaults = ["Reading", "Maths", "Talk", "Records"]
    cards = []
    colors = ["Sky", "Mint", "Peach", "Lavender"]
    for idx in range(4):
        text = short(items[idx] if idx < len(items) else "Add one useful record.", 36)
        cards.append(rf"\FocusCard{{{colors[idx]}}}{{{idx + 1}}}{{{defaults[idx]}}}{{{tex_escape(text)}}}")
    return r"\hfill".join(cards)


def render_document(data: dict[str, Any], input_path: Path) -> str:
    poster = data.get("poster") or {}
    stats = poster.get("stats") or {}
    sections = poster.get("sections") or []
    lookup = section_lookup(sections)
    reflection = poster.get("reflection") or {}
    progress = reflection.get("key_progress") or []
    summary = short(progress[0] if progress else "Weekly learning was recorded.", 150)
    main_thread = summary
    if progress:
        main_thread = progress[0]
    reference = poster.get("reference_image") or f"assets/children/{str(poster.get('name') or 'child').split()[0].lower()}/reference.jpg"
    week = poster.get("week_range") or {}
    week_label = week.get("label") or f"{week.get('start', '')} to {week.get('end', '')}".strip(" to")
    active_days = stats.get("active_days") or 0

    rows = []
    for name in ROW_ORDER:
        rows.append(render_row(name, lookup.get(name, {"section": name, "current_skills": "No activities logged this week.", "activities": [], "minutes": None})))

    return (
        template_preamble()
        + rf"""
\renewcommand{{\StudentName}}{{{tex_escape(str(poster.get('name') or 'Weekly Poster').split()[0])}}}
\renewcommand{{\ReportTitle}}{{Weekly Learning Dashboard}}
\renewcommand{{\ReportWeek}}{{Week of {tex_escape(week_label)}}}
\renewcommand{{\StudentReferenceImage}}{{{tex_escape(reference)}}}
"""
        + render_glance(stats, main_thread)
        + render_weekly_pattern(active_days, sections)
        + rf"""
\begin{{document}}
\ThinPageFrame
\vspace*{{0.02cm}}

\begin{{minipage}}[t]{{0.46\textwidth}}
  \vspace{{0pt}}
  \StudentPhoto{{\STIXTwoText\fontsize{{31}}{{32}}\selectfont\bfseries\color{{Navy}}\StudentName\hspace{{0.12em}}\DoodleStar}}\par
  \vspace{{0.02em}}
  {{\normalsize\bfseries\color{{Muted}}\ReportTitle}}\par
  \vspace{{0.16em}}
  {{\normalsize\ReportWeek}}\par
  \vspace{{0.25em}}
  \SoftNote{{{tex_escape(summary)}}}
\end{{minipage}}
\hfill
\begin{{minipage}}[t]{{0.51\textwidth}}
  \vspace{{0pt}}
  \GlancePanel
\end{{minipage}}

\vspace{{0.12em}}

\begin{{minipage}}[t]{{0.705\textwidth}}
  \vspace{{0pt}}
  \arrayrulecolor{{Line}}
  \fontsize{{7.15}}{{7.8}}\selectfont
  \begin{{tabularx}}{{\linewidth}}{{|L{{2.42cm}}|Y|Y|C{{1.22cm}}|}}
  \hline
  \rowcolor{{Navy!94}}
  \rule{{0pt}}{{0.52cm}}\color{{white}}\bfseries Pillar
  & \color{{white}}\bfseries Current Level
  & \color{{white}}\bfseries Activities This Week
  & \color{{white}}\bfseries Total Minutes\\
  \hline
{''.join(rows)}
  \end{{tabularx}}
  \normalsize
\end{{minipage}}
\hfill
\begin{{minipage}}[t]{{0.275\textwidth}}
  \vspace{{0pt}}
  \begin{{tcolorbox}}[
    title={{\DoodleBook\ Books \& Reading}},
    colback=Lavender!45,
    colframe=Line,
    colbacktitle=Lavender,
    coltitle=Navy,
    fonttitle=\bfseries,
    arc=2mm,
    boxrule=0.35pt,
    left=1.8mm,
    right=1.8mm,
    top=1.4mm,
    bottom=1.1mm,
    height=4.85cm
  ]
    {render_books(poster.get('featured_books') or [], input_path)}
  \end{{tcolorbox}}

  \vspace{{0.16em}}

  \begin{{tcolorbox}}[
    title={{\DoodleCamera\ Work Evidence}},
    colback=Sky,
    colframe=Line,
    colbacktitle=Sky,
    coltitle=Navy,
    fonttitle=\bfseries,
    arc=2mm,
    boxrule=0.35pt,
    left=1.8mm,
    right=1.8mm,
    top=1.4mm,
    bottom=1.1mm,
    height=3.75cm
  ]
    {render_evidence(poster.get('featured_evidence') or [], input_path)}
  \end{{tcolorbox}}

  \vspace{{0.1em}}
  \WeeklyPatternCard
\end{{minipage}}

\vspace{{0.1em}}

\begin{{tcolorbox}}[
  title={{Next Week's Focus}},
  colback=Paper,
  colframe=Line,
  colbacktitle=Peach,
  coltitle=Navy,
  fonttitle=\bfseries,
  arc=2mm,
  boxrule=0.35pt,
  left=2mm,
  right=2mm,
  top=1.0mm,
  bottom=1.0mm,
  height=1.42cm
]
  {render_focus(reflection)}
\end{{tcolorbox}}

\vspace{{0.08em}}

\begin{{tcolorbox}}[
  title={{\DoodleLeaf\ End-of-Week Summary}},
  colback=Cream,
  colframe=Line,
  colbacktitle=Mint,
  coltitle=Navy,
  fonttitle=\bfseries,
  arc=2mm,
  boxrule=0.35pt,
  left=2.2mm,
  right=2.2mm,
  top=0.9mm,
  bottom=0.9mm,
  height=1.18cm
]
  \scriptsize\linespread{{1.0}}\selectfont
  {tex_escape(summary)}
\end{{tcolorbox}}

\end{{document}}
"""
    )


def compile_tex(tex_file: Path, output_pdf: Path) -> None:
    env = os.environ.copy()
    env["TEXINPUTS"] = f"{BRAND_TEX / 'classes'}//;{BRAND_TEX / 'packages'}//;"
    result = subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={output_pdf.parent}", str(tex_file)],
        cwd=str(POSTER_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)

    built_pdf = output_pdf.parent / f"{tex_file.stem}.pdf"
    if built_pdf != output_pdf:
        output_pdf.write_bytes(built_pdf.read_bytes())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Poster input YAML")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--no-refresh", action="store_true", help="Accepted for core workflow compatibility")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input).resolve()
    output_pdf = Path(args.output).resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
    tex_file = output_pdf.with_suffix(".tex")
    tex_file.write_text(render_document(data, input_path), encoding="utf-8")
    compile_tex(tex_file, output_pdf)
    print(str(output_pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
