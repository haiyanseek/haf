#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gap_driven_evolution.py — 一个可复现的「自进化闭环为什么会空转」实验包
=====================================================================
纯标准库 · 零依赖 · 离线可跑 · 任何人可复现

本文件回答两个工程问题（都来自真实生产系统的踩坑）：

    问题 1：为什么给一批**完全同构**的智能体（没有任何角色预设）
            它们却不会自己分工？
    问题 2：为什么把评分器写得更严格，模型反而学会了「表面合规」？

两条被实验支持的定律
--------------------
    【定律 1】世界缺口结构决定分工
        分工的上界 = 世界提供的缺口**类型数**。
        1 类缺口 → 动作熵 = 0.000（所有智能体挤在同一个动作上）
        K 类缺口 → 动作熵随 K 上升（可达 log2 K）
        ⇒ 想让智能体分化，**不是教它们分工，而是让世界有多种缺口**。

    【定律 2】判据强度 = 诚实下限
        弱判据（只看格式）→ 伪造标识符可以蒙混过关
        强判据（真去核验）→ 伪造被拦住
        ⇒ 但真正把伪造率压到 0 的不是「禁止伪造」，
          而是 **给模型「有得抄」**（把真实标识符放进素材里）。
          这是本包最重要的结论：**给模型有得抄，比禁止它编造有效一个量级。**

用法
----
    python3 gap_driven_evolution.py --run          # 跑全部实验并打印结论表
    python3 gap_driven_evolution.py --selftest     # 自检
    python3 gap_driven_evolution.py --json out.json  # 结果落盘

诚实边界（本包不做什么）
------------------------
- 本包用**确定性模拟**演示机制，不是 LLM 实测。真实生产系统上的实测数字见 README。
- 模拟里的 "Author"（作者模型）是**行为可配置的替身**，不是任何真实模型。
- 本包不声称重现任何外部系统的成绩。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# 缺口类型 —— 世界能提供多少种「值得做的事」
# ---------------------------------------------------------------------------
GAP_KINDS: Tuple[str, ...] = (
    "citation",    # 缺引用 / 出处
    "control",     # 缺对照 / 基线
    "repro",       # 缺可复现步骤
    "limitation",  # 缺局限与边界
    "number",      # 缺具体量化
    "crossref",    # 缺跨域关联
    "method",      # 缺方法细节
    "risk",        # 缺风险评估
)
GAP_TO_ACTION = {g: "add_" + g for g in GAP_KINDS}


# ---------------------------------------------------------------------------
# 实验 1：世界缺口结构 → 分工
# ---------------------------------------------------------------------------
@dataclass
class Item:
    """世界里的一个对象（可理解为一份知识卡 / 一个任务）"""
    id: str
    text: str


@dataclass
class Gap:
    kind: str
    item_id: str

    @property
    def action(self) -> str:
        return GAP_TO_ACTION[self.kind]


class World:
    """世界 —— 它「缺什么」由 gap_kinds 决定；智能体只能看见世界给的缺口"""

    def __init__(self, n_items: int, gap_kinds: Sequence[str], seed: int = 7):
        rng = random.Random(seed)
        self.gap_kinds = tuple(gap_kinds)
        self.items: List[Item] = []
        for i in range(n_items):
            # 每个对象随机缺其中若干类（至少一类）
            k = max(1, min(len(self.gap_kinds), rng.randint(1, max(1, len(self.gap_kinds)))))
            missing = rng.sample(list(self.gap_kinds), k) if len(self.gap_kinds) > 1 else list(self.gap_kinds)
            self.items.append(Item(id="it-%03d" % i, text="对象 %d 的正文" % i))
            setattr(self.items[-1], "_missing", set(missing))

    def gaps(self, item: Item) -> List[Gap]:
        return [Gap(kind=k, item_id=item.id) for k in sorted(getattr(item, "_missing", ()))]


def entropy(counter: Counter) -> float:
    """香农熵（bit）。0 = 完全没有分化"""
    total = sum(counter.values())
    if total <= 1:
        return 0.0
    h = 0.0
    for v in counter.values():
        p = v / total
        if p > 0:
            h -= p * math.log2(p)
    return round(h, 4)


@dataclass
class Agent:
    """同构智能体 —— **没有任何角色预设**，只有稳定的个体偏好（偏好来自 id 哈希）"""
    id: str
    policy: str = "preference"      # preference | round_robin

    def _affinity(self, gap_kind: str) -> float:
        h = hashlib.sha1(("%s|%s" % (self.id, gap_kind)).encode()).hexdigest()
        return int(h[:8], 16) / 0xFFFFFFFF

    def pick(self, gaps: List[Gap], idx: int) -> Optional[Gap]:
        if not gaps:
            return None
        if self.policy == "round_robin":
            return gaps[idx % len(gaps)]
        # 个体偏好：同构但不同偏好 -> 有选择空间时自然错开
        return max(gaps, key=lambda g: self._affinity(g.kind))


def experiment_division(n_agents: int = 60, n_items: int = 40,
                        kinds_counts: Sequence[int] = (1, 2, 3, 5, 8)) -> List[dict]:
    """定律 1：固定世界规模与智能体数量，只改变**缺口类型数**，看动作熵如何变化"""
    out = []
    for k in kinds_counts:
        kinds = GAP_KINDS[:k]
        world = World(n_items=n_items, gap_kinds=kinds)
        agents = [Agent(id="ag-%03d" % i) for i in range(n_agents)]
        actions = Counter()
        for a in agents:
            for idx, item in enumerate(world.items):
                g = a.pick(world.gaps(item), idx)
                if g:
                    actions[g.action] += 1
        out.append({
            "gap_kinds": k,
            "gap_kind_names": list(kinds),
            "actions": len(actions),
            "entropy": entropy(actions),
            "theoretical_max": round(math.log2(k), 4) if k > 1 else 0.0,
            "top_action_share": round(max(actions.values()) / sum(actions.values()), 4) if actions else 0.0,
        })
    return out


# ---------------------------------------------------------------------------
# 实验 2：判据强度 → 诚实下限
# ---------------------------------------------------------------------------
DOI_LIKE = re.compile(r"10\.\d{4,5}/[A-Za-z0-9._;()/:-]{4,40}")


@dataclass
class SourcePack:
    """素材包 —— 「有得抄」的关键载体"""
    real_ids: List[str] = field(default_factory=list)   # 真实存在的标识符


class Author:
    """作者模型（行为可配置的替身，不是任何真实模型）

    fabricate_prob: 当素材里**没有**可抄的真实标识符时，凭空编一个的概率
    """

    def __init__(self, fabricate_prob: float = 0.8, seed: Optional[int] = 11):
        self.rng = random.Random(seed)
        self.fabricate_prob = fabricate_prob

    def write_citation(self, sources: SourcePack) -> Tuple[str, bool]:
        """返回 (标识符, 是否伪造)"""
        if sources.real_ids:
            # ★ 有得抄 -> 直接抄真的（这是把伪造率压到 0 的真正原因）
            return self.rng.choice(sources.real_ids), False
        if self.rng.random() < self.fabricate_prob:
            # 编一个「格式完全正确」的编号 —— 格式判据抓不到它
            return "10.1021/jacs.%d.%s" % (
                self.rng.randint(2020, 2026),
                "".join(self.rng.choice("abcdef0123456789") for _ in range(6)),
            ), True
        return "（未核实）", False


class MockRegistry:
    """离线注册表 —— 模拟「真去核验」"""

    def __init__(self, known: Sequence[str]):
        self.known = set(known)

    def exists(self, identifier: str) -> bool:
        return identifier in self.known


class Judge:
    """三档判据：none / format / verify"""

    def __init__(self, level: str, registry: Optional[MockRegistry] = None):
        assert level in ("none", "format", "verify")
        self.level = level
        self.registry = registry

    def check(self, text: str) -> Tuple[bool, str]:
        if self.level == "none":
            return True, "无判据"
        if self.level == "format":
            return bool(DOI_LIKE.fullmatch(text.strip())), "格式判据"
        m = DOI_LIKE.fullmatch(text.strip())
        if not m:
            return False, "格式不合法"
        ok = bool(self.registry and self.registry.exists(text.strip()))
        return ok, ("核验通过" if ok else "核验失败：该编号不存在")


def experiment_judge(trials: int = 400, fabricate_prob: float = 0.8) -> List[dict]:
    """定律 2：同一作者模型，只改判据强度 / 有无素材，看伪造通过率"""
    real = ["10.1021/jacs.0c%04d" % i for i in range(50)]
    reg = MockRegistry(real)
    scenarios = [
        ("无判据 + 无素材",  Judge("none"),            SourcePack()),
        ("只查格式 + 无素材", Judge("format"),          SourcePack()),
        ("真核验 + 无素材",  Judge("verify", reg),     SourcePack()),
        ("只查格式 + 有素材", Judge("format"),          SourcePack(real_ids=real)),
        ("真核验 + 有素材",  Judge("verify", reg),     SourcePack(real_ids=real)),
    ]
    out = []
    for name, judge, src in scenarios:
        ok_fab = 0          # 伪造且被判通过
        ok_honest = 0
        total = trials
        for t in range(trials):
            # ★ 用「轮次」当种子：跨场景用同一串随机决策，
            #   否则各场景的随机噪声会掩盖结论（实测曾出现「格式判据 0.8275 > 无判据 0.8」
            #   这种纯噪声排序，把最有力的结论糊掉了）。
            author = Author(fabricate_prob=fabricate_prob, seed=t)
            ident, fabricated = author.write_citation(src)
            passed, _why = judge.check(ident)
            if passed and fabricated:
                ok_fab += 1
            if passed and not fabricated:
                ok_honest += 1
        out.append({
            "scenario": name,
            "accepted_fabricated_rate": round(ok_fab / total, 4),
            "accepted_honest_rate": round(ok_honest / total, 4),
        })
    return out


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def selftest() -> int:
    checks: List[Tuple[str, bool]] = []

    # 熵的定义
    checks.append(("熵：单点分布 = 0", entropy(Counter({"a": 10})) == 0.0))
    checks.append(("熵：均匀两点 = 1", entropy(Counter({"a": 5, "b": 5})) == 1.0))
    checks.append(("熵：空输入 = 0", entropy(Counter()) == 0.0))

    # 定律 1 —— 1 类缺口必须熵为 0
    r1 = experiment_division(n_agents=30, n_items=20, kinds_counts=(1, 5))
    d1, d5 = r1[0], r1[1]
    checks.append(("1 类缺口 -> 动作熵 = 0", d1["entropy"] == 0.0))
    checks.append(("1 类缺口 -> 只有 1 种动作", d1["actions"] == 1))
    checks.append(("5 类缺口 -> 熵显著上升", d5["entropy"] > 1.0))
    checks.append(("5 类缺口 -> 动作用上多类", d5["actions"] >= 4))

    # 定律 2 —— 格式判据抓不到伪造
    r2 = experiment_judge(trials=200)
    by = {x["scenario"]: x for x in r2}
    checks.append(("无判据 -> 伪造照过",
                   by["无判据 + 无素材"]["accepted_fabricated_rate"] > 0.6))
    checks.append(("只查格式 -> 伪造仍照过",
                   by["只查格式 + 无素材"]["accepted_fabricated_rate"] > 0.6))
    checks.append(("真核验 -> 伪造被拦",
                   by["真核验 + 无素材"]["accepted_fabricated_rate"] == 0.0))
    checks.append(("★有素材 -> 伪造率归 0（连弱判据也拦住了）",
                   by["只查格式 + 有素材"]["accepted_fabricated_rate"] == 0.0))

    # 作者在有素材时不应该再伪造
    a = Author(fabricate_prob=1.0)
    ident, fab = a.write_citation(SourcePack(real_ids=["10.1021/jacs.0c0001"]))
    checks.append(("有素材时作者抄真的", fab is False and ident == "10.1021/jacs.0c0001"))
    ident, fab = a.write_citation(SourcePack())
    checks.append(("无素材时作者会编（prob=1.0）", fab is True))

    n = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print("  %s %s" % ("PASS" if ok else "FAIL", name))
    print("\n%d/%d" % (n, len(checks)))
    return 0 if n == len(checks) else 1


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 0

    print("=" * 74)
    print("定律 1：世界缺口结构决定分工（同构智能体 60 个，无任何角色预设）")
    print("=" * 74)
    div = experiment_division()
    print("%-10s %-10s %-10s %-14s %s" % ("缺口类型数", "出现的动作", "动作熵", "理论上界", "最热动作占比"))
    for r in div:
        print("%-10d %-10d %-10s %-14s %s" % (
            r["gap_kinds"], r["actions"], r["entropy"], r["theoretical_max"], r["top_action_share"]))
    print("\n⇒ 1 类缺口时动作熵为 0：智能体不是「不会分工」，是**世界没给它们可分的空间**。")

    print()
    print("=" * 74)
    print("定律 2：判据强度 = 诚实下限（同一作者模型，只改判据与素材）")
    print("=" * 74)
    jud = experiment_judge()
    print("%-22s %-18s %s" % ("场景", "伪造被接受率", "诚实被接受率"))
    for r in jud:
        print("%-22s %-18s %s" % (
            r["scenario"], r["accepted_fabricated_rate"], r["accepted_honest_rate"]))
    print()
    print("⇒ 只查格式，伪造几乎全过 —— 因为它**格式完全正确**。")
    print("⇒ 真核验能拦住伪造，但真正的解法是**把真实编号放进素材**：")
    print("   同一个弱判据下，有素材时伪造接受率直接归 0。")

    result = {"division": div, "judge": jud}
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
        print("\n结果已写入 %s" % a.json)
    print("\n（用 --json <path> 落盘结果，便于第三方比对）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
