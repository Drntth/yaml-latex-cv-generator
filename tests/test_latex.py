"""LaTeX escaping and template rendering with the custom delimiters."""

import pytest

from build import ENV, BuildError, latex_escape


def test_special_characters_are_escaped():
    assert latex_escape("R&D 100% #1 a_b $5") == r"R\&D 100\% \#1 a\_b \$5"


def test_backslash_and_braces_are_escaped():
    assert latex_escape(r"\x{y}") == r"\textbackslash{}x\{y\}"


def test_double_asterisks_become_bold():
    assert latex_escape("use **Kotlin** daily") == r"use \textbf{Kotlin} daily"


def test_unbalanced_bold_marker_is_a_build_error():
    with pytest.raises(BuildError, match="Odd number of"):
        latex_escape("**Kotlin daily")


def test_template_variables_are_escaped_on_output():
    template = ENV.from_string(r"\textbf{\VAR{name}}")
    assert template.render(name="A & B") == r"\textbf{A \& B}"


def test_missing_value_renders_as_empty_text():
    assert ENV.from_string(r"[\VAR{nothing}]").render() == "[]"


def test_url_filter_keeps_the_url_and_escapes_only_percent_and_hash():
    template = ENV.from_string(r"\href{\VAR{u|url}}{x}")
    url = "https://example.com/a_b%20c#top"
    assert template.render(u=url) == r"\href{https://example.com/a_b\%20c\#top}{x}"


def test_block_tags_leave_no_blank_lines():
    template = ENV.from_string("\\BLOCK{for i in items}\n\\VAR{i}\n\\BLOCK{endfor}\n")
    assert template.render(items=["a", "b"]) == "a\nb\n"
