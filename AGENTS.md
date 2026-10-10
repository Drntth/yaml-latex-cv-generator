# yaml-latex-cv-generator

Commit prefix: [CV-GENERATOR]

## Purpose

Bilingual (en, hu) CV and cover letter generator. Content in YAML, design in one LaTeX class with Jinja2 templates, two CV variants (`developer`, `general`) and per-application overrides. Ships with fictional sample data (Jane Doe) and the PDFs generated from it. Domain terms: `CONTEXT.md`.

## Stack

Python 3.10+, Jinja2, PyYAML; TeX Live (`pdflatex`, `latexmk`); poppler-utils (`pdfinfo`, `pdftoppm`); pytest, ruff.

## Commands

```bash
make venv                                # .venv + requirements.txt + requirements-dev.txt
make all                                 # 4 CVs + 4 letters into dist/
make app APP=applications/<file>.yaml    # one application
make test                                # pytest (no LaTeX needed)
make lint                                # ruff check + format --check
make preview                             # docs/ preview PNGs from dist/
```

Run `make all`, `make test` and `make lint` after every change; check the page and word count report.

## Structure

- `content/`: all text (`profile`, `labels`, `cv`, `cover_letter`).
- `variants/`: per-variant title, summary, section order, output name.
- `applications/`: per-application overrides; allowed keys are `APP_KEYS` in `build.py`.
- `templates/`: `developercv.cls` and the `*.tex.j2` templates; Jinja delimiters `\VAR{}`, `\BLOCK{}`, `\#{}`.
- `assets/`: images (`photo_file`, optional `signature_file` from `content/profile.yaml`).
- `build.py`: resolve, render, latexmk, checks. `tests/`: pytest suite.
- `dist/`: committed sample PDFs; `build/`: gitignored intermediates.

## Conventions and gotchas

- Code comments, docstrings, CLI messages and docs are English; only `README.hu.md` is Hungarian. `README.md` and `README.hu.md` change together.
- Sample data stays fictional: no real people, companies, contact details or photos. Use `example.com` and `Example …` names.
- Design changes go into `templates/`; text changes into `content/`, `variants/`, `applications/`.
- Every text exists in both languages; quote YAML values that contain a comma.
- Targets: CV 1 page; letter 250-400 words (en), 180-320 (hu).
- Output must stay reproducible: keep `SOURCE_DATE_EPOCH` and the fixed `date` in `content/cover_letter.yaml`; commit `dist/` only for real content changes.
- After a design or sample content change, run `make preview` and commit the PNGs.
- ATS-friendly: single column, no icon fonts, ligatures disabled, contact details as plain text.
- The LaTeX class is MIT-licensed third-party work; keep its notice in `LICENSE` and in the class header.
