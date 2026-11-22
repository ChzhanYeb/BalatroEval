"""Agent 协议与内置实现：脚本策略、Oracle 策略、随机策略、HTTP 模型适配器。

Agent 职责：把 observation + 合法动作 → 一个 ``Action``。Agent **不得**直接读游戏状态、
不得绕过环境校验；所有合法性由 Environment 最终判定（非法动作会被记录为 legality 失败）。

并发模型：
- 脚本 Agent（oracle/random/fixed）是同步 CPU 调用；异步 runner 用 ``asyncio.to_thread``
  包装，避免阻塞事件循环；
- 模型 Agent 实现 ``decide_async``，在等待网络时让出事件循环；并发上限由 batch runner
  的 ``agent_concurrency`` 信号量控制，重试/退避/超时/缓存都在本模块内处理。

可复现性：脚本 Agent 的随机性只来自显式 seed；模型 Agent 的采样参数进入缓存键，
相同请求命中缓存时不重复计费。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, Sequence, runtime_checkable

from bench.actions import Action
from bench.errors import AGENT_ERROR, BAD_REQUEST, TIMEOUT, BenchError
from bench.model import GameState, Joker, card_from_id
from bench.observation import render_observation
from bench.oracle import best_play, discard_ev


@dataclass(frozen=True, slots=True)
class AgentDecision:
    """Agent 的一次决策输出（含诊断元数据）。

    Attributes:
        action: 解析出的动作；None 表示本次决策失败。
        raw_output: 模型原始输出（脚本 Agent 为 None）。
        usage: token/成本信息（如 ``{"prompt_tokens":..}``）；脚本 Agent 为空 dict。
        error_code: 失败时的错误码（AGENT_ERROR/BAD_REQUEST/TIMEOUT）。
        error_message: 人类可读失败原因。
        latency_ms: Agent 侧耗时（runner 也会独立计时）。
    """

    action: Action | None
    raw_output: str | None = None
    usage: dict = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: float = 0.0

    @property
    def ok(self) -> bool:
        """是否成功产出动作。"""
        return self.action is not None and self.error_code is None


@runtime_checkable
class Agent(Protocol):
    """同步 Agent 协议。"""

    agent_id: str

    def decide(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        ...


@runtime_checkable
class AsyncAgent(Protocol):
    """异步 Agent 协议（模型调用推荐）。"""

    agent_id: str

    async def decide_async(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        ...


async def decide_async(agent: Agent | AsyncAgent, observation: dict,
                       legal_actions: Sequence[Action]) -> AgentDecision:
    """统一调用入口：优先 ``decide_async``，否则把同步 ``decide`` 放入线程池。"""
    if hasattr(agent, "decide_async"):
        return await agent.decide_async(observation, legal_actions)  # type: ignore[union-attr]
    return await asyncio.to_thread(agent.decide, observation, legal_actions)


# --------------------------------------------------------------------- scripted
@dataclass
class CallableAgent:
    """用一个函数实现的脚本 Agent（测试与自定义策略的入口）。"""

    agent_id: str
    fn: Callable[[dict, Sequence[Action]], Action | dict | None]

    def decide(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        start = time.perf_counter()
        try:
            value = self.fn(observation, legal_actions)
        except BenchError as exc:
            return AgentDecision(None, error_code=exc.code, error_message=exc.message,
                                 latency_ms=(time.perf_counter() - start) * 1000)
        except Exception as exc:  # noqa: BLE001
            return AgentDecision(None, error_code=AGENT_ERROR,
                                 error_message=f"{type(exc).__name__}: {exc}",
                                 latency_ms=(time.perf_counter() - start) * 1000)
        latency = (time.perf_counter() - start) * 1000
        if value is None:
            return AgentDecision(None, error_code=AGENT_ERROR, error_message="agent returned None",
                                 latency_ms=latency)
        action = value if isinstance(value, Action) else Action.from_dict(value)
        return AgentDecision(action, latency_ms=latency)


@dataclass
class FirstLegalAgent:
    """总是选择第一个合法动作（用于 smoke test / 负对照）。"""

    agent_id: str = "first-legal"

    def decide(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        if not legal_actions:
            return AgentDecision(None, error_code=AGENT_ERROR, error_message="no legal actions")
        return AgentDecision(legal_actions[0])


@dataclass
class RandomAgent:
    """确定性随机 Agent：seed 由构造参数决定，动作按 legal_actions 均匀抽样。"""

    seed: int = 0
    agent_id: str = "random"

    def decide(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        if not legal_actions:
            return AgentDecision(None, error_code=AGENT_ERROR, error_message="no legal actions")
        step = int(observation.get("episode", {}).get("step", 0))
        rng = random.Random(self.seed * 1_000_003 + step)
        return AgentDecision(rng.choice(list(legal_actions)))


@dataclass
class OracleGreedyAgent:
    """局部最强脚本策略：play 用 O1 精确 argmax；discard 用 O2 近似 EV；
    商店「能买就买第一个报价，否则离开」（不 reroll、不卖、不为利息存钱）。

    这是“局部贪心参照”，不是全局最优，也不是经济最优；用于 golden/integration 测试
    与负对照基线。
    """

    agent_id: str = "oracle-greedy"
    discard_samples: int = 10

    def decide(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        if not legal_actions:
            return AgentDecision(None, error_code=AGENT_ERROR, error_message="no legal actions")
        kinds = observation.get("allowed_action_kinds")
        state = _state_from_observation(observation)
        if any(a.kind == "play" for a in legal_actions) and (kinds is None or "play" in kinds):
            best = best_play(state)
            return AgentDecision(Action("play", card_ids=best.card_ids))
        if any(a.kind == "discard" for a in legal_actions):
            evs = discard_ev(state, K=self.discard_samples)
            best_ev = max(evs, key=lambda item: (item.mean, -item.indices[0] if item.indices else 0))
            return AgentDecision(Action("discard", card_ids=best_ev.card_ids))
        # shop 阶段：买第一个买得起的，否则离开（legal_actions 已过滤掉买不起的报价）
        buy = [a for a in legal_actions if a.kind == "choose_joker" and a.joker_index is not None]
        if buy:
            return AgentDecision(buy[0])
        leave = [a for a in legal_actions if a.kind == "choose_joker" and a.joker_index is None]
        if leave:
            return AgentDecision(leave[0])
        return AgentDecision(legal_actions[0])


def _state_from_observation(observation: dict) -> GameState:
    """从 observation 重建 best_play 需要的最小状态（hand/jokers/money/phase）。

    注意：这不是完整状态（没有 deck/rng）；只用于 Agent 侧的局部评估，不能用于推进游戏。
    """
    hand = [card_from_id(item["id"]) for item in observation.get("hand", [])]
    jokers = [Joker.from_dict(item) for item in observation.get("jokers", [])]
    blind = observation.get("blind", {})
    economy = observation.get("economy", {})
    return GameState(
        blind_idx=int(blind.get("index", 0)),
        blind_kind=blind.get("kind", "small"),
        target=int(blind.get("target", 300)),
        total_score=int(blind.get("score", 0)),
        hand=hand,
        jokers=jokers,
        hands_left=int(blind.get("hands_left", 0)),
        discards_left=int(blind.get("discards_left", 0)),
        money=int(economy.get("money", 0)),
        phase=observation.get("episode", {}).get("phase", "play"),
    )


# ------------------------------------------------------------------- model agent
class ResponseCache:
    """模型响应的本地 SQLite 缓存（键 = 模型 + 请求体 + 采样参数的 sha256）。"""

    def __init__(self, path: str | None = None) -> None:
        self.path = path
        self._conn: sqlite3.Connection | None = None
        if path is not None:
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            self._conn.commit()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def make_key(request: dict) -> str:
        payload = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> str | None:
        if self._conn is None:
            return None
        row = self._conn.execute("SELECT value FROM responses WHERE key = ?", (key,)).fetchone()
        if row is None:
            self.misses += 1
            return None
        self.hits += 1
        return str(row[0])

    def put(self, key: str, value: str) -> None:
        if self._conn is None:
            return
        self._conn.execute("INSERT OR REPLACE INTO responses (key, value) VALUES (?, ?)", (key, value))
        self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()


class TokenBucket:
    """异步令牌桶（限制模型请求速率）。"""

    def __init__(self, rate_per_second: float, burst: int = 1) -> None:
        self.rate = rate_per_second
        self.capacity = max(1, burst)
        self.tokens = float(self.capacity)
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens < 1:
                await asyncio.sleep((1 - self.tokens) / self.rate)
                self.tokens = 0.0
                self.updated = time.monotonic()
            else:
                self.tokens -= 1


def default_prompt_builder(observation: dict, legal_actions: Sequence[Action]) -> list[dict]:
    """构造 OpenAI Chat Completions 风格的消息（可替换）。

    只把紧凑 observation 与“动作种类/数量”给模型，不把 436 条候选全塞进上下文。
    """
    observation_text = render_observation(observation)
    kinds = sorted({a.kind for a in legal_actions})
    system = (
        "You are playing a deterministic Balatro rules subset. Reply with ONE JSON object only: "
        '{"kind":"play","card_ids":["c7h","c7d"]} or {"kind":"discard","card_ids":[...]} '
        'or a shop action: {"kind":"choose_joker","index":0} (buy), '
        '{"kind":"choose_joker","index":null} (leave), {"kind":"sell_joker","index":0}, '
        '{"kind":"reroll_shop"}. Use stable card ids from the hand. '
        "Money is the only resource that carries across blinds; interest pays $1 per $5 held "
        "(cap $5) at the next blind clear."
    )
    user = (
        f"{observation_text}\nAllowed action kinds: {kinds}\n"
        f"Legal action counts: {observation.get('legal_action_counts')}\n"
        "Choose the best action. JSON only."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_action_text(text: str) -> Action:
    """从模型输出中解析动作 JSON（容忍前后解释文字）。

    Raises:
        BenchError(BAD_REQUEST): 找不到 JSON/字段非法。
    """
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise BenchError(BAD_REQUEST, "model output contains no JSON object")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise BenchError(BAD_REQUEST, f"model output JSON invalid: {exc}") from exc
    return Action.from_dict(data)


class HttpChatAgent:
    """异步 HTTP 模型适配器（OpenAI-compatible chat completions）。

    Attributes:
        transport: async callable(request: dict) -> dict（至少含 ``text``；可选 ``usage``）。
            测试中注入 fake transport，不依赖真实服务。
        cache: 可选 ``ResponseCache``；键包含模型、messages、temperature、max_tokens。
        rate_limiter: 可选 ``TokenBucket``。
        max_retries / backoff_s / timeout_s: 失败重试与超时策略。
    """

    def __init__(
        self,
        agent_id: str,
        model: str,
        *,
        transport: Callable[[dict], Awaitable[dict]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 256,
        prompt_builder: Callable[[dict, Sequence[Action]], list[dict]] = default_prompt_builder,
        cache: ResponseCache | None = None,
        rate_limiter: TokenBucket | None = None,
        max_retries: int = 3,
        backoff_s: float = 0.5,
        timeout_s: float = 30.0,
    ) -> None:
        self.agent_id = agent_id
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_builder = prompt_builder
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self.timeout_s = timeout_s
        self.transport = transport or _urllib_transport
        self.request_count = 0
        self.total_usage: dict[str, int] = {}

    async def decide_async(self, observation: dict, legal_actions: Sequence[Action]) -> AgentDecision:
        """构造请求 → 缓存/限流/重试 → 解析动作。"""
        start = time.perf_counter()
        messages = self.prompt_builder(observation, legal_actions)
        request = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        key = ResponseCache.make_key(request)
        text: str | None = self.cache.get(key) if self.cache else None
        usage: dict = {}
        if text is None:
            last_error: Exception | None = None
            for attempt in range(self.max_retries):
                try:
                    if self.rate_limiter is not None:
                        await self.rate_limiter.acquire()
                    response = await asyncio.wait_for(self.transport(request), timeout=self.timeout_s)
                    text = str(response.get("text", ""))
                    usage = dict(response.get("usage", {}))
                    self.request_count += 1
                    for name, value in usage.items():
                        if isinstance(value, int):
                            self.total_usage[name] = self.total_usage.get(name, 0) + value
                    if self.cache:
                        self.cache.put(key, text)
                    break
                except asyncio.TimeoutError:
                    last_error = asyncio.TimeoutError()
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                await asyncio.sleep(self.backoff_s * (2 ** attempt))
            if text is None:
                code = TIMEOUT if isinstance(last_error, asyncio.TimeoutError) else AGENT_ERROR
                return AgentDecision(None, error_code=code,
                                     error_message=f"{type(last_error).__name__}: {last_error}",
                                     latency_ms=(time.perf_counter() - start) * 1000)
        try:
            action = parse_action_text(text)
        except BenchError as exc:
            return AgentDecision(None, raw_output=text, usage=usage, error_code=exc.code,
                                 error_message=exc.message,
                                 latency_ms=(time.perf_counter() - start) * 1000)
        return AgentDecision(action, raw_output=text, usage=usage,
                             latency_ms=(time.perf_counter() - start) * 1000)


async def _urllib_transport(request: dict) -> dict:
    """默认 HTTP transport：POST 到 ``BALATROEVAL_LLM_URL``（OpenAI-compatible）。

    环境变量：
        BALATROEVAL_LLM_URL: 完整 chat/completions 端点；
        BALATROEVAL_LLM_KEY: 可选 Bearer token。

    说明：本函数仅作示例适配器；未内置任何供应商默认地址。无 URL 时抛 RuntimeError，
    由调用方/重试逻辑转成 AGENT_ERROR。
    """
    import os

    url = os.environ.get("BALATROEVAL_LLM_URL")
    if not url:
        raise RuntimeError("BALATROEVAL_LLM_URL is not configured")
    key = os.environ.get("BALATROEVAL_LLM_KEY", "")

    def _post() -> dict:
        data = json.dumps(request).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json",
                                              **({"Authorization": f"Bearer {key}"} if key else {})})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - 显式配置端点
            payload = json.loads(resp.read().decode("utf-8"))
        return {
            "text": payload["choices"][0]["message"]["content"],
            "usage": payload.get("usage", {}),
        }

    return await asyncio.to_thread(_post)
