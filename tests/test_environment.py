"""环境层与引擎转移测试：资源/盲注/胜负/快照/动作校验/工具层。"""
from __future__ import annotations

import json
import unittest

from bench.actions import Action, encode_card_action, legal_actions, legal_plays
from bench.cards import STANDARD_DECK_ORDER, card_from_stable_id
from bench.engine import apply_action, discard, new_game, play
from bench.environment import Environment, ResetSpec
from bench.errors import (
    BAD_REQUEST,
    DUPLICATE_CARD,
    EPISODE_DONE,
    INVALID_STATE,
    NOT_ALLOWED,
    UNKNOWN_CARD,
    InvalidActionError,
)
from bench.model import Card
from bench.rules_version import VANILLA_SUBSET_V1
from bench.serialize import restore, snapshot, state_hash, state_to_dict
from bench.tools import GameSession, dispatch_tool


class TestEngineConstants(unittest.TestCase):
    def test_ruleset_targets_and_resources(self):
        self.assertEqual([b.target for b in VANILLA_SUBSET_V1.blinds], [300, 450, 600])
        self.assertEqual([b.kind for b in VANILLA_SUBSET_V1.blinds], ["small", "big", "boss"])
        self.assertEqual(VANILLA_SUBSET_V1.hands_per_blind, 4)
        self.assertEqual(VANILLA_SUBSET_V1.discards_per_blind, 4)  # Red Deck: 3 + 1
        self.assertEqual(VANILLA_SUBSET_V1.hand_size, 8)
        self.assertEqual(VANILLA_SUBSET_V1.joker_slots, 5)

    def test_new_game_initial_state(self):
        state = new_game(123)
        self.assertEqual(state.deck_total, 52)
        self.assertEqual(len(state.hand), 8)
        self.assertEqual(len(state.deck), 44)
        self.assertEqual(state.target, 300)
        self.assertEqual(state.blind_kind, "small")
        self.assertEqual(state.hands_left, 4)
        self.assertEqual(state.discards_left, 4)
        self.assertEqual(state.phase, "play")
        self.assertEqual(state.joker_slots, 5)
        self.assertEqual(len({c.card_id for c in state.hand + state.deck}), 52)

    def test_same_seed_is_deterministic(self):
        self.assertEqual(new_game(42), new_game(42))
        self.assertNotEqual(new_game(42), new_game(43))

    def test_starting_hand_override(self):
        ids = ["c7h", "c7d", "c9s", "c9d", "c13h", "c2c", "c5s", "c11d"]
        state = new_game(42, hand_ids=ids)
        self.assertEqual([c.card_id for c in state.hand], ids)
        self.assertEqual(state.deck_total, 52)

    def test_starting_jokers_validated(self):
        state = new_game(42, joker_ids=["joker", "the_duo"])
        self.assertEqual([j.jid for j in state.jokers], ["joker", "the_duo"])
        with self.assertRaises(InvalidActionError):
            new_game(42, joker_ids=["not_a_joker"])


class TestBlindProgression(unittest.TestCase):
    def test_clear_blind_advances_and_resets(self):
        state = new_game(7)
        state.target = 1  # 仅用于测试：强制本盲注立即达标
        before_hand = [c.card_id for c in state.hand]
        after, result = play(state, [state.hand[0].card_id])
        self.assertGreaterEqual(result.final_score, 1)
        self.assertEqual(after.blind_idx, 1)
        self.assertEqual(after.blind_kind, "big")
        self.assertEqual(after.target, 450)
        self.assertEqual(after.total_score, 0)
        self.assertEqual((after.hands_left, after.discards_left), (4, 4))
        self.assertEqual(len(after.hand), 8)
        self.assertEqual(after.deck_total, 52)
        self.assertNotEqual([c.card_id for c in after.hand], before_hand)  # 新盲注重发

    def test_win_after_boss(self):
        state = new_game(7)
        state.blind_idx = 2
        state.blind_kind = "boss"
        state.target = 600
        state.target = 1
        after, _ = play(state, [state.hand[0].card_id])
        self.assertEqual(after.phase, "done")
        self.assertEqual(after.outcome, "win")

    def test_loss_when_last_hand_misses(self):
        state = new_game(7)
        state.target = 10**9
        state.hands_left = 1
        after, _ = play(state, [state.hand[0].card_id])
        self.assertEqual(after.phase, "done")
        self.assertEqual(after.outcome, "loss")

    def test_last_hand_can_still_win(self):
        state = new_game(7)
        state.target = 1
        state.hands_left = 1
        after, _ = play(state, [state.hand[0].card_id])
        # 达标优先于“次数耗尽判负”
        self.assertNotEqual(after.outcome, "loss")


class TestDiscardAndValidation(unittest.TestCase):
    def test_discard_consumes_and_refills(self):
        state = new_game(11)
        ids = [state.hand[0].card_id, state.hand[1].card_id]
        after = discard(state, ids)
        self.assertEqual(after.discards_left, 3)
        self.assertEqual(len(after.hand), 8)
        self.assertEqual(after.deck_total, 52)
        self.assertEqual(after.total_score, 0)
        self.assertEqual(after.steps, 1)

    def test_no_discards_remaining(self):
        state = new_game(11)
        state.discards_left = 0
        with self.assertRaises(InvalidActionError) as ctx:
            discard(state, [state.hand[0].card_id])
        self.assertEqual(ctx.exception.code, "NO_RESOURCE")

    def test_play_unknown_duplicate_and_count(self):
        state = new_game(11)
        with self.assertRaises(InvalidActionError) as ctx:
            play(state, ["c1s", "c2s"])
        self.assertEqual(ctx.exception.code, UNKNOWN_CARD)
        cid = state.hand[0].card_id
        with self.assertRaises(InvalidActionError) as ctx:
            play(state, [cid, cid])
        self.assertEqual(ctx.exception.code, DUPLICATE_CARD)
        with self.assertRaises(InvalidActionError) as ctx:
            play(state, [])
        self.assertEqual(ctx.exception.code, BAD_REQUEST)

    def test_play_does_not_mutate_input_state(self):
        state = new_game(11)
        before = state_to_dict(state)
        play(state, [state.hand[0].card_id])
        self.assertEqual(state_to_dict(state), before)

    def test_done_state_rejects_actions(self):
        state = new_game(11)
        state.phase = "done"
        state.outcome = "loss"
        with self.assertRaises(InvalidActionError) as ctx:
            play(state, [state.hand[0].card_id])
        self.assertEqual(ctx.exception.code, EPISODE_DONE)

    def test_shop_disabled_by_default(self):
        state = new_game(11)
        state.phase = "shop"
        with self.assertRaises(InvalidActionError) as ctx:
            apply_action(state, Action("choose_joker", joker_index=0))
        self.assertEqual(ctx.exception.code, NOT_ALLOWED)


class TestSnapshot(unittest.TestCase):
    def test_snapshot_roundtrip(self):
        state = new_game(99)
        after, _ = play(state, [state.hand[0].card_id])
        snap = snapshot(after)
        restored = restore(snap)
        self.assertEqual(restored, after)
        self.assertEqual(state_hash(restored), state_hash(after))

    def test_snapshot_hash_detects_tamper(self):
        state = new_game(99)
        snap = snapshot(state)
        snap["state"]["total_score"] = 12345
        with self.assertRaises(InvalidActionError):
            restore(snap)

    def test_snapshot_rejects_duplicate_cards(self):
        snap = snapshot(new_game(99))
        snap["state"]["deck"][0] = snap["state"]["hand"][0]
        with self.assertRaises(InvalidActionError):
            restore(snap)


class TestActions(unittest.TestCase):
    def test_218_play_actions_and_counts(self):
        state = new_game(5)
        self.assertEqual(len(legal_plays(state.hand)), 218)
        actions = legal_actions(state)
        self.assertEqual(sum(1 for a in actions if a.kind == "play"), 218)
        self.assertEqual(sum(1 for a in actions if a.kind == "discard"), 218)

    def test_action_code_is_canonical(self):
        hand = [Card(1, 7), Card(2, 7)]
        a = encode_card_action("play", hand, (0, 1))
        b = encode_card_action("play", hand, (1, 0))
        self.assertEqual(a.code, b.code)  # ID 排序后相同

    def test_action_from_dict_validation(self):
        action = Action.from_dict({"kind": "play", "card_ids": ["c7h", "c7d"]})
        self.assertEqual(action.card_ids, ("c7h", "c7d"))
        with self.assertRaises(InvalidActionError):
            Action.from_dict({"kind": "play", "card_ids": []})
        with self.assertRaises(InvalidActionError):
            Action.from_dict({"kind": "unknown"})


class TestEnvironment(unittest.TestCase):
    def test_reset_and_observe(self):
        env = Environment()
        obs = env.reset(ResetSpec(seed=42))
        self.assertEqual(obs["schema_version"], 1)
        self.assertEqual(obs["episode"]["phase"], "play")
        self.assertEqual(len(obs["hand"]), 8)
        self.assertEqual(obs["blind"]["target"], 300)
        self.assertEqual(obs["legal_action_counts"]["play"], 218)
        self.assertEqual(obs["rules_version"], VANILLA_SUBSET_V1.rules_version)

    def test_step_play_and_termination(self):
        env = Environment()
        env.reset(ResetSpec(seed=42))
        play_action = next(a for a in env.legal_actions() if a.kind == "play")
        result = env.step(play_action)
        self.assertTrue(result.reward > 0)
        self.assertFalse(result.terminated)
        self.assertEqual(result.info["steps"], 1)

    def test_allowed_action_kinds_enforced_without_state_change(self):
        env = Environment()
        env.reset(ResetSpec(seed=42, allowed_action_kinds=("play",)))
        before = state_hash(env.state)
        # legal_actions 已过滤掉 discard；这里直接构造 discard 动作，验证 step 仍拒绝
        # 绕过过滤的调用，且状态不发生任何变化。
        discard_action = Action("discard", card_ids=(env.state.hand[0].card_id,))
        with self.assertRaises(InvalidActionError) as ctx:
            env.step(discard_action)
        self.assertEqual(ctx.exception.code, NOT_ALLOWED)
        self.assertEqual(state_hash(env.state), before)

    def test_max_steps_truncation(self):
        env = Environment()
        env.reset(ResetSpec(seed=42, max_steps=1))
        action = next(a for a in env.legal_actions() if a.kind == "play")
        result = env.step(action)
        self.assertTrue(result.truncated)
        self.assertFalse(result.terminated)
        with self.assertRaises(InvalidActionError):
            env.step(next(a for a in env.legal_actions() if a.kind == "play"))

    def test_snapshot_restore_environment(self):
        env = Environment()
        env.reset(ResetSpec(seed=42))
        action = next(a for a in env.legal_actions() if a.kind == "play")
        env.step(action)
        snap = env.snapshot()
        env2 = Environment()
        env2.restore(snap)
        self.assertEqual(env2.state, env.state)
        self.assertEqual(env2.step_count, env.step_count)

    def test_render_is_compact(self):
        env = Environment()
        env.reset(ResetSpec(seed=42))
        text = env.render()
        self.assertLess(len(text), 1000)
        self.assertIn("hand", text)


class TestTools(unittest.TestCase):
    def test_tool_calls_and_error_envelope(self):
        session = GameSession(seed=42)
        state = dispatch_tool(session, "get_state")
        self.assertTrue(state["ok"])
        card_ids = [item["id"] for item in state["observation"]["hand"][:1]]
        played = dispatch_tool(session, "play_cards", {"card_ids": card_ids})
        self.assertTrue(played["ok"])
        self.assertGreater(played["reward"], 0)
        bad = dispatch_tool(session, "play_cards", {"card_ids": ["c1s", "c2s"]})
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["error"]["code"], UNKNOWN_CARD)
        unknown_tool = dispatch_tool(session, "does_not_exist")
        self.assertEqual(unknown_tool["error"]["code"], BAD_REQUEST)

    def test_reset_episode_with_fixed_hand(self):
        session = GameSession(seed=42)
        hand = ["c7h", "c7d", "c9s", "c9d", "c13h", "c2c", "c5s", "c11d"]
        result = dispatch_tool(session, "reset_episode", {"hand_ids": hand, "max_steps": 5})
        self.assertTrue(result["ok"])
        self.assertEqual([c["id"] for c in result["observation"]["hand"]], hand)

    def test_bridge_module_imports_without_mcp_sdk(self):
        import bridge.server as server  # 延迟导入 mcp，不应在 import 期失败
        self.assertIn("get_state", server.TOOL_FUNCTIONS)
        self.assertTrue(callable(server.get_state))


if __name__ == "__main__":
    unittest.main()
