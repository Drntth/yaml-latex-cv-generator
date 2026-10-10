"""CV and cover letter build: YAML content -> Jinja2 LaTeX template -> PDF.

Usage:
    python build.py all
    python build.py cv --variant developer --lang hu
    python build.py letter --variant general --lang en
    python build.py app applications/2026-01-15-company-position.yaml
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

import jinja2
import yaml

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
VARIANTS = ROOT / "variants"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
BUILD = ROOT / "build"
DIST = ROOT / "dist"

LANGS = ("en", "hu")
VARIANT_NAMES = ("developer", "general")
# Recommended letter length in words; Hungarian needs fewer words for the same length.
LETTER_WORDS = {"en": (250, 400), "hu": (180, 320)}
# Sections known by cv.tex.j2.
SECTIONS = {
    "summary",
    "experience",
    "projects",
    "education",
    "activities",
    "skills",
    "certificates",
    "other",
}
# Fixed PDF timestamp (2026-01-01 00:00 UTC): the same content gives a byte-identical PDF,
# so committed files in dist/ change only when the content really changes.
SOURCE_DATE_EPOCH = "1767225600"

# Keys an application file may override (never facts).
APP_KEYS = {
    "extends",
    "langs",
    "photo",
    "title",
    "summary",
    "sections",
    "hide",
    "skills_order",
    "letter",
}


class BuildError(Exception):
    pass


# ---------------------------------------------------------------------------
# YAML loading and resolution
# ---------------------------------------------------------------------------


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve(node, lang: str, variant: str, where: str = ""):
    """Resolve language and variant dependent values recursively.

    - {en, hu} dict: the value for the language (both keys are required);
    - {"@developer", "@general"} dict: the value for the variant, None if missing;
    - in a list, an item with a `tags` field is kept only for the listed variants.
    """
    if isinstance(node, dict):
        keys = set(node)
        if keys and keys <= set(LANGS):
            missing = set(LANGS) - keys
            if missing:
                raise BuildError(
                    f"Missing translation ({', '.join(sorted(missing))}): {where}"
                )
            return resolve(node[lang], lang, variant, where)
        if keys & set(LANGS):
            # Typical cause: an unquoted comma inside an {en: ..., hu: ...} line.
            raise BuildError(
                f"Malformed language pair (extra keys: {sorted(keys - set(LANGS))}): {where}"
            )
        if keys and all(str(k).startswith("@") for k in keys):
            return resolve(node.get(f"@{variant}"), lang, variant, where)
        return {
            k: resolve(v, lang, variant, f"{where}.{k}")
            for k, v in node.items()
            if k != "tags"
        }
    if isinstance(node, list):
        out = []
        for i, item in enumerate(node):
            if (
                isinstance(item, dict)
                and "tags" in item
                and variant not in item["tags"]
            ):
                continue
            value = resolve(item, lang, variant, f"{where}[{i}]")
            if value is not None:
                out.append(value)
        return out
    return node


def format_date(day: dt.date, lang: str, months: list[str]) -> str:
    if lang == "hu":
        return f"{day.year}. {months[day.month - 1]} {day.day}."
    return f"{day.day} {months[day.month - 1]} {day.year}"


def require_asset(name: str) -> None:
    """A missing image would only fail deep in the LaTeX log; report it early."""
    if not (ASSETS / name).is_file():
        raise BuildError(f"Missing file in assets/: {name}")


def build_context(variant: str, lang: str, app: dict | None = None) -> dict:
    if variant not in VARIANT_NAMES:
        raise BuildError(f"Unknown variant: {variant}")
    app = app or {}

    def r(node, where):
        return resolve(node, lang, variant, where)

    profile = load_yaml(CONTENT / "profile.yaml")
    labels = r(load_yaml(CONTENT / "labels.yaml"), "labels")
    cv = r(load_yaml(CONTENT / "cv.yaml"), "cv")
    letter = r(load_yaml(CONTENT / "cover_letter.yaml"), "cover_letter")
    base = load_yaml(VARIANTS / f"{variant}.yaml")

    title = r(app.get("title", base.get("title")), "title")
    summary = r(app.get("summary", base.get("summary")), "summary")
    sections = app.get("sections", base["sections"])
    unknown = set(sections) - SECTIONS
    if unknown:
        raise BuildError(f"Unknown section(s): {', '.join(sorted(unknown))}")
    hide = set(base.get("hide", [])) | set(app.get("hide", []))

    for section, items in cv.items():
        cv[section] = [it for it in items if f"{section}:{it.get('id')}" not in hide]

    order = app.get("skills_order")
    if order and "skills" in cv:
        rank = {sid: i for i, sid in enumerate(order)}
        cv["skills"].sort(key=lambda s: rank.get(s.get("id"), len(rank)))

    letter.update(r(app.get("letter", {}), "letter"))
    day = letter.get("date") or dt.datetime.now().astimezone().date()
    if isinstance(day, str):
        day = dt.date.fromisoformat(day)
    letter["place_date"] = (
        f"{letter['place']}, {format_date(day, lang, labels['months'])}"
    )

    # Precedence: command line / application file > variant > default (on).
    photo = bool(app.get("photo", base.get("photo", True)))
    if photo:
        require_asset(profile.get("photo_file", "avatar.jpg"))
    if profile.get("signature_file"):
        require_asset(profile["signature_file"])

    return {
        "lang": lang,
        "variant": variant,
        "profile": profile,
        "labels": labels,
        "photo": photo,
        "title": title,
        "summary": summary,
        "sections": sections,
        "letter": letter,
        "base": base,
        **cv,
    }


# ---------------------------------------------------------------------------
# LaTeX rendering
# ---------------------------------------------------------------------------


class Raw(str):
    """Text that is already LaTeX-safe; finalize does not escape it again."""


LATEX_ESCAPES = {
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


def latex_escape(text: str) -> str:
    escaped = "".join(LATEX_ESCAPES.get(ch, ch) for ch in text)
    # **bold** -> \textbf{bold}
    parts = escaped.split("**")
    if len(parts) % 2 == 0:
        raise BuildError(f"Odd number of ** bold markers: {text}")
    return "".join(f"\\textbf{{{p}}}" if i % 2 else p for i, p in enumerate(parts))


def url_filter(value: str) -> Raw:
    return Raw(str(value).replace("%", r"\%").replace("#", r"\#"))


def finalize(value):
    if value is None or isinstance(value, jinja2.Undefined):
        return ""
    if isinstance(value, Raw):
        return value
    return latex_escape(str(value))


ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES),
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    comment_start_string=r"\#{",
    comment_end_string="}",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    finalize=finalize,
    keep_trailing_newline=True,
)
ENV.filters["url"] = url_filter


def run_tool(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run an external program; a missing program gives a readable error."""
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, errors="replace", check=False, **kwargs
        )
    except OSError as exc:
        raise BuildError(f"Cannot run: {cmd[0]} ({exc})") from exc


def compile_pdf(template: str, ctx: dict, name: str, dest: Path) -> Path:
    workdir = BUILD / name
    workdir.mkdir(parents=True, exist_ok=True)
    tex = workdir / f"{name}.tex"
    tex.write_text(ENV.get_template(template).render(**ctx), encoding="utf-8")

    env = dict(
        os.environ,
        TEXINPUTS=f"{TEMPLATES}{os.pathsep}{ASSETS}{os.pathsep}",
        SOURCE_DATE_EPOCH=SOURCE_DATE_EPOCH,
        FORCE_SOURCE_DATE="1",
    )
    cmd = [
        "latexmk",
        "-pdf",
        "-g",  # always recompile (environment variables are not tracked)
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-outdir={workdir}",
        str(tex),
    ]
    result = run_tool(cmd, cwd=ROOT, env=env)
    if result.returncode != 0:
        tail = "\n".join(result.stdout.splitlines()[-30:])
        raise BuildError(
            f"LaTeX error ({name}), log: {workdir / (name + '.log')}\n{tail}"
        )

    dest.mkdir(parents=True, exist_ok=True)
    pdf = dest / f"{name}.pdf"
    shutil.copyfile(workdir / f"{name}.pdf", pdf)
    return pdf


def page_count(pdf: Path) -> int:
    result = run_tool(["pdfinfo", str(pdf)])
    if result.returncode != 0:
        raise BuildError(f"pdfinfo error ({pdf.name}): {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise BuildError(f"Cannot read the page count: {pdf.name}")


def report(pdf: Path, extra: str = "") -> None:
    pages = page_count(pdf)
    warn = "  WARNING: longer than 1 page" if pages > 1 else ""
    print(f"  {pdf.relative_to(ROOT)}  ({pages} page(s){extra}){warn}")


# ---------------------------------------------------------------------------
# Build commands
# ---------------------------------------------------------------------------


def build_cv(
    variant: str, lang: str, dest: Path = DIST, app: dict | None = None
) -> Path:
    ctx = build_context(variant, lang, app)
    pdf = compile_pdf("cv.tex.j2", ctx, f"{ctx['base']['output']}_{lang}", dest)
    report(pdf)
    return pdf


def build_letter(
    variant: str, lang: str, dest: Path = DIST, app: dict | None = None
) -> Path:
    ctx = build_context(variant, lang, app)
    if not ctx["letter"].get("body"):
        raise BuildError(f"Empty letter body: {variant}/{lang}")
    pdf = compile_pdf(
        "cover_letter.tex.j2", ctx, f"{ctx['base']['letter_output']}_{lang}", dest
    )
    words = sum(len(p.split()) for p in ctx["letter"]["body"])
    lo, hi = LETTER_WORDS[lang]
    note = "" if lo <= words <= hi else f", recommended {lo}-{hi}"
    report(pdf, f", {words} words{note}")
    return pdf


def build_app(path: Path, photo: bool | None = None) -> None:
    if not path.is_file():
        raise BuildError(f"No such application file: {path}")
    app = load_yaml(path)
    unknown = set(app) - APP_KEYS
    if unknown:
        raise BuildError(
            f"Key(s) not allowed in an application file: {', '.join(sorted(unknown))}"
        )
    if photo is not None:
        app["photo"] = photo
    variant = app.get("extends", "developer")
    dest = DIST / "applications" / path.stem
    for lang in app.get("langs", list(LANGS)):
        build_cv(variant, lang, dest, app)
        build_letter(variant, lang, dest, app)


def build_all(app: dict | None = None) -> None:
    for variant in VARIANT_NAMES:
        for lang in LANGS:
            build_cv(variant, lang, app=app)
            build_letter(variant, lang, app=app)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("all", help="all 4 CVs and 4 fallback letters")
    for name in ("cv", "letter"):
        p = sub.add_parser(name)
        p.add_argument("--variant", choices=VARIANT_NAMES, default="developer")
        p.add_argument("--lang", choices=LANGS, default="en")
    p = sub.add_parser("app", help="application-specific CV and letter")
    p.add_argument("file", type=Path)
    for p in sub.choices.values():
        p.add_argument(
            "--photo",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="photo on/off (overrides the variant and application file)",
        )
    args = parser.parse_args(argv)
    override = {} if args.photo is None else {"photo": args.photo}

    try:
        if args.cmd == "all":
            build_all(override)
        elif args.cmd == "cv":
            build_cv(args.variant, args.lang, app=override)
        elif args.cmd == "letter":
            build_letter(args.variant, args.lang, app=override)
        else:
            build_app(args.file, args.photo)
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
