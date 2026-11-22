"""Agent 工具层：get_state / play_cards / discard_cards / choose_joker / sell_joker /
reroll_shop / reset_episode。

职责：把 ``Environment`` 包装成**面向 Agent 的薄壳**：
- 校验输入形状（不重复实现规则；规则判定仍在 engine/hand_eval）；
- 把 ``BenchError`` 转成统一错误码 + 结构化 JSON，**不抛 traceback 给 Agent**；
- 返回 observation + 紧凑文本 + 奖励/终止标志，供 MCP 或本地 runner 复用。

工具契约（与 plan D6 对齐）：6 个游戏工具 + 1 个控制工具（reset_episode）。
商店阶段（Small/Big 之后）用 ``choose_joker(index)`` 买入、``choose_joker(None)`` 离开、
``sell_joker(index)`` 卖出、``reroll_shop()`` 换报价。
所有返回都是 JSON 可序列化 dict；``ok=false`` 时 ``error.code`` 取值见
``bench.errors.ERROR_CODES``。

确定性/副作用：本模块不写文件、不产生随机性（seed 由调用方给）；同一 session 上的
工具调用按顺序推进同一局状态。
"""
from __future__ import annotations

from dataclasses import dataclass

from .environment import Environment, ResetSpec
from .errors import (
    BAD_REQUEST,
    INTERNAL,
    BenchError,
    InvalidActionError,
)
from .observation import render_observation
from .rules_version import Ruleset, VANILLA_SUBSET_V1

TOOL_SCHEMA_VERSION = 1


@dataclass
class GameSession:
    """一个进程内共享的游戏会话（MCP server 或本地评测各持有一个）。

    Args:
        ruleset: 规则集。
        seed: 初始种子；reset 前使用。
    """

    ruleset: Ruleset = VANILLA_SUBSET_V1
    seed: int = 0
    env: Environment | None = None

    def __post_init__(self) -> None:
        if self.env is None:
            self.env = Environment(self.ruleset)
            self.env.reset(ResetSpec(seed=self.seed, ruleset=self.ruleset))


def _ok(payload: dict) -> dict:
    return {"ok": True, "schema_version": TOOL_SCHEMA_VERSION, **payload}


def _error(exc: BenchError) -> dict:
    return {"ok": False, "schema_version": TOOL_SCHEMA_VERSION, "error": exc.to_dict()}


def _run(session: GameSession, fn) -> dict:
    """执行一次工具调用并统一异常映射。

    - ``BenchError``：原样返回结构化错误；
    - 其它异常：转 INTERNAL，避免把实现细节/堆栈泄露给 Agent。
    """
    try:
        return fn()
    except BenchError as exc:
        return _error(exc)
    except Exception as exc:  # noqa: BLE001 - 工具边界必须兜底
        return _error(InvalidActionError(INTERNAL, f"unexpected tool failure: {type(exc).__name__}"))


def _state_payload(env: Environment, reward: int = 0, terminated: bool = False,
                   truncated: bool = False, info: dict | None = None) -> dict:
    observation = env.observe()
    return _ok({
        "observation": observation,
        "text": render_observation(observation),
        "reward": reward,
        "terminated": terminated,
        "truncated": truncated,
        "info": info or {},
    })


def get_state(session: GameSession) -> dict:
    """返回当前状态（observation + 紧凑文本）。

    Returns:
        ``{"ok": True, "observation": {...}, "text": str, ...}`` 或 ``{"ok": False, "error": {...}}``。
    """
    def _impl() -> dict:
        assert session.env is not None
        return _state_payload(session.env)

    return _run(session, _impl)


def play_cards(session: GameSession, card_ids) -> dict:
    """打出 1–5 张手牌。

    Args:
        session: 游戏会话。
        card_ids: 稳定卡牌 ID 列表（如 ``["c7h","c7d"]``）。

    Returns:
        成功：新 observation + reward（本手得分）+ terminated/truncated + info.score（完整计分过程）；
        失败：统一错误结构（BAD_REQUEST/UNKNOWN_CARD/DUPLICATE_CARD/INVALID_STATE/...）。
    """
    def _impl() -> dict:
        assert session.env is not None
        result = session.env.step({"kind": "play", "card_ids": list(card_ids)})
        return _state_payload(session.env, result.reward, result.terminated,
                              result.truncated, result.info)

    return _run(session, _impl)


def discard_cards(session: GameSession, card_ids) -> dict:
    """弃掉 1–5 张手牌（消耗 1 次 discard 并补牌）。

    Returns:
        成功：新 observation（reward=0）或统一错误结构。
    """
    def _impl() -> dict:
        assert session.env is not None
        result = session.env.step({"kind": "discard", "card_ids": list(card_ids)})
        return _state_payload(session.env, 0, result.terminated, result.truncated, result.info)

    return _run(session, _impl)


def choose_joker(session: GameSession, index: int | None = None) -> dict:
    """商店工具：买入第 index 个报价（花钱），``None`` 表示离开商店。

    只有 shop 阶段（Small/Big 通关后）可用；买不起 / 槽位满返回 ``NO_RESOURCE``，
    非商店阶段返回 ``INVALID_STATE``。买入后仍停在商店，可继续买/卖/reroll，最后
    显式离开才进入下一盲注。
    """
    def _impl() -> dict:
        assert session.env is not None
        result = session.env.step({"kind": "choose_joker", "joker_index": index})
        return _state_payload(session.env, 0, result.terminated, result.truncated, result.info)

    return _run(session, _impl)


def sell_joker(session: GameSession, index: int) -> dict:
    """商店工具：卖掉第 index 个已拥有的 Joker，返还半价并腾出槽位。"""
    def _impl() -> dict:
        assert session.env is not None
        result = session.env.step({"kind": "sell_joker", "joker_index": index})
        return _state_payload(session.env, 0, result.terminated, result.truncated, result.info)

    return _run(session, _impl)


def reroll_shop(session: GameSession) -> dict:
    """商店工具：花 ``reroll_cost`` 换一批报价（同一商店内每 reroll 一次涨价 $1）。"""
    def _impl() -> dict:
        assert session.env is not None
        result = session.env.step({"kind": "reroll_shop"})
        return _state_payload(session.env, 0, result.terminated, result.truncated, result.info)

    return _run(session, _impl)


def reset_episode(session: GameSession, *, seed: int | None = None,
                  hand_ids=None, joker_ids=(), blind_idx: int | None = None,
                  total_score: int | None = None, hands_left: int | None = None,
                  discards_left: int | None = None, target: int | None = None,
                  money: int | None = None, shop_open: bool = False,
                  allowed_action_kinds=None, max_steps: int | None = None) -> dict:
    """重置到新 episode（可选固定手牌/Joker/盲注/资源/金钱，用于决策点场景）。

    Args:
        money: 覆盖初始金钱（商店决策点用）。
        shop_open: True 时 reset 后直接进入商店。

    Returns:
        新 episode 的 observation。
    """
    def _impl() -> dict:
        assert session.env is not None
        spec = ResetSpec(
            seed=int(seed if seed is not None else session.seed),
            hand_ids=tuple(hand_ids) if hand_ids is not None else None,
            joker_ids=tuple(joker_ids or ()),
            ruleset=session.ruleset,
            allowed_action_kinds=tuple(allowed_action_kinds) if allowed_action_kinds else None,
            max_steps=max_steps,
            blind_idx=blind_idx,
            total_score=total_score,
            hands_left=hands_left,
            discards_left=discards_left,
            target=target,
            money=money,
            shop_open=bool(shop_open),
        )
        observation = session.env.reset(spec)
        return _ok({"observation": observation,
                    "text": render_observation(observation),
                    "reward": 0, "terminated": False, "truncated": False, "info": {}})

    return _run(session, _impl)


# 工具注册表：名称 → (函数, JSON schema 片段)。MCP / 本地 runner 共用同一份声明，
# 避免“工具描述一份、实现一份”的漂移（plan D6：工具声明是单一事实源）。
TOOL_SPECS: dict[str, dict] = {
    "get_state": {
        "description": "Return the current observation and a compact text summary.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "play_cards": {
        "description": "Play 1-5 cards from hand by stable card ids (e.g. c7h).",
        "parameters": {
            "type": "object",
            "properties": {"card_ids": {"type": "array", "items": {"type": "string"},
                                        "minItems": 1, "maxItems": 5}},
            "required": ["card_ids"], "additionalProperties": False,
        },
    },
    "discard_cards": {
        "description": "Discard 1-5 cards from hand by stable card ids.",
        "parameters": {
            "type": "object",
            "properties": {"card_ids": {"type": "array", "items": {"type": "string"},
                                        "minItems": 1, "maxItems": 5}},
            "required": ["card_ids"], "additionalProperties": False,
        },
    },
    "choose_joker": {
        "description": "Shop: buy the joker offer at index (costs money); null means leave the shop.",
        "parameters": {
            "type": "object",
            "properties": {"index": {"type": ["integer", "null"]}},
            "required": ["index"], "additionalProperties": False,
        },
    },
    "sell_joker": {
        "description": "Shop: sell the owned joker at slot index for half its price.",
        "parameters": {
            "type": "object",
            "properties": {"index": {"type": "integer", "minimum": 0}},
            "required": ["index"], "additionalProperties": False,
        },
    },
    "reroll_shop": {
        "description": "Shop: pay the reroll cost to draw a new set of offers (+$1 each reroll).",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "reset_episode": {
        "description": "Start a new episode, optionally with a fixed hand/seed/state/money.",
        "parameters": {
            "type": "object",
            "properties": {
                "seed": {"type": "integer"},
                "hand_ids": {"type": "array", "items": {"type": "string"}},
                "joker_ids": {"type": "array", "items": {"type": "string"}},
                "blind_idx": {"type": "integer", "minimum": 0, "maximum": 2},
                "total_score": {"type": "integer", "minimum": 0},
                "hands_left": {"type": "integer", "minimum": 0},
                "discards_left": {"type": "integer", "minimum": 0},
                "target": {"type": "integer", "minimum": 1},
                "money": {"type": "integer", "minimum": 0},
                "shop_open": {"type": "boolean"},
                "allowed_action_kinds": {"type": "array", "items": {"type": "string"}},
                "max_steps": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
    },
}


def dispatch_tool(session: GameSession, name: str, arguments: dict | None = None) -> dict:
    """按工具名分派调用（MCP 适配器与本地 runner 共用）。

    Raises:
        不抛出 ``BenchError``：非法工具名返回 BAD_REQUEST 结构。
    """
    args = arguments or {}
    if name == "get_state":
        return get_state(session)
    if name == "play_cards":
        return play_cards(session, args.get("card_ids"))
    if name == "discard_cards":
        return discard_cards(session, args.get("card_ids"))
    if name == "choose_joker":
        return choose_joker(session, args.get("index"))
    if name == "sell_joker":
        return sell_joker(session, args.get("index"))
    if name == "reroll_shop":
        return reroll_shop(session)
    if name == "reset_episode":
        return reset_episode(session, **{k: v for k, v in args.items() if k in TOOL_SPECS[name]["parameters"]["properties"]})
    return _error(InvalidActionError(BAD_REQUEST, f"unknown tool: {name!r}"))
