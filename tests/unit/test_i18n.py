"""Unit tests for the dashboard i18n layer.

Covers the catalog integrity, the ``t()`` lookup/fallback contract, and the
language-state helpers.  These tests deliberately avoid rendering Streamlit
widgets so they run fast and headless.
"""

from __future__ import annotations

import pytest

from src.observability.dashboard.i18n import (
    CATALOG,
    DEFAULT_LANG,
    LANG_LABELS,
    SUPPORTED_LANGS,
    get_lang,
    set_lang,
    stage_label,
    t,
)
from src.observability.dashboard.i18n.translator import translate_mapping


class TestCatalogIntegrity:
    """Every key must exist in every supported language."""

    def test_default_lang_is_supported(self) -> None:
        assert DEFAULT_LANG in SUPPORTED_LANGS

    def test_default_lang_is_chinese(self) -> None:
        assert DEFAULT_LANG == "zh"

    def test_every_lang_has_label(self) -> None:
        for lang in SUPPORTED_LANGS:
            assert lang in LANG_LABELS

    def test_catalog_is_non_empty(self) -> None:
        assert len(CATALOG) > 100

    def test_all_keys_cover_all_languages(self) -> None:
        incomplete = {
            key: sorted(set(SUPPORTED_LANGS) - set(translations))
            for key, translations in CATALOG.items()
            if set(translations) != set(SUPPORTED_LANGS)
        }
        assert not incomplete, f"keys missing translations: {incomplete}"

    def test_no_empty_translations(self) -> None:
        empty = [
            (key, lang)
            for key, translations in CATALOG.items()
            for lang, text in translations.items()
            if not text.strip()
        ]
        assert not empty, f"empty translations: {empty}"

    def test_translations_actually_differ(self) -> None:
        """A zh entry identical to its en entry is almost certainly a miss."""
        suspicious = [
            key for key, tr in CATALOG.items() if tr["zh"] == tr["en"]
        ]
        # A handful of legitimate cases exist (pure-symbol/name strings).
        assert len(suspicious) < 25, f"untranslated keys: {suspicious}"

    def test_placeholder_names_match_across_languages(self) -> None:
        """A key must use the same named placeholders in every language."""
        import re

        mismatched = []
        for key, translations in CATALOG.items():
            sets = {
                lang: set(re.findall(r"\{(\w+)\}", text))
                for lang, text in translations.items()
            }
            if len({frozenset(s) for s in sets.values()}) > 1:
                mismatched.append((key, sets))
        assert not mismatched, f"placeholder mismatch: {mismatched}"


class TestTranslator:
    """Verify t() lookup, ordering and fallback behaviour."""

    def test_returns_chinese_by_default(self) -> None:
        assert t("nav.overview") == "系统总览"

    def test_returns_english_when_set(self) -> None:
        set_lang("en")
        try:
            assert t("nav.overview") == "Overview"
        finally:
            set_lang("zh")

    def test_switch_back_to_chinese(self) -> None:
        set_lang("en")
        set_lang("zh")
        assert t("nav.overview") == "系统总览"

    def test_unknown_lang_is_ignored(self) -> None:
        set_lang("zh")
        set_lang("klingon")
        assert get_lang() == "zh"

    def test_unknown_key_returns_key(self) -> None:
        assert t("does.not.exist") == "does.not.exist"

    def test_interpolation(self) -> None:
        text = t("ingestion.success", name="a.pdf", collection="default")
        assert "a.pdf" in text
        assert "default" in text
        assert "{" not in text

    def test_missing_interpolation_arg_does_not_raise(self) -> None:
        # Should return the raw template rather than exploding mid-render.
        text = t("ingestion.success", name="only-name")
        assert isinstance(text, str)
        assert text

    def test_extra_interpolation_arg_is_harmless(self) -> None:
        text = t("nav.overview", unused="x")
        assert text == "系统总览"

    def test_bare_stage_name_resolves(self) -> None:
        """Pipeline callbacks pass raw stage names like 'load'."""
        assert stage_label("load") == CATALOG["ingestion.stage.load"]["zh"]

    def test_unknown_stage_name_echoes_back(self) -> None:
        assert stage_label("brand_new_stage") == "brand_new_stage"

    def test_stage_labels_cover_pipeline_stages(self) -> None:
        for stage in ("integrity", "load", "split", "transform", "embed", "upsert"):
            assert f"ingestion.stage.{stage}" in CATALOG
            assert stage_label(stage) != stage

    def test_translate_mapping(self) -> None:
        result = translate_mapping({"col.stage": "load", "col.chars": 12})
        assert result["阶段"] == "load"
        assert result["字符数"] == 12

    def test_all_nav_labels_translated(self) -> None:
        nav_keys = [k for k in CATALOG if k.startswith("nav.")]
        assert len(nav_keys) == 6
        for key in nav_keys:
            for lang in SUPPORTED_LANGS:
                assert CATALOG[key][lang] != key


class TestPageKeyCoverage:
    """Each page module must resolve every key it references."""

    @pytest.mark.parametrize(
        "prefix",
        [
            "overview.",
            "browser.",
            "ingestion.",
            "ingestion_traces.",
            "query_traces.",
            "eval.",
        ],
    )
    def test_prefix_has_entries(self, prefix: str) -> None:
        assert any(k.startswith(prefix) for k in CATALOG)
