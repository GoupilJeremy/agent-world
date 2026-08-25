"""Tests for portable, content-based output filenames."""

from datetime import date, datetime, timedelta, timezone

import pytest

from backend.services.file_naming import generate_filename, slugify_component


def test_generate_filename_uses_content_and_injected_date() -> None:
    filename = generate_filename(
        "Résumé : analyse des ventes 2026 !",
        now=datetime(2026, 8, 6, 23, 30, tzinfo=timezone.utc),
    )

    assert filename == "resume_analyse_des_ventes_2026_20260806.json"


def test_aware_datetime_is_normalized_to_utc_at_day_boundary() -> None:
    local_time = datetime(
        2026,
        8,
        26,
        1,
        30,
        tzinfo=timezone(timedelta(hours=3)),
    )

    assert generate_filename("Report", now=local_time) == "report_20260825.json"


def test_naive_datetime_keeps_its_calendar_date() -> None:
    local_calendar_value = datetime(2026, 8, 26, 1, 30)

    assert (
        generate_filename("Report", now=local_calendar_value) == "report_20260826.json"
    )


@pytest.mark.parametrize("extension", ["json", ".MD", " txt "])
def test_generate_filename_supports_common_formats(extension: str) -> None:
    filename = generate_filename("Weekly report", extension, now=date(2026, 8, 25))

    assert filename == f"weekly_report_20260825.{extension.strip().lstrip('.').lower()}"


def test_generate_filename_supports_sanitized_prefix_and_suffix() -> None:
    filename = generate_filename(
        "Analyse / ventes",
        "md",
        prefix="Rapport client",
        suffix="Final #1",
        now=date(2026, 8, 25),
    )

    assert filename == "rapport_client_analyse_ventes_final_1_20260825.md"


@pytest.mark.parametrize("content", ["", "   ", "💡🚀", "///\\\\"])
def test_non_transliterable_content_uses_fallback(content: str) -> None:
    assert (
        generate_filename(content, now=date(2026, 8, 25))
        == "agent_output_20260825.json"
    )


def test_generated_names_are_length_bounded() -> None:
    filename = generate_filename(
        "word " * 200,
        prefix="prefix " * 20,
        suffix="suffix " * 20,
        now=date(2026, 8, 25),
    )

    assert len(filename) <= 134
    assert filename.endswith("_20260825.json")


@pytest.mark.parametrize("extension", ["", "yaml", "../json", "json.exe"])
def test_unsupported_extensions_are_rejected(extension: str) -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        generate_filename("report", extension)


def test_non_string_inputs_are_rejected() -> None:
    with pytest.raises(TypeError, match="content"):
        generate_filename(42)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="prefix"):
        generate_filename("report", prefix=42)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "expected"),
    [("CON", "_con"), ("lpt1", "_lpt1"), ("normal", "normal")],
)
def test_windows_reserved_components_are_escaped(value: str, expected: str) -> None:
    assert slugify_component(value) == expected


@pytest.mark.parametrize(
    ("fallback", "expected"),
    [
        ("../../Emergency Output", "emergency_output"),
        ("CON", "_con"),
        ("///", "output"),
    ],
)
def test_slug_fallback_is_sanitized(fallback: str, expected: str) -> None:
    assert slugify_component("!!!", fallback=fallback) == expected


def test_slug_fallback_type_is_validated() -> None:
    with pytest.raises(TypeError, match="fallback"):
        slugify_component("", fallback=42)  # type: ignore[arg-type]
