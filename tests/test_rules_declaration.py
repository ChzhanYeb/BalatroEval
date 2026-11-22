"""规则声明一致性测试：代码（Ruleset）↔ JSON 镜像 ↔ RULES_VERSION 文档不得漂移。"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from bench.jokers import VANILLA_JOKERS
from bench.rules_version import (
    ANTE1_BLINDS,
    HAND_BASE_SCORE,
    SHOP_EXTENSION,
    VANILLA_SUBSET_V1,
    ruleset_for,
)

ROOT = Path(__file__).resolve().parents[1]


class TestRulesDeclaration(unittest.TestCase):
    def test_json_mirror_matches_ruleset(self):
        mirror = json.loads((ROOT / "scenarios" / "rules_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(mirror, VANILLA_SUBSET_V1.to_dict())

    def test_rules_version_doc_mentions_active_version(self):
        text = (ROOT / "scenarios" / "RULES_VERSION").read_text(encoding="utf-8")
        self.assertIn("rules_version: vanilla_1.0.1o_subset_v1", text)
        self.assertIn("verification_status: NOT_VERIFIED", text)
        self.assertIn("legacy_w2_l0", text)  # 历史声明保留

    def test_blind_targets_are_ante1(self):
        self.assertEqual([b.target for b in ANTE1_BLINDS], [300, 450, 600])
        self.assertEqual([b.kind for b in ANTE1_BLINDS], ["small", "big", "boss"])
        self.assertEqual({b.base_score for b in ANTE1_BLINDS}, {300})
        # 旧 L0 的 300/800/2000 不得再作为三盲注
        self.assertNotIn(800, [b.target for b in ANTE1_BLINDS])

    def test_resources_and_slots(self):
        rules = VANILLA_SUBSET_V1
        self.assertEqual((rules.hands_per_blind, rules.discards_per_blind), (4, 4))
        self.assertEqual((rules.hand_size, rules.joker_slots), (8, 5))
        self.assertEqual(rules.deck, "red")
        self.assertEqual(rules.stake, "white")

    def test_hand_base_table_matches_docs(self):
        expected = {
            "high_card": (5, 1), "pair": (10, 2), "two_pair": (20, 2),
            "three_kind": (30, 3), "straight": (30, 4), "flush": (35, 4),
            "full_house": (40, 4), "four_kind": (60, 7), "straight_flush": (100, 8),
            "five_kind": (120, 12), "flush_house": (140, 14), "flush_five": (160, 16),
        }
        self.assertEqual(HAND_BASE_SCORE, expected)

    def test_eight_vanilla_jokers_are_exactly_declared(self):
        expected = {
            "joker": ("add_mult", 4, "always"),
            "jolly_joker": ("add_mult", 8, "contains_pair"),
            "zany_joker": ("add_mult", 12, "contains_three"),
            "sly_joker": ("add_chips", 50, "contains_pair"),
            "wily_joker": ("add_chips", 100, "contains_three"),
            "half_joker": ("add_mult", 20, "cards_le_3"),
            "the_duo": ("mul_mult", 200, "contains_pair"),
            "the_trio": ("mul_mult", 300, "contains_three"),
        }
        actual = {j.jid: (j.kind, j.value, j.condition) for j in VANILLA_JOKERS}
        self.assertEqual(actual, expected)
        self.assertEqual(len(VANILLA_JOKERS), 8)

    def test_exclusions_include_known_gaps(self):
        for name in ("money", "shop_economy", "boss_effects", "consumables_tarot_planet_spectral",
                     "card_enhancements", "hand_levels_gt1"):
            self.assertIn(name, VANILLA_SUBSET_V1.excluded)

    def test_ruleset_extension_only_shop(self):
        enabled = ruleset_for([SHOP_EXTENSION])
        self.assertTrue(enabled.shop_enabled)
        self.assertFalse(VANILLA_SUBSET_V1.shop_enabled)
        with self.assertRaises(ValueError):
            ruleset_for(["unknown_extension"])

    def test_signature_is_stable_and_content_sensitive(self):
        sig = VANILLA_SUBSET_V1.signature()
        self.assertEqual(len(sig), 64)
        self.assertEqual(sig, VANILLA_SUBSET_V1.signature())
        modified = ruleset_for([SHOP_EXTENSION])
        self.assertNotEqual(sig, modified.signature())


if __name__ == "__main__":
    unittest.main()
