"""测试用临时目录：放在 workspace 的 runs/_test_tmp 下。

原因：本机 DSH 文件沙箱对系统临时目录的 chmod/删除会拒绝；workspace 内的 runs/ 可写且
可清理。每个测试用 uuid 子目录，退出时尽力删除（失败不掩盖测试结果）。
"""
from __future__ import annotations

import contextlib
import shutil
import uuid
from pathlib import Path

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / "runs" / "_test_tmp"


@contextlib.contextmanager
def workspace_tmp():
    """yield 一个新的临时目录路径（str）；退出时尽力清理。"""
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEST_TMP_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)
