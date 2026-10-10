"""Missing image files are reported before LaTeX runs."""

import shutil

import pytest

import build


def test_missing_photo_file_is_a_build_error(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "ASSETS", tmp_path)
    with pytest.raises(build.BuildError, match="avatar.jpg"):
        build.build_context("developer", "en")


def test_photo_off_needs_no_photo_file(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "ASSETS", tmp_path)
    ctx = build.build_context("developer", "en", {"photo": False})
    assert ctx["photo"] is False


def test_missing_signature_file_is_a_build_error(tmp_path, monkeypatch):
    content = tmp_path / "content"
    shutil.copytree(build.CONTENT, content)
    profile = content / "profile.yaml"
    profile.write_text(
        profile.read_text(encoding="utf-8") + "signature_file: signature.png\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(build, "CONTENT", content)
    with pytest.raises(build.BuildError, match="signature.png"):
        build.build_context("developer", "en")
