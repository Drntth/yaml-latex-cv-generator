"""Language pairs, variant values and tag filtering in content data."""

import pytest

from build import BuildError, resolve


def test_language_pair_resolves_to_the_requested_language():
    assert (
        resolve({"en": "Skills", "hu": "Készségek"}, "hu", "developer") == "Készségek"
    )


def test_missing_translation_names_the_language_and_the_location():
    with pytest.raises(BuildError, match=r"Missing translation \(hu\): cv.title"):
        resolve({"en": "Skills"}, "en", "developer", "cv.title")


def test_language_pair_with_extra_keys_is_rejected():
    # What YAML makes of {en: a, b, hu: c}: the unquoted comma adds a key "b".
    with pytest.raises(BuildError, match="Malformed language pair"):
        resolve({"en": "a", "b": None, "hu": "c"}, "en", "developer")


def test_variant_value_resolves_to_the_requested_variant():
    node = {"@developer": "Kotlin", "@general": "Office"}
    assert resolve(node, "en", "general") == "Office"


def test_variant_value_without_the_variant_is_none():
    assert resolve({"@developer": "Kotlin"}, "en", "general") is None


def test_tagged_items_are_kept_only_in_their_variants():
    items = [
        {"id": "a", "tags": ["developer"]},
        {"id": "b", "tags": ["general"]},
        {"id": "c"},
    ]
    assert resolve(items, "en", "general") == [{"id": "b"}, {"id": "c"}]


def test_list_items_resolving_to_none_are_dropped():
    items = [{"@developer": "x"}, "y"]
    assert resolve(items, "en", "general") == ["y"]


def test_nested_structures_resolve_recursively():
    node = {
        "role": {"en": "Developer", "hu": "Fejlesztő"},
        "tech": {"@developer": ["Kotlin"]},
    }
    assert resolve(node, "hu", "developer") == {"role": "Fejlesztő", "tech": ["Kotlin"]}
