"""性能 smoke 测试：用宽松阈值防止无意退化（不是基准报告；真实数据见 docs/implementation/performance.md）。"""
from __future__ import annotations

import time
import unittest

from bench.engine import new_game
from bench.environment import Environment, ResetSpec
from bench.oracle import best_play
from bench.scoring import score_hand
from bench.model import Card


class TestPerformanceSmoke(unittest.TestCase):
    def test_scoring_is_fast(self):
        cards = [Card(0, 7), Card(1, 7), Card(2, 9), Card(3, 9), Card(0, 13)]
        start = time.perf_counter()
        for _ in range(500):
            score_hand(cards)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0)  # 500 次 < 2s（本机实测约 0.02s）

    def test_env_step_is_fast(self):
        env = Environment()
        env.reset(ResetSpec(seed=1))
        start = time.perf_counter()
        for _ in range(100):
            env.reset(ResetSpec(seed=1))
            action = next(a for a in env.legal_actions() if a.kind == "play")
            env.step(action)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 10.0)  # 100 次 reset+step < 10s（本机约 0.6s）

    def test_oracle_218_candidates_is_bounded(self):
        state = new_game(20261117)
        start = time.perf_counter()
        best_play(state)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.5)  # 本机约 5ms


if __name__ == "__main__":
    unittest.main()
