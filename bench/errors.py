"""BalatroEval 统一错误类型与错误码（规则层 / 环境层 / 工具层共用）。

设计目标：
- 规则引擎与工具层用**同一套错误码**描述失败，避免每层各造一套字符串；
- 错误对象可无损转成工具层 JSON（MCP `isError` 载荷），不依赖异常文本；
- 规则层（纯函数）不打印、不写文件，只抛出带 code 的异常。

错误码语义（与 plan/详细版/07 的工具错误码口径一致）：
- ``BAD_REQUEST``：参数形状不合法（缺字段、类型错、张数越界）。
- ``INVALID_STATE``：动作与当前阶段不匹配（例如 done 阶段继续出牌）。
- ``NOT_ALLOWED``：动作本身合法但当前场景/模式禁止（例如 play 决策点要求出牌时弃牌、
  shop 未启用时 choose_joker）。
- ``UNKNOWN_CARD``：动作引用了手牌中不存在的稳定卡牌 ID。
- ``DUPLICATE_CARD``：同一张牌在动作中被引用两次。
- ``NO_RESOURCE``：资源耗尽（无弃牌次数 / 无出牌次数）。
- ``EPISODE_DONE``：episode 已终止，不能再执行动作。
- ``UNSUPPORTED_RULE``：请求了规则子集明确排除的机制（Boss 效果、金钱、消耗品等）。
- ``INTERNAL``：不应发生的不变量破坏（防御性错误，出现即代码 bug）。

异常层级的唯一来源是 ``bench.errors``；``evaluation`` 与 ``bridge`` 只读取 ``code``，
不得复制错误码表。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


# 错误码常量：字符串值是协议的一部分，工具层会原样返回给 Agent。
BAD_REQUEST: Final = "BAD_REQUEST"
INVALID_STATE: Final = "INVALID_STATE"
NOT_ALLOWED: Final = "NOT_ALLOWED"
UNKNOWN_CARD: Final = "UNKNOWN_CARD"
DUPLICATE_CARD: Final = "DUPLICATE_CARD"
NO_RESOURCE: Final = "NO_RESOURCE"
EPISODE_DONE: Final = "EPISODE_DONE"
UNSUPPORTED_RULE: Final = "UNSUPPORTED_RULE"
INTERNAL: Final = "INTERNAL"
AGENT_ERROR: Final = "AGENT_ERROR"
TIMEOUT: Final = "TIMEOUT"

ERROR_CODES: Final[tuple[str, ...]] = (
    BAD_REQUEST,
    INVALID_STATE,
    NOT_ALLOWED,
    UNKNOWN_CARD,
    DUPLICATE_CARD,
    NO_RESOURCE,
    EPISODE_DONE,
    UNSUPPORTED_RULE,
    INTERNAL,
    AGENT_ERROR,
    TIMEOUT,
)


@dataclass(eq=True)
class BenchError(Exception):
    """所有 BalatroEval 业务异常的基类。

    Attributes:
        code: 上面 ``ERROR_CODES`` 中的一个稳定字符串。
        message: 人类可读说明；不含随机内容，便于测试断言与日志聚合。
        detail: 可选的结构化上下文（如非法张数、未知 ID 列表），会进入 trace。
    """

    code: str
    message: str
    detail: dict | None = None

    def __post_init__(self) -> None:
        if self.code not in ERROR_CODES:
            raise ValueError(f"unknown error code: {self.code!r}")
        Exception.__init__(self, f"{self.code}: {self.message}")

    def to_dict(self) -> dict:
        """转成工具层/轨迹层的 JSON 结构（``ok: false`` 由调用方添加）。"""
        payload: dict = {"code": self.code, "message": self.message}
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


class InvalidActionError(BenchError):
    """动作不合法：规则层与环境层统一抛这个类型。"""


class UnsupportedRuleError(BenchError):
    """规则子集明确排除的机制被请求。"""

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(UNSUPPORTED_RULE, message, detail)


class InternalInvariantError(BenchError):
    """不变量被破坏（代码 bug），不应由 Agent 输入触发。"""

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(INTERNAL, message, detail)
