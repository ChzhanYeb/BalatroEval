"""Environment：稳定接口的游戏环境封装（reset/observe/legal_actions/step/snapshot）。

职责边界：
- 规则计算全部委托给 ``bench.engine`` / ``bench.scoring``（单一规则实现）；本模块只做
  **会话状态管理**：当前 state、步数、场景约束（允许的动作种类）、截断（max_steps）与
  snapshot/restore。
- 不写文件、不调用模型、不持有全局可变状态；一个 Environment 实例只服务一个 episode。
- 错误：非法动作抛 ``bench.errors.InvalidActionError``（带稳定 code）；工具层/runner
  负责把异常转成结构化结果与 trace。

StepResult 语义：
- ``terminated``：按规则正常结束（win/loss）；
- ``truncated``：因外部限制（max_steps）结束，**不等于**游戏结束；两者不混用。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actions import Action, legal_actions as rule_legal_actions
from .engine import apply_action, new_game, open_shop
from .errors import BAD_REQUEST, EPISODE_DONE, INVALID_STATE, NOT_ALLOWED, InvalidActionError
from .model import GameState
from .observation import build_observation, render_observation
from .rules_version import VANILLA_SUBSET_V1, Ruleset
from .serialize import snapshot as state_snapshot, restore as state_restore, state_hash
from .scoring import ScoreResult

ENV_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class StepResult:
    """``Environment.step`` 的返回结构。

    Attributes:
        observation: 新状态的 observation dict。
        reward: 本次动作带来的分数增量（play 得分；discard/商店动作为 0）。
        terminated: 规则意义上的 episode 结束。
        truncated: 外部限制（max_steps）导致的结束。
        info: 结构化附加信息：``state_hash`` / ``score`` / ``action_code`` /
            ``phase`` / ``termination_reason``。
    """

    observation: dict
    reward: int
    terminated: bool
    truncated: bool
    info: dict

    def to_dict(self) -> dict:
        """导出 JSON 友好 dict（保留 reward/terminated/truncated 三态语义）。"""
        return {
            "observation": self.observation,
            "reward": self.reward,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "info": self.info,
        }


@dataclass(frozen=True, slots=True)
class ResetSpec:
    """环境重置参数（由场景加载器构造，Environment 不依赖 scenarios 包）。

    Attributes:
        seed: 随机种子。
        hand_ids: 指定初始手牌（None = 按 seed 发牌）。
        joker_ids: 初始 Joker。
        deck_order: 指定抽牌堆顺序（回放/测试用）。
        ruleset: 规则集；None 用默认。
        allowed_action_kinds: 仅允许的动作种类（None = 不限制）。
        max_steps: 步数上限（None = 不限制）。
        blind_idx / total_score / hands_left / discards_left / target:
            覆盖初始状态字段（用于固定决策点场景）；None 表示用默认值。
        money: 覆盖初始金钱；None 表示用规则默认（Red Deck $4）。
        shop_open: True 表示 reset 后直接进入商店（用于商店决策点场景）；
            只对 blind_idx 0/1 有意义（Boss 通关即 win，没有商店）。
        scenario_id: 场景 ID（写入 episode 元数据）。
    """

    seed: int = 0
    hand_ids: tuple[str, ...] | None = None
    joker_ids: tuple[str, ...] = ()
    deck_order: tuple[str, ...] | None = None
    ruleset: Ruleset = VANILLA_SUBSET_V1
    allowed_action_kinds: tuple[str, ...] | None = None
    max_steps: int | None = None
    blind_idx: int | None = None
    total_score: int | None = None
    hands_left: int | None = None
    discards_left: int | None = None
    target: int | None = None
    money: int | None = None
    shop_open: bool = False
    scenario_id: str | None = None


class Environment:
    """单 episode 的确定性环境。

    Args:
        ruleset: 规则集；默认 ``VANILLA_SUBSET_V1``。
        max_steps: 可选步数上限（可在 reset 时覆盖）。
    """

    def __init__(self, ruleset: Ruleset = VANILLA_SUBSET_V1, max_steps: int | None = None) -> None:
        self.ruleset = ruleset
        self.max_steps = max_steps
        self.state: GameState | None = None
        self.reset_spec: ResetSpec | None = None
        self.step_count = 0
        self.total_reward = 0
        self._allowed: tuple[str, ...] | None = None
        self._started = False

    # ------------------------------------------------------------------ reset
    def reset(
        self,
        spec: ResetSpec | None = None,
        *,
        seed: int | None = None,
    ) -> dict:
        """初始化 episode 并返回首个 observation。

        Args:
            spec: 场景重置参数；None 时用 ``seed`` 构造默认全随机局面。
            seed: 便捷参数；仅当 spec 为 None 时使用。

        Returns:
            observation dict。

        Raises:
            InvalidActionError: spec 与规则冲突（例如指定了不存在的盲注、手牌超额）。
        """
        if spec is None:
            spec = ResetSpec(seed=int(seed or 0), ruleset=self.ruleset)
        self.ruleset = spec.ruleset
        self.max_steps = spec.max_steps
        self._allowed = spec.allowed_action_kinds
        state = new_game(
            spec.seed,
            ruleset=spec.ruleset,
            hand_ids=spec.hand_ids,
            joker_ids=spec.joker_ids,
            deck_order=spec.deck_order,
        )
        # 覆盖固定决策点字段（不改变规则常量，只改变起点）。
        if spec.blind_idx is not None:
            if spec.blind_idx not in (0, 1, 2):
                raise InvalidActionError(BAD_REQUEST, "blind_idx must be 0..2",
                                         {"blind_idx": spec.blind_idx})
            state.blind_idx = spec.blind_idx
            spec_blind = spec.ruleset.blind(spec.blind_idx)
            state.blind_kind = spec_blind.kind
            state.boss_effect = spec_blind.effect
            state.target = spec_blind.target
        if spec.target is not None:
            if spec.target <= 0:
                raise InvalidActionError(BAD_REQUEST, "target must be positive")
            state.target = spec.target
        if spec.total_score is not None:
            if spec.total_score < 0:
                raise InvalidActionError(BAD_REQUEST, "total_score cannot be negative")
            state.total_score = spec.total_score
        if spec.hands_left is not None:
            if not 0 <= spec.hands_left <= spec.ruleset.hands_per_blind:
                raise InvalidActionError(BAD_REQUEST, "hands_left out of range",
                                         {"hands_left": spec.hands_left})
            state.hands_left = spec.hands_left
        if spec.discards_left is not None:
            if not 0 <= spec.discards_left <= spec.ruleset.discards_per_blind:
                raise InvalidActionError(BAD_REQUEST, "discards_left out of range",
                                         {"discards_left": spec.discards_left})
            state.discards_left = spec.discards_left
        if spec.money is not None:
            if spec.money < 0:
                raise InvalidActionError(BAD_REQUEST, "money cannot be negative",
                                         {"money": spec.money})
            state.money = spec.money
        if spec.shop_open:
            if not spec.ruleset.shop_enabled:
                raise InvalidActionError(NOT_ALLOWED, "shop is disabled in this ruleset")
            if state.blind_idx == 2:
                raise InvalidActionError(
                    BAD_REQUEST, "shop does not open after the boss blind",
                    {"blind_idx": state.blind_idx},
                )
            open_shop(state, spec.ruleset)
        self.state = state
        self.reset_spec = spec
        self.step_count = 0
        self.total_reward = 0
        self._started = True
        return self.observe()

    # ------------------------------------------------------------------ views
    def _require_state(self) -> GameState:
        if self.state is None:
            raise InvalidActionError(INVALID_STATE, "environment is not reset")
        return self.state

    def observe(self) -> dict:
        """返回当前 Observation dict（不推进状态）。"""
        state = self._require_state()
        return build_observation(state, self.ruleset, self._allowed)

    def render(self, max_chars: int = 1000) -> str:
        """返回紧凑文本 observation（供 LLM 工具/日志）。"""
        return render_observation(self.observe(), max_chars=max_chars)

    def legal_actions(self) -> list[Action]:
        """返回当前全部合法动作（按场景约束过滤；不修改状态）。"""
        state = self._require_state()
        actions = rule_legal_actions(state, self.ruleset.max_play_cards,
                                     self.ruleset.max_discard_cards)
        if self._allowed is None:
            return actions
        return [a for a in actions if a.kind in self._allowed]

    def is_terminated(self) -> bool:
        """规则上是否已结束（state.phase == 'done'）。"""
        return self.state is not None and self.state.phase == "done"

    def is_truncated(self) -> bool:
        """是否因 max_steps 被截断（规则未结束但不能再 step）。"""
        return (not self.is_terminated() and self.max_steps is not None
                and self.step_count >= self.max_steps)

    # ------------------------------------------------------------------- step
    def step(self, action: Action | dict) -> StepResult:
        """执行一个动作并返回 ``StepResult``。

        Args:
            action: ``Action`` 或工具层 dict（``Action.from_dict`` 可解析）。

        Returns:
            StepResult。

        Raises:
            InvalidActionError: episode 已结束（EPISODE_DONE）、被 max_steps 截断
                （INVALID_STATE）、场景不允许该动作种类（NOT_ALLOWED）、
                动作本身非法（见 engine）。
        """
        state = self._require_state()
        if self.is_terminated():
            raise InvalidActionError(EPISODE_DONE, "episode is already finished")
        if self.is_truncated():
            raise InvalidActionError(INVALID_STATE, "episode is truncated by max_steps")
        act = action if isinstance(action, Action) else Action.from_dict(action)
        if self._allowed is not None and act.kind not in self._allowed:
            raise InvalidActionError(
                NOT_ALLOWED,
                f"action kind {act.kind!r} is not allowed in this scenario",
                {"allowed": list(self._allowed)},
            )
        # 为 card 动作补充“动作发生时的手牌下标快照”（trace 证据；不影响规则）。
        if act.kind in ("play", "discard") and not act.hand_indices_snapshot:
            index = {card.card_id: i for i, card in enumerate(state.hand)}
            try:
                snapshot = tuple(index[cid] for cid in act.card_ids)
            except KeyError:
                snapshot = ()
            else:
                act = Action(act.kind, card_ids=act.card_ids, hand_indices_snapshot=snapshot)
        before = state
        after, result = apply_action(state, act)
        # reward 在环境层定义为“本步分数增量”；discard/商店动作为 0（金钱变化看 info）。
        reward = result.final_score if isinstance(result, ScoreResult) else 0
        self.state = after
        self.step_count += 1
        self.total_reward += reward
        terminated = after.phase == "done"
        truncated = (not terminated and self.max_steps is not None
                     and self.step_count >= self.max_steps)
        if after.outcome == "win":
            termination_reason = "win"
        elif after.outcome == "loss":
            termination_reason = "loss"
        elif truncated:
            termination_reason = "truncated"
        else:
            termination_reason = None
        info: dict[str, Any] = {
            "action_code": act.code,
            "state_hash_before": state_hash(before),
            "state_hash_after": state_hash(after),
            "steps": self.step_count,
            "phase": after.phase,
            "outcome": after.outcome,
            "blind_idx": after.blind_idx,
            "total_score": after.total_score,
            "money": after.money,
            "money_delta": after.money - before.money,
            "last_payout": after.last_payout,
            "termination_reason": termination_reason,
        }
        if isinstance(result, ScoreResult):
            info["score"] = result.to_dict()
        return StepResult(
            observation=self.observe(),
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info=info,
        )

    # -------------------------------------------------------- snapshot/restore
    def snapshot(self) -> dict:
        """导出环境 + 状态快照（含步数与场景约束），用于回放/断点续跑。"""
        state = self._require_state()
        return {
            "env_schema_version": ENV_SCHEMA_VERSION,
            "step_count": self.step_count,
            "total_reward": self.total_reward,
            "allowed_action_kinds": list(self._allowed) if self._allowed else None,
            "max_steps": self.max_steps,
            "state": state_snapshot(state),
        }

    def restore(self, payload: dict) -> dict:
        """从 ``snapshot`` 产物恢复环境，返回恢复后的 observation。

        Raises:
            InvalidActionError: payload 结构/哈希非法。
        """
        if not isinstance(payload, dict) or payload.get("env_schema_version") != ENV_SCHEMA_VERSION:
            raise InvalidActionError(BAD_REQUEST, "unsupported environment snapshot")
        self.state = state_restore(payload["state"])
        self.step_count = int(payload.get("step_count", 0))
        self.total_reward = int(payload.get("total_reward", 0))
        allowed = payload.get("allowed_action_kinds")
        self._allowed = tuple(allowed) if allowed else None
        self.max_steps = payload.get("max_steps")
        self._started = True
        return self.observe()
