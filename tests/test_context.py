"""Context building from the sample content, variants and application overrides."""

import shutil

import pytest

import build
from build import BuildError, build_app, build_context


@pytest.mark.parametrize("variant", build.VARIANT_NAMES)
@pytest.mark.parametrize("lang", build.LANGS)
def test_sample_content_resolves_for_every_variant_and_language(variant, lang):
    ctx = build_context(variant, lang)
    assert ctx["title"] and ctx["summary"] and ctx["letter"]["body"]


def test_variant_selects_its_tagged_items():
    general = build_context("general", "en")
    assert [e["id"] for e in general["experience"]] == [
        "example-apps",
        "sample-studio",
        "library",
    ]
    assert build_context("developer", "en")["projects"][0]["id"] == "trail-app"
    assert general["projects"] == []


def test_application_can_hide_an_item():
    ctx = build_context("developer", "en", {"hide": ["certificates:cert-a11y"]})
    assert [c["id"] for c in ctx["certificates"]] == ["cert-mobile"]


def test_application_can_reorder_skill_groups():
    ctx = build_context("developer", "en", {"skills_order": ["tools", "languages"]})
    assert [s["id"] for s in ctx["skills"]][:2] == ["tools", "languages"]


def test_application_title_overrides_the_variant_title():
    ctx = build_context("developer", "hu", {"title": {"en": "X", "hu": "Y"}})
    assert ctx["title"] == "Y"


def test_letter_date_is_formatted_per_language():
    assert build_context("developer", "en")["letter"]["place_date"] == (
        "Example City, 15 January 2026"
    )
    assert build_context("developer", "hu")["letter"]["place_date"] == (
        "Example City, 2026. január 15."
    )


def test_unknown_section_is_a_build_error():
    with pytest.raises(BuildError, match="Unknown section"):
        build_context("developer", "en", {"sections": ["summary", "hobbies"]})


def test_unknown_variant_is_a_build_error():
    with pytest.raises(BuildError, match="Unknown variant"):
        build_context("designer", "en")


def test_application_file_with_a_fact_key_is_rejected(tmp_path):
    app = tmp_path / "2026-01-15-example.yaml"
    app.write_text("extends: developer\nexperience: []\n", encoding="utf-8")
    with pytest.raises(BuildError, match="not allowed.*experience"):
        build_app(app)


def test_skills_order_without_a_skills_section_is_ignored(tmp_path, monkeypatch):
    content = tmp_path / "content"
    shutil.copytree(build.CONTENT, content)
    cv = content / "cv.yaml"
    text = cv.read_text(encoding="utf-8")
    start, end = text.index("\nskills:"), text.index("\ncertificates:")
    cv.write_text(text[:start] + text[end:], encoding="utf-8")
    monkeypatch.setattr(build, "CONTENT", content)
    ctx = build_context("developer", "en", {"skills_order": ["tools"]})
    assert "skills" not in ctx
