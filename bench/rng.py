"""可复现的随机数状态（RNG state）序列化辅助函数。

职责：把 random.Random.getstate() 的完整随机数状态编码为 JSON 文本，并能无损还原。

边界／不变量：
- 只保存随机数状态、不保存 seed；同一个编码必然还原出同一段后续随机流。
- 编码是 JSON 文本，可安全写入 episode 日志（经 state_summary 落盘）。
- 本模块不会推进任何既有随机流：encode／decode／restore 都不让原（或还原出的）
  随机流前进一步；只有调用方在还原出的实例上调用 random 方法才会推进。
- 这不是跨 Python 大版本的稳定格式：getstate 布局属于 CPython 实现细节，
  升级解释器或更换 RNG 算法可能使旧日志无法还原（保真度边界）。

维护提示：改动编码格式前先看 bench/engine.py（encode_state／restore_rng 的
唯一生产调用方）与 tests/test_w2_rules.py 的 test_rng_state_full_round_trip。
"""
from __future__ import annotations
import json
import random
from typing import Any


def _lists_to_tuples(value: Any) -> Any:
    """递归把 JSON 还原出的 list 转回 tuple（random.setstate 要求 tuple）。

    json.loads 只能产出 list，而 getstate() 的内层是嵌套 tuple；setstate 对
    容器类型敏感，直接传 list 会抛 TypeError，所以必须显式还原。dict 的值同样
    递归处理（键保持字符串），当前随机数状态里没有 dict，此为通用性保留。
    返回：转换后的新容器，不修改入参。异常：无。副作用：无。
    """
    if isinstance(value, list):
        return tuple(_lists_to_tuples(x) for x in value)
    if isinstance(value, dict):
        return {k: _lists_to_tuples(v) for k, v in value.items()}
    return value


def encode_state(rng: random.Random) -> str:
    """把 rng 的完整 getstate() 编码为紧凑 JSON 文本。

    参数：任意 random.Random 实例，函数不会推进它。
    返回：JSON 字符串（分隔符为 "," 与 ":"，无多余空白），可直接作为
    日志字段值；超大整数由 json 支持。
    异常：无。副作用：无（不消耗随机数）。
    """
    return json.dumps(rng.getstate(), separators=(",", ":"))


def decode_state(encoded: str) -> tuple:
    """把 encode_state 的产物还原成 random.setstate 可接受的状态元组。

    参数：encoded 为 JSON 文本。
    返回：顶层 tuple，结构为 getstate 的 (version, internal_state, gauss_next)。
    异常：JSON 非法时抛 json.JSONDecodeError；顶层解码后不是 list（因此不是
    tuple）时抛 ValueError("serialized random state must decode to a tuple")。
    副作用：无。
    """
    raw = json.loads(encoded)
    value = _lists_to_tuples(raw)
    if not isinstance(value, tuple):
        raise ValueError("serialized random state must decode to a tuple")
    return value


def restore_rng(encoded: str) -> random.Random:
    """从编码文本构造一个处于相同随机数状态的新 random.Random 实例。

    参数：encoded 为 encode_state 的产物。
    返回：新实例；它此后产生的随机序列与原实例在编码时刻之后完全一致。
    异常：decode_state 抛出的异常；状态结构不合法时由 random.setstate 抛
    TypeError／ValueError。
    副作用：不修改任何已有 rng；新实例与调用方各自独立推进。
    """
    rng = random.Random()
    rng.setstate(decode_state(encoded))
    return rng


def state_round_trip_ok(encoded: str) -> bool:
    """校验「编码 → 还原 → 再编码」是否逐字符一致（保真度自检）。

    只做编解码，不调用 random()，因此不推进编码所描述的随机流；意义在于：日志里的
    rng_state 必须能被离线精确还原，否则重放与 oracle 对拍会静默漂移。
    返回：一致为 True，否则 False。异常：与 decode_state 相同。
    """
    rng = restore_rng(encoded)
    return encode_state(rng) == encoded
