"""经济（v2）测试：结算发钱、利息上限、商店买入/卖出/reroll/离开、语义边界。

覆盖的声明（``Ruleset.implemented`` 中带 economy 的项）：
- 起始 $4；奖励 $3/$4/$5；每剩余 1 手 +$1；每未用 1 弃牌 +$1；利息每 $5 上限 $5；
- Small/Big 之后开商店（2 个报价、按稀有度固定价）；Boss 通关即 win、不进商店；
- 买入扣钱并占用槽位；卖出返还半价；reroll 涨价；离开商店进入下一盲注且金钱保留。
"""
from __future__ import annotations

import unittest

from bench.actions import legal_actions, shop_actions
from bench.engine import (
    choose_joker,
    new_game,
    open_shop,
    play,
    reroll_shop,
    sell_joker,
)
from bench.environment import Environment, ResetSpec
from bench.errors import BAD_REQUEST, INVALID_STATE, NO_RESOURCE, InvalidActionError
from bench.observation import build_observation
from bench.rules_version import VANILLA_SUBSET_V1 as RULES, interest_for, joker_price
from bench.serialize import restore, snapshot, state_to_dict


def _shop_state(seed: int = 7, money: int = 6, jokers=(), blind_idx: int = 0):
    """构造一个 shop 阶段的状态（种子 7 的报价是 jolly_joker + wily_joker，各 $5）。"""
    state = new_game(seed, joker_ids=jokers)
    state.money = money
    state.blind_idx = blind_idx
    open_shop(state, RULES)
    return state


class TestBlindPayout(unittest.TestCase):
    def test_payout_breakdown_on_small_blind(self):
        state = new_game(7)
        state.target = 1              # 强制本盲注立即达标
        state.hands_left = 3
        state.discards_left = 2
        state.money = 12              # 12 // 5 = 2 利息
        after, _ = play(state, [state.hand[0].card_id])
        payout = after.last_payout
        self.assertEqual(payout["blind_reward"], 3)
        self.assertEqual(payout["hand_bonus"], 2 * 1)     # play 已扣掉 1 手
        self.assertEqual(payout["discard_bonus"], 2 * 1)
        self.assertEqual(payout["interest"], 2)
        self.assertEqual(payout["money_before"], 12)
        self.assertEqual(payout["total"], 3 + 2 + 2 + 2)
        self.assertEqual(after.money, 12 + payout["total"])

    def test_interest_is_capped_at_five(self):
        state = new_game(7)
        state.target = 1
        state.money = 100
        after, _ = play(state, [state.hand[0].card_id])
        self.assertEqual(after.last_payout["interest"], 5)
        self.assertEqual(interest_for(100), 5)

    def test_interest_uses_money_before_payout(self):
        # 若按入账后金额算，$10 会拿到 $2 利息；本实现固定用入账前金额。
        state = new_game(7)
        state.target = 1
        state.money = 10
        after, _ = play(state, [state.hand[0].card_id])
        self.assertEqual(after.last_payout["interest"], 2)

    def test_big_blind_reward_is_four(self):
        state = new_game(7)
        state.blind_idx = 1
        state.blind_kind = "big"
        state.target = 450
        state.total_score = 449
        after, _ = play(state, [state.hand[0].card_id])
        self.assertEqual(after.phase, "shop")
        self.assertEqual(after.last_payout["blind_reward"], 4)

    def test_boss_clear_does_not_open_shop(self):
        state = new_game(7)
        state.blind_idx = 2
        state.blind_kind = "boss"
        state.target = 1
        after, _ = play(state, [state.hand[0].card_id])
        self.assertEqual(after.phase, "done")
        self.assertEqual(after.outcome, "win")
        self.assertEqual(after.shop_options, [])
        self.assertEqual(after.last_payout["blind_reward"], 5)


class TestShopMath(unittest.TestCase):
    def test_offers_are_two_priced_by_rarity(self):
        state = _shop_state(money=6)
        self.assertEqual(len(state.shop_options), 2)
        self.assertEqual([j.jid for j in state.shop_options], ["jolly_joker", "wily_joker"])
        self.assertEqual([joker_price(j) for j in state.shop_options], [5, 5])

    def test_buying_costs_money_and_keeps_shop_open(self):
        state = _shop_state(money=6)
        after = choose_joker(state, 0)
        self.assertEqual(after.money, 1)
        self.assertEqual([j.jid for j in after.jokers], ["jolly_joker"])
        self.assertEqual(len(after.shop_options), 1)     # 已买走，不能重复买
        self.assertEqual(after.phase, "shop")            # 还能继续买/卖/reroll
        self.assertIsNone(after.last_payout)

    def test_cannot_buy_without_money(self):
        state = _shop_state(money=4)
        self.assertEqual([a for a in shop_actions(state) if a.joker_index is not None], [])
        with self.assertRaises(InvalidActionError) as ctx:
            choose_joker(state, 0)
        self.assertEqual(ctx.exception.code, NO_RESOURCE)
        self.assertEqual(ctx.exception.detail["price"], 5)

    def test_cannot_buy_when_slots_full(self):
        state = _shop_state(money=99, jokers=("joker", "jolly_joker",
                                             "zany_joker", "sly_joker", "wily_joker"))
        with self.assertRaises(InvalidActionError) as ctx:
            choose_joker(state, 0)
        self.assertEqual(ctx.exception.code, NO_RESOURCE)
        self.assertIn("slots", ctx.exception.message)

    def test_sell_refunds_half_price_and_frees_slot(self):
        state = _shop_state(money=0, jokers=("the_duo",))   # Rare $9 → 卖 $4
        after = sell_joker(state, 0)
        self.assertEqual(after.money, 4)
        self.assertEqual(after.jokers, [])
        self.assertEqual(len(after.shop_options), 2)

    def test_sell_out_of_range(self):
        state = _shop_state(money=0)
        with self.assertRaises(InvalidActionError) as ctx:
            sell_joker(state, 0)
        self.assertEqual(ctx.exception.code, BAD_REQUEST)

    def test_reroll_costs_and_escalates(self):
        state = _shop_state(money=20)
        first = reroll_shop(state)
        self.assertEqual((first.money, first.reroll_cost), (15, 6))
        second = reroll_shop(first)
        self.assertEqual((second.money, second.reroll_cost), (9, 7))
        third = reroll_shop(second)
        self.assertEqual((third.money, third.reroll_cost), (2, 8))
        with self.assertRaises(InvalidActionError) as ctx:
            reroll_shop(third)           # 只剩 $2，买不起 $8 的 reroll
        self.assertEqual(ctx.exception.code, NO_RESOURCE)

    def test_reroll_blocked_when_broke(self):
        state = _shop_state(money=4)      # 4 < 5
        with self.assertRaises(InvalidActionError) as ctx:
            reroll_shop(state)
        self.assertEqual(ctx.exception.code, NO_RESOURCE)
        self.assertNotIn("reroll_shop", [a.kind for a in legal_actions(state)])

    def test_reroll_changes_offers_and_keeps_them_distinct(self):
        state = _shop_state(money=20)
        before = [j.jid for j in state.shop_options]
        after = reroll_shop(state)
        self.assertEqual(len(after.shop_options), 2)
        self.assertEqual(len({j.jid for j in after.shop_options}), 2)
        self.assertNotEqual(before, [j.jid for j in after.shop_options])

    def test_offers_exclude_owned_jokers(self):
        state = _shop_state(money=20, jokers=("jolly_joker",))
        owned = {j.jid for j in state.jokers}
        self.assertFalse(owned & {j.jid for j in state.shop_options})
        after = reroll_shop(state)
        self.assertFalse(owned & {j.jid for j in after.shop_options})

    def test_offers_are_deterministic_per_seed(self):
        a = _shop_state(seed=7, money=6)
        b = _shop_state(seed=7, money=6)
        self.assertEqual([j.jid for j in a.shop_options], [j.jid for j in b.shop_options])
        self.assertEqual(a.rng_state, b.rng_state)


class TestShopFlow(unittest.TestCase):
    def test_leave_advances_blind_preserves_money_and_resets_reroll(self):
        state = _shop_state(money=20)
        state = reroll_shop(state)                       # reroll_cost 涨到 6
        left = choose_joker(state, None)
        self.assertEqual(left.blind_idx, 1)
        self.assertEqual(left.phase, "play")
        self.assertEqual(left.money, 15)
        self.assertEqual(left.reroll_cost, 5)            # 新商店重新从基准价开始
        self.assertEqual(left.shop_options, [])
        self.assertEqual(left.deck_total, 52)

    def test_shop_actions_are_legal_actions(self):
        state = _shop_state(money=6)
        kinds = [a.kind for a in legal_actions(state)]
        self.assertEqual(kinds.count("choose_joker"), 3)  # 2 个买 + 1 个离开
        self.assertEqual(kinds[-1], "choose_joker")       # 离开恒为最后一项
        self.assertFalse(any(a.kind == "sell_joker" for a in legal_actions(state)))

    def test_environment_reset_can_open_shop(self):
        env = Environment()
        obs = env.reset(ResetSpec(seed=7, money=6, shop_open=True,
                                  allowed_action_kinds=("choose_joker",)))
        self.assertEqual(obs["episode"]["phase"], "shop")
        self.assertEqual(obs["economy"]["money"], 6)
        self.assertEqual([o["price"] for o in obs["shop"]["offers"]], [5, 5])
        self.assertEqual(obs["shop"]["reroll_cost"], 5)
        result = env.step({"kind": "choose_joker", "joker_index": 0})
        self.assertEqual(result.info["money"], 1)
        self.assertEqual(result.info["money_delta"], -5)
        self.assertEqual(result.info["phase"], "shop")

    def test_buy_outside_shop_phase_is_rejected(self):
        state = new_game(7)
        with self.assertRaises(InvalidActionError) as ctx:
            choose_joker(state, 0)
        self.assertEqual(ctx.exception.code, INVALID_STATE)


class TestEconomySerialization(unittest.TestCase):
    def test_snapshot_roundtrip_in_shop(self):
        state = _shop_state(money=6, jokers=("joker",))
        state = reroll_shop(state) if state.money >= state.reroll_cost else state
        snap = snapshot(state)
        restored = restore(snap)
        self.assertEqual(restored, state)
        self.assertEqual(restored.money, state.money)
        self.assertEqual(restored.reroll_cost, state.reroll_cost)
        self.assertEqual(state_to_dict(restored)["money"], state.money)

    def test_observation_exposes_economy_and_shop(self):
        state = _shop_state(money=6, jokers=("joker",))
        obs = build_observation(state, RULES)
        self.assertEqual(obs["schema_version"], 2)
        self.assertEqual(obs["economy"]["money"], 6)
        self.assertEqual(obs["economy"]["next_interest"], 1)
        self.assertTrue(obs["shop"]["open"])
        self.assertEqual(len(obs["shop"]["offers"]), 2)
        self.assertEqual(obs["shop"]["sell_values"][0]["sell_value"], 2)
        self.assertEqual(obs["shop"]["free_slots"], 4)

    def test_render_includes_money_and_shop(self):
        env = Environment()
        env.reset(ResetSpec(seed=7, money=6, shop_open=True))
        text = env.render()
        self.assertIn("money=$6", text)
        self.assertIn("shop:", text)
        self.assertIn("reroll=$5", text)


if __name__ == "__main__":
    unittest.main()
