"""状态快照、还原与稳定哈希。

用途：
- ``Environment.snapshot()/restore()``：把一局状态完整序列化，用于回放、分支实验与
  断点续跑；
- ``state_hash()``：为 trace 的每一步提供可核对的稳定指纹（同状态恒同哈希）。

不变量：
- 快照包含 52 张牌的全部牌面与顺序、Joker、资源、阶段、RNG 状态；**不允许**只存摘要；
- 还原后的状态与原状态逐字段相等（``GameState`` 是 dataclass，支持 ``==``）；
- 哈希使用 JSON 规范化（sort_keys + 紧凑分隔符）后 sha256，不受 dict 插入顺序影响。

快照版本（``SNAPSHOT_SCHEMA_VERSION``）：
- 1：rules_version / 完整状态 / cards 以稳定 ID 表示（v1 时代，无经济字段）。
- 2：新增 ``money`` / ``reroll_cost`` / ``last_payout``（economy v2）。
字段变更必须升版本并在 docs/implementation/data-schema.md 记录；旧版本快照会被显式
拒绝（经济字段缺失时无法还原出可信状态，宁可报错也不猜）。
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .cards import card_from_stable_id
from .errors import BAD_REQUEST, InvalidActionError
from .jokers import CATALOG_BY_ID
from .model import Card, GameState, Joker
from .rules_version import REROLL_BASE_COST, STARTING_MONEY, VANILLA_SUBSET_V1

SNAPSHOT_SCHEMA_VERSION = 2


def state_to_dict(state: GameState) -> dict:
    """把完整状态导出为 JSON 可序列化 dict（含全部牌面、经济与 RNG 状态）。

    Returns:
        dict；键集合即快照 schema（见 docs/implementation/data-schema.md）。
    """
    return {
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "rules_version": state.rules_version,
        "ante": state.ante,
        "blind_idx": state.blind_idx,
        "blind_kind": state.blind_kind,
        "boss_effect": state.boss_effect,
        "target": state.target,
        "joker_slots": state.joker_slots,
        "hand_size": state.hand_size,
        "shop_enabled": state.shop_enabled,
        "total_score": state.total_score,
        "hands_left": state.hands_left,
        "discards_left": state.discards_left,
        "money": state.money,
        "reroll_cost": state.reroll_cost,
        "last_payout": state.last_payout,
        "steps": state.steps,
        "phase": state.phase,
        "outcome": state.outcome,
        "hand": [c.card_id for c in state.hand],
        "deck": [c.card_id for c in state.deck],
        "discard_pile": [c.card_id for c in state.discard_pile],
        "jokers": [j.jid for j in state.jokers],
        "shop_options": [j.jid for j in state.shop_options],
        "seed": state.seed,
        "rng_state": state.rng_state,
    }


def state_from_dict(data: dict) -> GameState:
    """从 ``state_to_dict`` 的产物还原完整状态。

    Raises:
        InvalidActionError: 缺字段、未知卡牌/Joker ID、schema 版本不支持、重复牌。
    """
    if not isinstance(data, dict):
        raise InvalidActionError(BAD_REQUEST, "snapshot must be an object")
    version = data.get("snapshot_schema_version")
    if version != SNAPSHOT_SCHEMA_VERSION:
        raise InvalidActionError(
            BAD_REQUEST,
            f"unsupported snapshot schema version: {version!r}",
            {"supported": SNAPSHOT_SCHEMA_VERSION},
        )

    def _cards(ids: Any, field: str) -> list[Card]:
        if not isinstance(ids, list):
            raise InvalidActionError(BAD_REQUEST, f"{field} must be a list of card ids")
        cards = [card_from_stable_id(str(cid)) for cid in ids]
        if len({c.card_id for c in cards}) != len(cards):
            raise InvalidActionError(BAD_REQUEST, f"{field} contains duplicate card ids")
        return cards

    def _jokers(ids: Any, field: str) -> list[Joker]:
        if not isinstance(ids, list):
            raise InvalidActionError(BAD_REQUEST, f"{field} must be a list of joker ids")
        result: list[Joker] = []
        for jid in ids:
            try:
                result.append(CATALOG_BY_ID[str(jid)])
            except KeyError as exc:
                raise InvalidActionError(BAD_REQUEST, f"unknown joker id in {field}: {jid!r}") from exc
        return result

    hand = _cards(data.get("hand"), "hand")
    deck = _cards(data.get("deck"), "deck")
    discard_pile = _cards(data.get("discard_pile"), "discard_pile")
    all_ids = [c.card_id for c in hand + deck + discard_pile]
    if len(set(all_ids)) != len(all_ids):
        raise InvalidActionError(BAD_REQUEST, "snapshot contains the same physical card twice")
    if len(all_ids) != 52:
        raise InvalidActionError(BAD_REQUEST, f"snapshot must contain exactly 52 cards, got {len(all_ids)}")

    state = GameState(
        rules_version=str(data.get("rules_version", VANILLA_SUBSET_V1.rules_version)),
        ante=int(data.get("ante", 1)),
        blind_idx=int(data["blind_idx"]),
        blind_kind=data["blind_kind"],
        boss_effect=data.get("boss_effect"),
        target=int(data["target"]),
        joker_slots=int(data.get("joker_slots", 5)),
        hand_size=int(data.get("hand_size", 8)),
        shop_enabled=bool(data.get("shop_enabled", False)),
        total_score=int(data.get("total_score", 0)),
        hands_left=int(data["hands_left"]),
        discards_left=int(data["discards_left"]),
        money=int(data.get("money", STARTING_MONEY)),
        reroll_cost=int(data.get("reroll_cost", REROLL_BASE_COST)),
        last_payout=data.get("last_payout"),
        steps=int(data.get("steps", 0)),
        phase=data["phase"],
        outcome=data.get("outcome"),
        hand=hand,
        deck=deck,
        discard_pile=discard_pile,
        jokers=_jokers(data.get("jokers"), "jokers"),
        shop_options=_jokers(data.get("shop_options", []), "shop_options"),
        seed=int(data.get("seed", 0)),
        rng_state=str(data.get("rng_state", "")),
    )
    return state


def canonical_json(data: Any) -> str:
    """规范化 JSON：UTF-8 原样字符、键排序、紧凑分隔符（哈希与 diff 的稳定输入）。"""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def state_hash(state: GameState) -> str:
    """返回完整状态的 sha256 十六进制摘要（64 位）。"""
    return hashlib.sha256(canonical_json(state_to_dict(state)).encode("utf-8")).hexdigest()


def snapshot(state: GameState) -> dict:
    """返回带哈希的状态快照：``{"state": ..., "state_hash": ...}``。"""
    payload = state_to_dict(state)
    return {
        "state": payload,
        "state_hash": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
    }


def restore(snap: dict) -> GameState:
    """从 ``snapshot`` 产物还原状态，并校验 state_hash 一致。

    Raises:
        InvalidActionError: 结构非法或哈希不匹配（说明快照被篡改/损坏）。
    """
    if not isinstance(snap, dict) or "state" not in snap:
        raise InvalidActionError(BAD_REQUEST, "snapshot payload must contain 'state'")
    state = state_from_dict(snap["state"])
    if "state_hash" in snap:
        actual = state_hash(state)
        if actual != snap["state_hash"]:
            raise InvalidActionError(
                BAD_REQUEST, "snapshot hash mismatch",
                {"expected": snap["state_hash"], "actual": actual},
            )
    return state
