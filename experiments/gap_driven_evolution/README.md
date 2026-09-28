# Gap-Driven Evolution

**Two measured laws about why self-improving agent loops stall — and what actually fixes them.**

Pure Python standard library. No dependencies. Runs offline. Reproducible by anyone.

```bash
python3 gap_driven_evolution.py --run       # reproduce the results below
python3 gap_driven_evolution.py --selftest  # 18 assertions, no LLM, no network
```

---

## The two problems

Both come from operating a multi-agent system that is supposed to improve itself:

1. **A pool of agents produces almost no diversity.** You give them no roles, you give
   them a task queue, and they all converge on doing the same kind of thing.
   Is that a problem with the agents, or with the world you gave them?

2. **Making the evaluator stricter does not make the output more honest.**
   The model starts producing things that satisfy the letter of the check
   while remaining fabricated.

This package isolates both, in a form anyone can run in two seconds.

---

## Law 1 — Division of labour is bounded by the gap structure of the world

60 **identical** agents (no role prompts, no personas, no capability differences).
40 objects. The only thing that changes between rows is **how many kinds of
deficiency the world exposes** (`gap_kinds`).

| gap kinds | distinct actions used | action entropy (bit) | theoretical max | hottest action share |
|:--:|:--:|:--:|:--:|:--:|
| 1 | 1 | **0.0000** | 0.0000 | 1.0000 |
| 2 | 2 | 0.9950 | 1.0000 | 0.5417 |
| 3 | 3 | 1.5832 | 1.5850 | 0.3538 |
| 5 | 5 | 2.2889 | 2.3219 | 0.2429 |
| 8 | 8 | 2.8948 | 3.0000 | 0.2046 |

**Reading:** with one kind of gap, action entropy is exactly **0.0000** — every agent
does the same thing, and there is no room to specialise because there is nothing to
specialise *into*. Diversity grows monotonically with the number of gap kinds.

**Implication for system design:** when a swarm looks undifferentiated, the first thing
to change is **the set of deficiencies the world exposes**, not the agents.
Adding role prompts distributes *labels*; adding gap kinds distributes *work*.

Pitfall worth noting: the agent's tie-break rule in this demo is a stable per-agent
preference hash. That is deliberately the *cheapest possible* mechanism — it shows the
diversity ceiling is set by the world, not by agent sophistication.

---

## Law 2 — Judge strength sets the honesty floor, but *having something to copy* is what closes it

400 trials per scenario. Same author model throughout (a behaviourally configurable
stand-in, **not** any real model). Only two things change: the judge, and whether the
author was handed a source pack containing real identifiers.

| scenario | fabricated **accepted** rate | honest accepted rate |
|:--|:--:|:--:|
| no judge, no sources | 0.8125 | 0.1875 |
| **format-only judge**, no sources | **0.8125** | 0.0000 |
| real verification, no sources | 0.0000 | 0.0000 |
| **format-only judge, with sources** | **0.0000** | 1.0000 |
| real verification, with sources | 0.0000 | 1.0000 |

**Two readings, and the second one is the point:**

1. **A format-only judge is exactly as useful as no judge at all** — `0.8125` versus
   `0.8125`, identical. Fabricated identifiers pass because they are *format-correct*.
   Checking the shape of an answer is not checking the answer.

2. **The thing that drives fabrication to zero is not a stricter rule — it is giving
   the model something real to copy.** Under the *same weak judge*, handing over a source
   pack takes the fabricated-acceptance rate from `0.8125` to `0.0000`.

**Implication:** "do not fabricate" is a constraint the model can satisfy
*without being correct*. Putting real identifiers into the material converts an
unenforceable instruction into a lookup. In our experience this is worth roughly an
order of magnitude more than any amount of prompt-hardening or judge-tightening.

> A third finding worth internalising: when we first ran this, one scenario produced
> `0.8275` versus another's `0.8` — pure sampling noise presented as an ordering, which
> buried the result that actually mattered. The trial seed is now fixed per round so the
> scenarios are compared on **identical random decisions**. If a sweep shows a tidy
> ordering, check whether you are reading signal or noise.

---

## What this is, and what it is not

**Is:** an executable, deterministic demonstration of two mechanisms, with assertions
that fail if either mechanism stops holding (`--selftest`, 18/18).

**Is not:**

- Not an LLM benchmark. The "author" and "judge" here are simulations of behaviour
  classes, chosen so the experiment is offline, instant, and dependency-free.
- Not a claim to reproduce any published system's numbers.
- Not a general theory. Two laws, measured under stated conditions — nothing more.

If you want the honest version of a result, publish the script, the seed, the raw log,
and the environment. Everything in this directory is designed to be that.

---

## Files

| file | purpose |
|:--|:--|
| `gap_driven_evolution.py` | the whole experiment: world, agents, author, judges, metrics |
| `results/baseline.json` | raw numbers from the run quoted above |

## License

Apache License 2.0 — see the repository `LICENSE`.

---

## 中文要点

两个在跑多智能体自进化系统时反复踩到的工程问题，各自用一个可复现实验给出答案：

**定律 1 — 分工空间由世界的缺口结构决定。**
60 个**完全同构**、没有任何角色预设的智能体，只改变世界暴露的缺口**类型数**：
1 类缺口时动作熵恰好 **0.0000**（所有人挤在同一个动作上），缺口类型增加则熵单调上升。
⇒ 智能体看起来不会分工时，先改**世界提供多少种缺口**，而不是去给它们加角色。
加角色分配的是**标签**，加缺口类型分配的是**工作**。

**定律 2 — 判据强度决定诚实下限，但把伪造率压到 0 的是「有得抄」。**
同一作者模型，400 次试验：

- **只查格式的判据，和没有判据完全一样** —— `0.8125` 对 `0.8125`，一模一样。
  伪造的编号**格式完全正确**，所以能过。检查答案的形状不等于检查答案。
- **同一个弱判据下，把真实编号放进素材，伪造接受率直接归 0**（`0.8125 → 0.0000`）。

⇒「不许编造」是一条模型可以**在不正确的情况下也满足**的约束；
把真实编号放进素材，才把一条无法执行的指令变成一次查询。

**诚实边界**：本包用确定性模拟演示机制，不是 LLM 实测；作者与判据是行为可配置的替身，
不是任何真实模型；不声称重现任何外部系统的成绩。
