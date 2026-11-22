"""MCP 薄壳：把 bench.tools 暴露为 MCP 工具（stdio）。

职责边界（plan D6/D7）：
- 只做协议适配与参数转发：``bench.tools`` 是工具行为与错误码的唯一实现；
- **不实现规则**、不复算分数、不读写游戏文件；
- MCP SDK 只在启动时导入，因此本模块可以在没有安装 mcp 的环境里被静态检查/测试。

进程模型：一个 server 进程持有一个 ``GameSession``（单局串行）；并发评测由
``evaluation.batch_runner`` 在多进程中完成，而不是在一个 server 里共享全局状态。
"""
from __future__ import annotations

import json
import sys

from bench.tools import GameSession, TOOL_SPECS, dispatch_tool


def log(message: str) -> None:
    """日志写 stderr（stdout 是 MCP 协议流，不能被日志污染）。"""
    print(message, file=sys.stderr, flush=True)


# 会话默认按 seed=20261112 初始化；MCP 客户端可用 reset_episode 覆盖。
SESSION = GameSession(seed=20261112)


def _tool_result(payload: dict) -> str:
    """统一工具返回：JSON 字符串（MCP 工具只返回可序列化内容）。"""
    return json.dumps(payload, ensure_ascii=False)


def get_state() -> str:
    """返回当前 observation + 紧凑文本（规则/阶段/手牌/Joker/合法动作计数）。"""
    return _tool_result(dispatch_tool(SESSION, "get_state"))


def play_cards(card_ids: list[str]) -> str:
    """打出 1–5 张手牌（稳定卡牌 ID，如 ["c7h","c7d"]），返回新状态与计分过程。"""
    return _tool_result(dispatch_tool(SESSION, "play_cards", {"card_ids": card_ids}))


def discard_cards(card_ids: list[str]) -> str:
    """弃掉 1–5 张手牌（消耗 1 次 discard 并补牌）。"""
    return _tool_result(dispatch_tool(SESSION, "discard_cards", {"card_ids": card_ids}))


def choose_joker(index: int | None = None) -> str:
    """商店工具：买入第 index 个报价（花钱），null 表示离开商店。"""
    return _tool_result(dispatch_tool(SESSION, "choose_joker", {"index": index}))


def sell_joker(index: int) -> str:
    """商店工具：卖掉第 index 个已拥有的 Joker（返还半价，腾出槽位）。"""
    return _tool_result(dispatch_tool(SESSION, "sell_joker", {"index": index}))


def reroll_shop() -> str:
    """商店工具：花 reroll 价换一批报价。"""
    return _tool_result(dispatch_tool(SESSION, "reroll_shop"))


def reset_episode(seed: int | None = None, hand_ids: list[str] | None = None,
                  joker_ids: list[str] | None = None, blind_idx: int | None = None,
                  total_score: int | None = None, hands_left: int | None = None,
                  discards_left: int | None = None, target: int | None = None,
                  money: int | None = None, shop_open: bool = False,
                  allowed_action_kinds: list[str] | None = None,
                  max_steps: int | None = None) -> str:
    """开始新 episode（可固定手牌/种子/资源/金钱，用于决策点场景）。"""
    return _tool_result(dispatch_tool(SESSION, "reset_episode", {
        "seed": seed, "hand_ids": hand_ids, "joker_ids": joker_ids,
        "blind_idx": blind_idx, "total_score": total_score,
        "hands_left": hands_left, "discards_left": discards_left,
        "target": target, "money": money, "shop_open": shop_open,
        "allowed_action_kinds": allowed_action_kinds,
        "max_steps": max_steps,
    }))


TOOL_FUNCTIONS = {
    "get_state": get_state,
    "play_cards": play_cards,
    "discard_cards": discard_cards,
    "choose_joker": choose_joker,
    "sell_joker": sell_joker,
    "reroll_shop": reroll_shop,
    "reset_episode": reset_episode,
}


def build_server():
    """构造 MCP Server 并注册工具（延迟导入 mcp，避免测试环境强依赖）。

    Raises:
        RuntimeError: 未安装 mcp SDK。
    """
    try:
        from mcp.server import MCPServer  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "mcp SDK is not installed in this interpreter; install 'mcp' or run via bridge/.venv"
        ) from exc
    server = MCPServer("balatro_bridge")
    for name, spec in TOOL_SPECS.items():
        fn = TOOL_FUNCTIONS[name]
        fn.__doc__ = spec["description"]
        server.tool()(fn)
    return server


def main() -> None:
    """启动 stdio MCP server。"""
    log("balatro_bridge starting on stdio")
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
