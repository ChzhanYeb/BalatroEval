"""规则层核心测试（vanilla 1.0.1o 子集）。

说明：本文件取代旧 ``test_w2_rules.py`` 中针对 L0 自定义公式的断言（``PAIR`` 得 28 等）。
替代依据：``docs/balatro/engine-gap.md`` 的 23 项差异表与 ``plan/01-任务进度.md`` W3 任务 3–4
明确要求“牌型基础 Chips×Mult + 计分牌筛选 + 等级 1”，旧断言记录的是被替代的 L0 公式，
因此不是“为了通过测试而改期望值”，而是规则版本升级（见 docs/implementation/testing-and-validation.md）。
"""
from __future__ import annotations

import unittest

from bench.hand_eval import (
    HandType,
    classify_hand,
    evaluate_hand,
    hand_contains_types,
    is_straight_ranks,
    scoring_card_indices,
)
from bench.jokers import CATALOG_BY_ID, condition_met
from bench.model import Card, Joker
from bench.rules_version import HAND_BASE_SCORE
from bench.scoring import score_hand


def C(rank: int, suit: int = 0) -> Card:
    return Card(suit=suit, rank=rank)


class TestHandClassification(unittest.TestCase):
    def test_high_card(self):
        self.assertEqual(classify_hand([C(2), C(7, 1), C(11, 2)]), HandType.HIGH_CARD)

    def test_pair(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1)]), HandType.PAIR)

    def test_two_pair(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(9, 2), C(9, 3)]), HandType.TWO_PAIR)

    def test_three_kind(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(7, 2)]), HandType.THREE_KIND)

    def test_straight(self):
        self.assertEqual(classify_hand([C(4, 0), C(5, 1), C(6, 2), C(7, 3), C(8, 0)]),
                         HandType.STRAIGHT)

    def test_flush(self):
        self.assertEqual(classify_hand([C(2, 1), C(4, 1), C(7, 1), C(9, 1), C(12, 1)]),
                         HandType.FLUSH)

    def test_full_house(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(7, 2), C(9, 0), C(9, 1)]),
                         HandType.FULL_HOUSE)

    def test_four_kind(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(7, 2), C(7, 3)]),
                         HandType.FOUR_KIND)

    def test_four_kind_with_kicker(self):
        self.assertEqual(classify_hand([C(8, 0), C(8, 1), C(8, 2), C(8, 3), C(4, 0)]),
                         HandType.FOUR_KIND)

    def test_straight_flush(self):
        self.assertEqual(classify_hand([C(4, 1), C(5, 1), C(6, 1), C(7, 1), C(8, 1)]),
                         HandType.STRAIGHT_FLUSH)

    def test_wheel_and_broadway(self):
        self.assertTrue(is_straight_ranks({1, 2, 3, 4, 5}))
        self.assertTrue(is_straight_ranks({1, 10, 11, 12, 13}))
        self.assertFalse(is_straight_ranks({11, 12, 13, 1, 2}))  # K-A-2-3-4 不合法

    def test_royal_flush_is_display_only(self):
        cards = [C(10, 2), C(11, 2), C(12, 2), C(13, 2), C(1, 2)]
        analysis = evaluate_hand(cards)
        self.assertEqual(analysis.hand_type, HandType.STRAIGHT_FLUSH)
        self.assertTrue(analysis.is_royal_flush)

    def test_five_kind_secret(self):
        # 标准 52 张不可达；用重复点数构造，验证分类代码路径（计分入口会拒绝重复 ID）。
        cards = [C(8, 0), C(8, 1), C(8, 2), C(8, 3), C(8, 0)]
        self.assertEqual(classify_hand(cards), HandType.FIVE_KIND)

    def test_flush_house_secret(self):
        cards = [C(8, 0), C(8, 0), C(8, 0), C(9, 0), C(9, 0)]
        self.assertEqual(classify_hand(cards), HandType.FLUSH_HOUSE)

    def test_flush_five_secret(self):
        cards = [C(8, 0)] * 5
        self.assertEqual(classify_hand(cards), HandType.FLUSH_FIVE)


class TestScoringCards(unittest.TestCase):
    def test_high_card_only_highest_scores(self):
        cards = [C(1, 0), C(13, 1), C(12, 2), C(11, 3), C(9, 0)]
        indices = scoring_card_indices(cards, HandType.HIGH_CARD)
        self.assertEqual(indices, (0,))
        self.assertEqual(score_hand(cards).chips, 5 + 11)  # 基础 5 + A 的 11

    def test_pair_ignores_kickers(self):
        cards = [C(7, 0), C(7, 1), C(2, 2), C(4, 3), C(9, 0)]
        self.assertEqual(scoring_card_indices(cards, HandType.PAIR), (0, 1))
        self.assertEqual(score_hand(cards).chips, 10 + 14)

    def test_two_pair_scores_four(self):
        cards = [C(7, 0), C(7, 1), C(9, 2), C(9, 3), C(13, 0)]
        self.assertEqual(scoring_card_indices(cards, HandType.TWO_PAIR), (0, 1, 2, 3))

    def test_four_kind_kicker_not_scored(self):
        cards = [C(8, 0), C(8, 1), C(8, 2), C(8, 3), C(4, 0)]
        self.assertEqual(scoring_card_indices(cards, HandType.FOUR_KIND), (0, 1, 2, 3))
        self.assertEqual(score_hand(cards).final_score, (60 + 32) * 7)

    def test_full_house_scores_all_five(self):
        cards = [C(8, 0), C(8, 1), C(8, 2), C(9, 0), C(9, 1)]
        self.assertEqual(scoring_card_indices(cards, HandType.FULL_HOUSE), (0, 1, 2, 3, 4))


class TestBaseScoreTable(unittest.TestCase):
    def test_level1_table_matches_rules(self):
        expected = {
            "high_card": (5, 1), "pair": (10, 2), "two_pair": (20, 2),
            "three_kind": (30, 3), "straight": (30, 4), "flush": (35, 4),
            "full_house": (40, 4), "four_kind": (60, 7), "straight_flush": (100, 8),
            "five_kind": (120, 12), "flush_house": (140, 14), "flush_five": (160, 16),
        }
        self.assertEqual(HAND_BASE_SCORE, expected)

    def test_reachable_hand_base_scores(self):
        cases = {
            HandType.HIGH_CARD: [C(2, 0), C(5, 1)],
            HandType.PAIR: [C(7, 0), C(7, 1)],
            HandType.TWO_PAIR: [C(7, 0), C(7, 1), C(9, 2), C(9, 3)],
            HandType.THREE_KIND: [C(7, 0), C(7, 1), C(7, 2)],
            HandType.STRAIGHT: [C(4, 0), C(5, 1), C(6, 2), C(7, 3), C(8, 0)],
            HandType.FLUSH: [C(2, 1), C(4, 1), C(7, 1), C(9, 1), C(12, 1)],
            HandType.FULL_HOUSE: [C(7, 0), C(7, 1), C(7, 2), C(9, 0), C(9, 1)],
            HandType.FOUR_KIND: [C(7, 0), C(7, 1), C(7, 2), C(7, 3)],
            HandType.STRAIGHT_FLUSH: [C(4, 1), C(5, 1), C(6, 1), C(7, 1), C(8, 1)],
        }
        for hand_type, cards in cases.items():
            with self.subTest(hand_type=hand_type):
                analysis = evaluate_hand(cards)
                self.assertEqual(analysis.hand_type, hand_type)
                self.assertEqual((analysis.base_chips, analysis.base_mult),
                                 HAND_BASE_SCORE[hand_type.value])


class TestGoldenScoring(unittest.TestCase):
    def test_pair_7h7d_is_48(self):
        result = score_hand([C(7, 1), C(7, 2)])
        self.assertEqual(result.hand_type, HandType.PAIR)
        self.assertEqual((result.chips, str(result.mult)), (24, "2"))
        self.assertEqual(result.final_score, 48)
        self.assertEqual([e["phase"] for e in result.trace],
                         ["hand_base", "scoring_cards", "final_score"])

    def test_joker_plus_duo_order_matters(self):
        cards = [C(7, 1), C(7, 2)]
        add = CATALOG_BY_ID["joker"]      # +4 Mult
        duo = CATALOG_BY_ID["the_duo"]    # x2 Mult
        add_then_x = score_hand(cards, [add, duo])
        x_then_add = score_hand(cards, [duo, add])
        self.assertEqual((add_then_x.final_score, x_then_add.final_score), (288, 192))

    def test_three_kind_with_jokers(self):
        cards = [C(8, 0), C(8, 1), C(8, 2)]
        result = score_hand(cards, [CATALOG_BY_ID["joker"], CATALOG_BY_ID["jolly_joker"]])
        self.assertEqual((result.chips, str(result.mult)), (54, "15"))
        self.assertEqual(result.final_score, 810)

    def test_two_pair_boss_golden(self):
        cards = [C(1, 0), C(1, 1), C(13, 2), C(13, 3)]
        result = score_hand(cards, [CATALOG_BY_ID["joker"], CATALOG_BY_ID["the_duo"]])
        self.assertEqual(result.final_score, 744)  # (20+42) * (2+4)*2

    def test_fractional_mult_floor_once(self):
        cards = [C(7, 1), C(7, 2), C(3, 0)]  # pair + kicker：chips 10+14=24
        result = score_hand(cards, [Joker("test_x15", "x", "mul_mult", 150)])
        self.assertEqual(result.chips, 24)
        self.assertEqual(str(result.mult), "3")  # 2 * 1.5
        self.assertEqual(result.final_score, 72)

    def test_score_does_not_mutate_inputs(self):
        cards = [C(7, 1), C(7, 2)]
        jokers = [CATALOG_BY_ID["joker"]]
        before_cards, before_jokers = list(cards), list(jokers)
        score_hand(cards, jokers)
        self.assertEqual(cards, before_cards)
        self.assertEqual(jokers, before_jokers)

    def test_duplicate_card_ids_rejected_by_scoring(self):
        from bench.errors import InvalidActionError
        with self.assertRaises(InvalidActionError):
            score_hand([C(7, 0), C(7, 0)])


class TestJokerConditions(unittest.TestCase):
    def _analysis(self, cards):
        return evaluate_hand(cards)

    def test_joker_always(self):
        analysis = self._analysis([C(2, 0), C(5, 1)])
        self.assertTrue(condition_met(CATALOG_BY_ID["joker"], analysis, 2))

    def test_jolly_requires_pair_or_superset(self):
        jolly = CATALOG_BY_ID["jolly_joker"]
        pair = self._analysis([C(7, 0), C(7, 1), C(3, 2)])
        high = self._analysis([C(7, 0), C(3, 1), C(2, 2)])
        three = self._analysis([C(8, 0), C(8, 1), C(8, 2)])
        self.assertTrue(condition_met(jolly, pair, 3))
        self.assertTrue(condition_met(jolly, three, 3))  # contains Pair
        self.assertFalse(condition_met(jolly, high, 3))

    def test_zany_requires_three(self):
        zany = CATALOG_BY_ID["zany_joker"]
        self.assertTrue(condition_met(zany, self._analysis([C(8, 0), C(8, 1), C(8, 2)]), 3))
        self.assertFalse(condition_met(zany, self._analysis([C(8, 0), C(8, 1)]), 2))

    def test_half_joker_cards_le_3(self):
        half = CATALOG_BY_ID["half_joker"]
        analysis = self._analysis([C(8, 0), C(8, 1), C(8, 2)])
        self.assertTrue(condition_met(half, analysis, 3))
        self.assertFalse(condition_met(half, analysis, 4))

    def test_sly_and_wily(self):
        sly, wily = CATALOG_BY_ID["sly_joker"], CATALOG_BY_ID["wily_joker"]
        pair = self._analysis([C(7, 0), C(7, 1)])
        three = self._analysis([C(8, 0), C(8, 1), C(8, 2)])
        self.assertTrue(condition_met(sly, pair, 2))
        # 三条“包含”对子（structural-superset 口径，见 CONTAINS_POLICY；该口径标 UNVERIFIED），
        # 因此 Sly 在三条上也会触发。
        self.assertTrue(condition_met(sly, three, 3))
        self.assertTrue(condition_met(wily, three, 3))

    def test_duo_and_trio_conditions(self):
        duo, trio = CATALOG_BY_ID["the_duo"], CATALOG_BY_ID["the_trio"]
        pair = self._analysis([C(7, 0), C(7, 1)])
        three = self._analysis([C(8, 0), C(8, 1), C(8, 2)])
        self.assertTrue(condition_met(duo, pair, 2))
        # 三条含对子 → Duo 触发（structural-superset 口径，UNVERIFIED）。
        self.assertTrue(condition_met(duo, three, 3))
        self.assertTrue(condition_met(trio, three, 3))


class TestContainsRelation(unittest.TestCase):
    def test_three_contains_pair(self):
        contains = hand_contains_types([C(8, 0), C(8, 1), C(8, 2)])
        self.assertIn(HandType.PAIR, contains)
        self.assertIn(HandType.THREE_KIND, contains)

    def test_four_kind_does_not_contain_two_pair(self):
        contains = hand_contains_types([C(8, 0), C(8, 1), C(8, 2), C(8, 3), C(4, 0)])
        self.assertIn(HandType.PAIR, contains)
        self.assertIn(HandType.THREE_KIND, contains)
        self.assertNotIn(HandType.TWO_PAIR, contains)

    def test_five_kind_does_not_contain_full_house(self):
        contains = hand_contains_types([C(8, 0)] * 5)
        self.assertIn(HandType.FIVE_KIND, contains)
        self.assertNotIn(HandType.FULL_HOUSE, contains)

    def test_flush_house_and_flush_five_contains(self):
        fh = hand_contains_types([C(8, 0)] * 3 + [C(9, 0)] * 2)
        self.assertIn(HandType.FULL_HOUSE, fh)
        self.assertIn(HandType.FLUSH, fh)
        ff = hand_contains_types([C(8, 0)] * 5)
        self.assertIn(HandType.FLUSH_FIVE, ff)
        self.assertNotIn(HandType.FLUSH_HOUSE, ff)

    def test_straight_flush_contains_both(self):
        contains = hand_contains_types([C(r, 1) for r in (4, 5, 6, 7, 8)])
        self.assertIn(HandType.STRAIGHT, contains)
        self.assertIn(HandType.FLUSH, contains)
        self.assertIn(HandType.STRAIGHT_FLUSH, contains)


if __name__ == "__main__":
    unittest.main()
