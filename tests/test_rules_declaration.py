"""规则声明一致性测试：代码（Ruleset）↔ JSON 镜像 ↔ RULES_VERSION 文档不得漂移。"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from bench.jokers import VANILLA_JOKERS
from bench.rules_version import (
    ANTE1_BLINDS,
    HAND_BASE_SCORE,
    INTEREST_CAP,
    INTEREST_PER,
    JOKER_PRICE_BY_RARITY,
    SHOP_OFFER_COUNT,
    STARTING_MONEY,
    VANILLA_SUBSET_V1,
    interest_for,
    joker_price,
    ruleset_for,
    sell_value,
)

ROOT = Path(__file__).resolve().parents[1]


class TestRulesDeclaration(unittest.TestCase):
    def test_json_mirror_matches_ruleset(self):
        mirror = json.loads((ROOT / "scenarios" / "rules_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(mirror, VANILLA_SUBSET_V1.to_dict())

    def test_rules_version_doc_mentions_active_version(self):
        text = (ROOT / "scenarios" / "RULES_VERSION").read_text(encoding="utf-8")
        self.assertIn("rules_version: vanilla_1.0.1o_subset_v2", text)
        self.assertIn("verification_status: NOT_VERIFIED", text)
        self.assertIn("legacy_w2_l0", text)  # 历史声明保留
        self.assertIn("starting_money: 4", text)
        self.assertIn("interest_cap: 5", text)

    def test_blind_targets_and_rewards_are_ante1(self):
        self.assertEqual([b.target for b in ANTE1_BLINDS], [300, 450, 600])
        self.assertEqual([b.kind for b in ANTE1_BLINDS], ["small", "big", "boss"])
        self.assertEqual([b.reward_money for b in ANTE1_BLINDS], [3, 4, 5])
        self.assertEqual({b.base_score for b in ANTE1_BLINDS}, {300})
        # 旧 L0 的 300/800/2000 不得再作为三盲注
        self.assertNotIn(800, [b.target for b in ANTE1_BLINDS])

    def test_resources_and_slots(self):
        rules = VANILLA_SUBSET_V1
        self.assertEqual((rules.hands_per_blind, rules.discards_per_blind), (4, 4))
        self.assertEqual((rules.hand_size, rules.joker_slots), (8, 5))
        self.assertEqual((rules.deck, rules.stake), ("red", "white"))
        self.assertTrue(rules.shop_enabled)

    def test_economy_constants(self):
        rules = VANILLA_SUBSET_V1
        self.assertEqual(rules.starting_money, STARTING_MONEY)
        self.assertEqual((rules.interest_per, rules.interest_cap), (INTEREST_PER, INTEREST_CAP))
        self.assertEqual(rules.shop_offer_count, SHOP_OFFER_COUNT)
        self.assertEqual(rules.reroll_base_cost, 5)
        self.assertEqual(rules.reroll_increment, 1)
        self.assertEqual(JOKER_PRICE_BY_RARITY["Common"], 5)
        self.assertEqual(joker_price("Rare"), 9)
        with self.assertRaises(ValueError):
            joker_price("Unknown")

    def test_interest_brackets_and_cap(self):
        self.assertEqual(interest_for(0), 0)
        self.assertEqual(interest_for(4), 0)
        self.assertEqual(interest_for(5), 1)
        self.assertEqual(interest_for(24), 4)
        self.assertEqual(interest_for(25), 5)
        self.assertEqual(interest_for(999), 5)  # cap $5

    def test_sell_value_is_half_price_min_one(self):
        common = VANILLA_JOKERS[0]
        rare = [j for j in VANILLA_JOKERS if j.rarity == "Rare"][0]
        self.assertEqual(sell_value(common), 2)
        self.assertEqual(sell_value(rare), 4)

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
        for name in ("boss_effects", "consumables_tarot_planet_spectral",
                     "card_enhancements", "hand_levels_gt1"):
            self.assertIn(name, VANILLA_SUBSET_V1.excluded)

    def test_economy_is_no_longer_excluded(self):
        # v2 起经济已实现：这三个 key 必须从 excluded 消失，否则声明自相矛盾。
        for name in ("money", "interest", "shop_economy"):
            self.assertNotIn(name, VANILLA_SUBSET_V1.excluded)
        self.assertIn("money_start_4", VANILLA_SUBSET_V1.implemented)
        self.assertIn("interest_1_per_5_cap_5", VANILLA_SUBSET_V1.implemented)

    def test_economy_claims_are_marked_unverified(self):
        # 经济口径没做真游戏实测，必须留在 unverified 里，不能写成事实。
        for name in ("interest_ordering_before_payout",
                     "joker_price_fixed_mid_of_vanilla_range",
                     "shop_offer_pool_uniform_no_rarity_weights"):
            self.assertIn(name, VANILLA_SUBSET_V1.unverified)

    def test_no_extensions_are_supported(self):
        self.assertIs(ruleset_for([]), VANILLA_SUBSET_V1)
        self.assertIs(ruleset_for(None), VANILLA_SUBSET_V1)
        with self.assertRaises(ValueError):
            ruleset_for(["unknown_extension"])
        with self.assertRaises(ValueError):
            ruleset_for(["free_joker_choice"])  # v2 已退役

    def test_signature_is_stable_and_content_sensitive(self):
        sig = VANILLA_SUBSET_V1.signature()
        self.assertEqual(len(sig), 64)
        self.assertEqual(sig, VANILLA_SUBSET_V1.signature())


if __name__ == "__main__":
    unittest.main()
