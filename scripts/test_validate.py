import unittest

from scripts.validate import bootstrap_profile_contract, is_canonical_locale


class LocaleValidationTests(unittest.TestCase):
    def test_accepts_canonical_locales_and_reserved_neutral(self) -> None:
        for locale in ("fr-FR", "en-US", "zh-Hant-TW", "neutral"):
            with self.subTest(locale=locale):
                self.assertTrue(is_canonical_locale(locale))

    def test_rejects_non_canonical_or_invalid_locales(self) -> None:
        for locale in ("fr-fr", "EN-US", "fr_FR", "neutral-FR", "fr-"):
            with self.subTest(locale=locale):
                self.assertFalse(is_canonical_locale(locale))


class BootstrapProfileContractTests(unittest.TestCase):
    def test_contract_is_independent_of_binding_order_and_user_facing_text(self) -> None:
        first = {
            "metadata": {"name": "sample"},
            "definition": {
                "displayName": "Exemple",
                "targetScope": "workspace",
                "bindings": [
                    {"name": "runtime", "targetKind": "runtimeProfile"},
                    {"name": "model", "targetKind": "modelProfile", "required": True},
                ],
            },
        }
        translated = {
            "metadata": {"name": "sample"},
            "definition": {
                "displayName": "Sample",
                "targetScope": "workspace",
                "bindings": list(reversed(first["definition"]["bindings"])),
            },
        }

        self.assertEqual(
            bootstrap_profile_contract(first, "first"),
            bootstrap_profile_contract(translated, "translated"),
        )

    def test_contract_changes_when_a_binding_changes(self) -> None:
        first = {
            "metadata": {"name": "sample"},
            "definition": {
                "targetScope": "workspace",
                "bindings": [{"name": "model", "targetKind": "modelProfile"}],
            },
        }
        changed = {
            "metadata": {"name": "sample"},
            "definition": {
                "targetScope": "workspace",
                "bindings": [{"name": "model", "targetKind": "runtimeProfile"}],
            },
        }

        self.assertNotEqual(
            bootstrap_profile_contract(first, "first"),
            bootstrap_profile_contract(changed, "changed"),
        )


if __name__ == "__main__":
    unittest.main()
