from video_compressor.gui.i18n.translations import t


class TestTranslationManager:
    def test_default_language(self, translation_manager):
        assert translation_manager.get_language() == "en"

    def test_supported_languages(self, translation_manager):
        langs = translation_manager.get_supported_languages()
        assert "en" in langs
        assert "ja" in langs

    def test_set_language_ja(self, translation_manager):
        translation_manager.set_language("ja")
        assert translation_manager.get_language() == "ja"

    def test_set_language_en(self, translation_manager):
        translation_manager.set_language("ja")
        translation_manager.set_language("en")
        assert translation_manager.get_language() == "en"

    def test_set_invalid_language(self, translation_manager):
        import pytest

        with pytest.raises(ValueError, match="Unsupported language"):
            translation_manager.set_language("fr")

    def test_translate_simple_key(self, translation_manager):
        assert translation_manager.translate("app.title") == "AmeCompression"

    def test_translate_nested_key(self, translation_manager):
        result = translation_manager.translate("volume.modes.disabled")
        assert result == "Disabled"

    def test_translate_with_format(self, translation_manager):
        result = translation_manager.translate("app.version", version="1.0.0")
        assert "1.0.0" in result

    def test_translate_missing_key(self, translation_manager):
        result = translation_manager.translate("nonexistent.key")
        assert result == "nonexistent.key"

    def test_translate_japanese(self, translation_manager):
        translation_manager.set_language("ja")
        result = translation_manager.translate("nav.video")
        assert result == "動画圧縮"

    def test_translate_fallback(self, translation_manager):
        translation_manager.set_language("en")
        result = translation_manager.translate("app.title")
        assert result == "AmeCompression"


class TestTHelper:
    def test_t_function(self, translation_manager):
        result = t("app.title")
        assert result == "AmeCompression"

    def test_t_function_ja(self, translation_manager):
        translation_manager.set_language("ja")
        result = t("nav.settings")
        assert result == "設定"

    def test_t_function_with_format(self, translation_manager):
        result = t("compress.batch_success", count=5)
        assert "5" in result


class TestTranslationKeys:
    def test_all_en_and_ja_keys_match(self, translation_manager):
        import json
        from pathlib import Path

        i18n_dir = Path(__file__).parent.parent / "video_compressor" / "gui" / "i18n"
        with open(i18n_dir / "en.json", encoding="utf-8") as f:
            en = json.load(f)
        with open(i18n_dir / "ja.json", encoding="utf-8") as f:
            ja = json.load(f)

        def collect_keys(d, prefix=""):
            keys = set()
            for k, v in d.items():
                full = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.update(collect_keys(v, full))
                else:
                    keys.add(full)
            return keys

        en_keys = collect_keys(en)
        ja_keys = collect_keys(ja)
        assert en_keys == ja_keys, (
            f"Key mismatch: en-only={en_keys - ja_keys}, ja-only={ja_keys - en_keys}"
        )
