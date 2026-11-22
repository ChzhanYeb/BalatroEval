"""性质测试：不变量（守恒/确定性/无副作用/隔离/上界），不依赖具体样例数字。"""
from __future__ import annotations

import random
import unittest

from bench.actions import Action, legal_actions
from bench.engine import apply_action, new_game, discard, play
from bench.environment import Environment, ResetSpec
from bench.serialize import state_hash, state_to_dict
from bench.model import Card
from bench.scoring import score_hand


class TestInvariants(unittest.TestCase):
    def test_card_conservation_under_random_playouts(self):
        for seed in range(20):
            state = new_game(seed)
            rng = random.Random(seed)
            for _ in range(30):
                if state.phase == "done":
                    break
                actions = legal_actions(state)
                if not actions:
                    break
                action = rng.choice(actions)
                if action.kind == "play":
                    state, _ = play(state, action.card_ids)
                elif action.kind == "discard":
                    state = discard(state, action.card_ids)
                elif action.kind in ("choose_joker", "sell_joker", "reroll_shop"):
                    # v2 商店动作（买/卖/reroll/离开）：只验证不变量，不评估策略
                    state = apply_action(state, action)[0]
                else:
                    self.fail(f"unexpected action kind: {action.kind}")
                self.assertEqual(state.deck_total, 52)
                self.assertGreaterEqual(state.money, 0)

    def test_score_is_floor_of_chips_times_mult(self):
        cases = [
            [Card(0, 1), Card(1, 13)],
            [Card(0, 7), Card(1, 7)],
            [Card(0, 8), Card(1, 8), Card(2, 8), Card(3, 8)],
        ]
        for cards in cases:
            result = score_hand(cards)
            self.assertEqual(result.final_score, int(result.chips * result.mult))
            self.assertLessEqual(result.final_score, result.chips * result.mult)
            self.assertGreaterEqual(result.final_score, 0)

    def test_trace_final_entry_matches_result(self):
        result = score_hand([Card(0, 7), Card(1, 7)])
        final = [entry for entry in result.trace if entry["phase"] == "final_score"][0]
        self.assertEqual(final["final_score"], result.final_score)
        self.assertEqual(final["chips"], result.chips)

    def test_engine_functions_do_not_mutate_input(self):
        state = new_game(3)
        before = state_to_dict(state)
        play(state, [state.hand[0].card_id])
        self.assertEqual(state_to_dict(state), before)
        before = state_to_dict(state)
        discard(state, [state.hand[0].card_id])
        self.assertEqual(state_to_dict(state), before)

    def test_environment_state_isolation(self):
        env_a, env_b = Environment(), Environment()
        env_a.reset(ResetSpec(seed=1))
        env_b.reset(ResetSpec(seed=2))
        hash_a, hash_b = state_hash(env_a.state), state_hash(env_b.state)
        action = next(a for a in env_a.legal_actions() if a.kind == "play")
        env_a.step(action)
        self.assertEqual(state_hash(env_b.state), hash_b)
        self.assertNotEqual(state_hash(env_a.state), hash_a)

    def test_illegal_action_leaves_state_unchanged(self):
        env = Environment()
        env.reset(ResetSpec(seed=5))
        before = state_hash(env.state)
        bad = Action("play", card_ids=("c1s", "c2s"))  # 不在手牌
        with self.assertRaises(Exception):
            env.step(bad)
        self.assertEqual(state_hash(env.state), before)

    def test_action_codes_unique_for_full_hand(self):
        state = new_game(9)
        codes = [action.code for action in legal_actions(state)]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(codes), 436)  # 218 play + 218 discard

    def test_replay_same_actions_same_states(self):
        actions = []
        state = new_game(21)
        while state.phase == "play" and len(actions) < 4:
            action = legal_actions(state)[0]
            actions.append((action.kind, action.card_ids))
            state = play(state, action.card_ids)[0] if action.kind == "play" else discard(state, action.card_ids)
        replay = new_game(21)
        for kind, card_ids in actions:
            replay = play(replay, card_ids)[0] if kind == "play" else discard(replay, card_ids)
        self.assertEqual(state_hash(state), state_hash(replay))

    def test_hand_size_never_exceeds_limit(self):
        state = new_game(33)
        self.assertLessEqual(len(state.hand), state.hand_size)
        for _ in range(5):
            if state.phase != "play" or not state.hand or state.discards_left <= 0:
                break
            state = discard(state, [state.hand[0].card_id])
            self.assertLessEqual(len(state.hand), state.hand_size)


if __name__ == "__main__":
    unittest.main()
