"""Scenario schema/loader/validator 测试：合法场景可执行，非法场景被显式拒绝。"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from bench.errors import InvalidActionError, UnsupportedRuleError
from scenarios.loader import load_scenarios, scenario_from_dict, to_reset_spec
from scenarios.schema import Scenario
from scenarios.validator import validate_scenario
from tests.tmp_utils import workspace_tmp

DEV_DIR = Path(__file__).resolve().parents[1] / "scenarios" / "dev"


def base_dict(**overrides) -> dict:
    data = {
        "scenario_schema_version": 2,
        "scenario_id": "test-scenario",
        "rules_version": "vanilla_1.0.1o_subset_v2",
        "seed": 1,
        "origin": "synthetic_dev",
        "decision_type": "play",
        "goal": {"type": "reach_score", "target": 48},
        "initial_state": {
            "hand_ids": ["c7h", "c7d", "c9s", "c9d", "c13h", "c2c", "c5s", "c11d"],
            "joker_ids": [],
            "blind_idx": 0,
            "total_score": 0,
            "hands_left": 4,
            "discards_left": 4,
            "target": 300,
            "money": None,
            "shop_open": False,
        },
        "constraints": {"max_steps": 1, "allowed_action_kinds": ["play"]},
        "extensions": [],
        "boss_blind": None,
        "metadata": {"description": "unit test"},
    }
    data.update(overrides)
    return data


class TestLoadDevScenarios(unittest.TestCase):
    def test_all_dev_scenarios_load(self):
        scenarios = load_scenarios(DEV_DIR)
        self.assertGreaterEqual(len(scenarios), 5)
        ids = {s.scenario_id for s in scenarios}
        self.assertIn("dev-play-pair-7h7d", ids)
        self.assertIn("dev-episode-ante1-red-seed20261117", ids)
        self.assertIn("dev-episode-economy-seed20261112", ids)
        self.assertIn("dev-shop-buy-or-bank", ids)

    def test_reset_spec_for_decision_point(self):
        scenarios = {s.scenario_id: s for s in load_scenarios(DEV_DIR)}
        spec = to_reset_spec(scenarios["dev-play-pair-7h7d"])
        self.assertEqual(spec.allowed_action_kinds, ("play",))
        self.assertTrue(spec.ruleset.shop_enabled)  # v2 商店是基础规则
        self.assertFalse(spec.shop_open)
        self.assertIsNone(spec.money)
        self.assertEqual(spec.hand_ids[0], "c7h")

    def test_shop_decision_point_spec(self):
        scenarios = {s.scenario_id: s for s in load_scenarios(DEV_DIR)}
        scenario = scenarios["dev-shop-buy-or-bank"]
        spec = to_reset_spec(scenario)
        self.assertTrue(spec.shop_open)
        self.assertEqual(spec.money, 6)
        self.assertEqual(scenario.decision_type, "shop")
        self.assertEqual(set(spec.allowed_action_kinds),
                         {"choose_joker", "sell_joker", "reroll_shop"})


class TestValidationRejects(unittest.TestCase):
    def assert_rejects(self, data: dict, error_type=InvalidActionError):
        with self.assertRaises(error_type):
            scenario_from_dict(data)

    def test_rules_version_mismatch(self):
        self.assert_rejects(base_dict(rules_version="other"))

    def test_boss_effect_not_implemented(self):
        data = base_dict(boss_blind={"name": "The Wall", "effect": "wall"})
        self.assert_rejects(data, UnsupportedRuleError)

    def test_boss_blind_requires_declaration(self):
        data = base_dict()
        data["initial_state"]["blind_idx"] = 2
        self.assert_rejects(data)

    def test_unknown_extension(self):
        self.assert_rejects(base_dict(extensions=["teleport"]), UnsupportedRuleError)

    def test_free_joker_choice_extension_is_retired(self):
        # v2：免费三选一已退役（付费商店取代），声明它也要被拒。
        self.assert_rejects(base_dict(extensions=["free_joker_choice"]), UnsupportedRuleError)

    def test_shop_decision_requires_shop_open(self):
        data = base_dict(decision_type="shop")
        self.assert_rejects(data)  # 没声明 shop_open=true

    def test_shop_decision_rejects_non_shop_actions(self):
        data = base_dict(decision_type="shop")
        data["initial_state"]["shop_open"] = True
        data["constraints"]["allowed_action_kinds"] = ["play"]
        self.assert_rejects(data)

    def test_shop_open_after_boss_rejected(self):
        data = base_dict(decision_type="shop")
        data["initial_state"].update({"shop_open": True, "blind_idx": 2})
        data["boss_blind"] = {"name": "Boss", "effect": None}
        self.assert_rejects(data)

    def test_negative_money_rejected(self):
        data = base_dict()
        data["initial_state"]["money"] = -1
        self.assert_rejects(data)

    def test_real_capture_requires_capture_id(self):
        self.assert_rejects(base_dict(origin="real_capture"))

    def test_duplicate_hand_cards(self):
        data = base_dict()
        data["initial_state"]["hand_ids"] = ["c7h", "c7h"]
        self.assert_rejects(data)

    def test_unknown_card_id(self):
        data = base_dict()
        data["initial_state"]["hand_ids"] = ["c99z"]
        self.assert_rejects(data)

    def test_unknown_joker(self):
        data = base_dict()
        data["initial_state"]["joker_ids"] = ["made_up_joker"]
        self.assert_rejects(data)

    def test_too_many_jokers(self):
        data = base_dict()
        data["initial_state"]["joker_ids"] = ["joker", "jolly_joker", "zany_joker",
                                              "sly_joker", "wily_joker", "half_joker"]
        self.assert_rejects(data)

    def test_play_decision_requires_play_only(self):
        data = base_dict()
        data["constraints"]["allowed_action_kinds"] = ["play", "discard"]
        self.assert_rejects(data)

    def test_unknown_field_rejected(self):
        data = base_dict()
        data["typo_field"] = 1
        self.assert_rejects(data)

    def test_already_cleared_scenario_rejected(self):
        data = base_dict()
        data["initial_state"]["total_score"] = 300
        self.assert_rejects(data)


class TestJsonlLoading(unittest.TestCase):
    def test_jsonl_roundtrip(self):
        scenario = scenario_from_dict(base_dict())
        with workspace_tmp() as tmp:
            path = Path(tmp) / "scenarios.jsonl"
            path.write_text(json.dumps(scenario.to_dict()) + "\n", encoding="utf-8")
            loaded = load_scenarios(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].scenario_id, scenario.scenario_id)


if __name__ == "__main__":
    unittest.main()
