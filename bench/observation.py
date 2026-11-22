"""Observation 构造与紧凑文本渲染（给 Agent 看的状态视图）。

设计取舍：
- Observation 是**给 Agent 的公开视图**，不包含 oracle 结果、内部 RNG、完整牌堆顺序；
- 手牌给稳定 ID + 展示标签 + 点数筹码，Agent 用 ID 组动作；
- 合法动作只给**计数**（8 张手牌时 play/discard 各 218），不给完整 436 条列表：
  否则单次 observation 会吞掉小模型的上下文预算。需要完整动作集时用
  ``Environment.legal_actions()``（离线评测/Oracle 用，不交给 Agent）；
- 文本渲染目标 ≤ 250 token（按 “字符数/4” 粗估），用于 MCP ``get_state``。

Observation schema（``OBSERVATION_SCHEMA_VERSION=1``）是工具契约的一部分，字段名不得
随实现漂移；新增字段必须升版本并在 docs/implementation/data-schema.md 记录。
"""
from __future__ import annotations

from .actions import legal_discards, legal_plays
from .model import GameState
from .rules_version import VANILLA_SUBSET_V1, Ruleset

OBSERVATION_SCHEMA_VERSION = 1


def build_observation(
    state: GameState,
    ruleset: Ruleset = VANILLA_SUBSET_V1,
    allowed_action_kinds: tuple[str, ...] | None = None,
) -> dict:
    """把 ``GameState`` 转成 Agent 可见的 observation dict。

    Args:
        state: 当前状态。
        ruleset: 规则集（用于读取盲注名称与规则版本）。
        allowed_action_kinds: 场景约束的动作种类；None 表示不限制。用于告诉 Agent
            “这是出牌决策点，还是弃牌决策点”。

    Returns:
        JSON 可序列化 dict；字段见模块 docstring。

    确定性：纯函数，不修改 state。
    """
    spec = ruleset.blind(state.blind_idx)
    play_count = 0
    discard_count = 0
    if state.phase == "play":
        play_count = len(legal_plays(state.hand, ruleset.max_play_cards))
        discard_count = len(legal_discards(state.hand, state.discards_left,
                                           ruleset.max_discard_cards))
        if allowed_action_kinds is not None:
            if "play" not in allowed_action_kinds:
                play_count = 0
            if "discard" not in allowed_action_kinds:
                discard_count = 0
    return {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "rules_version": state.rules_version,
        "target_game_version": ruleset.target_game_version,
        "allowed_action_kinds": list(allowed_action_kinds) if allowed_action_kinds else None,
        "episode": {
            "phase": state.phase,
            "outcome": state.outcome,
            "step": state.steps,
            "terminated": state.phase == "done",
        },
        "blind": {
            "index": state.blind_idx,
            "kind": state.blind_kind,
            "name": spec.name,
            "target": state.target,
            "score": state.total_score,
            "score_needed": max(0, state.target - state.total_score),
            "hands_left": state.hands_left,
            "discards_left": state.discards_left,
            "boss_effect": state.boss_effect,
            "boss_effect_implemented": state.boss_effect is None,
        },
        "hand": [
            {
                "id": card.card_id,
                "label": card.label,
                "suit": card.suit_name,
                "rank": card.rank,
                "rank_label": card.rank_label,
                "chips": card.chips,
            }
            for card in state.hand
        ],
        "hand_size": len(state.hand),
        "hand_size_limit": state.hand_size,
        "deck_count": len(state.deck),
        "discard_count": len(state.discard_pile),
        "jokers": [joker.to_dict() for joker in state.jokers],
        "joker_slots": state.joker_slots,
        "shop_options": [joker.to_dict() for joker in state.shop_options],
        "legal_action_counts": {"play": play_count, "discard": discard_count},
    }


def render_observation(observation: dict, max_chars: int = 1000) -> str:
    """把 observation 渲染成紧凑多行文本（供 LLM 工具返回）。

    Args:
        observation: ``build_observation`` 的产物。
        max_chars: 输出字符上限（超出时截断并给提示）。

    Returns:
        多行字符串；典型输出约 400–700 字符（≈100–175 token）。

    说明：token 估算按 ``len(text)/4`` 仅为经验值，不是精确 tokenizer 计数。
    """
    episode = observation["episode"]
    blind = observation["blind"]
    lines = [
        f"rules={observation['rules_version']} phase={episode['phase']} step={episode['step']}",
        f"blind={blind['name']}({blind['kind']}) target={blind['target']} score={blind['score']} "
        f"need={blind['score_needed']} hands={blind['hands_left']} discards={blind['discards_left']}",
    ]
    if blind["boss_effect"] is not None:
        lines.append(f"boss_effect={blind['boss_effect']} (NOT implemented in this subset)")
    hand_text = " ".join(f"{c['label']}={c['id']}({c['chips']})" for c in observation["hand"])
    lines.append(f"hand({len(observation['hand'])}/{observation['hand_size_limit']}): {hand_text}")
    if observation["jokers"]:
        joker_text = " ".join(
            f"{j['name']}[{j['kind']}:{j['value']},{j['condition']}]" for j in observation["jokers"]
        )
        lines.append(f"jokers({len(observation['jokers'])}/{observation['joker_slots']}): {joker_text}")
    else:
        lines.append("jokers: none")
    lines.append(f"deck={observation['deck_count']} discard={observation['discard_count']} "
                 f"legal_play={observation['legal_action_counts']['play']} "
                 f"legal_discard={observation['legal_action_counts']['discard']}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[: max_chars - 40].rstrip() + "\n...[truncated]"
    return text
