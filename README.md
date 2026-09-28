# HAF — Haiyan Agent Framework

**Filesystem-first multi-agent infrastructure, and the experiments we run on it.**

> HaiyanSeek · 海燕探索（北京）科技有限公司

---

## What is actually in this repository

This repository is deliberately small. It contains **runnable work**, not a brochure.

| path | what it is |
|:--|:--|
| [`experiments/gap_driven_evolution/`](experiments/gap_driven_evolution/) | Two measured laws about why self-improving agent loops stall — with a reproducible, dependency-free experiment and 18 assertions |

That is the current contents. Nothing else here is claimed to exist.

## Why the repository is thin

We ran the opposite experiment first: a repository that *described* a large framework
(filesystem state layer, agent roles, memory, safety layer, tool system) while shipping
no code. It had zero stars and no commits for eight weeks. A README that describes
architecture you have not published is not a placeholder — it is a liability, because
the first thing a visitor does is check.

So this repository now publishes **one thing that runs**, with its numbers, its seed,
and its caveats. It will grow when the next thing runs.

## The experiment

**[Gap-Driven Evolution](experiments/gap_driven_evolution/)** — 60 identical agents, no
role prompts, one variable:

- **Law 1 — the gap structure of the world bounds the division of labour.**
  One kind of deficient item → action entropy **0.0000**. More kinds → entropy rises
  monotonically toward `log2(k)`. When a swarm looks undifferentiated, the thing to
  change is what the *world* exposes, not the agents' prompts.

- **Law 2 — judge strength sets the honesty floor; having something to copy is what
  closes it.** A format-only judge performed **identically to no judge at all**
  (0.8125 vs 0.8125). Handing the model a source pack containing real identifiers drove
  the fabricated-acceptance rate to **0.0000 — under the same weak judge**.

```bash
cd experiments/gap_driven_evolution
python3 gap_driven_evolution.py --selftest   # 18 assertions, offline
python3 gap_driven_evolution.py --run        # reproduce the published numbers
```

## Principles we hold to

1. **Publish the script, the seed, the raw log, the environment** — or do not publish the number.
2. **A passing run is not a correct run.** Reported status distinguishes "exited zero"
   from "assertions held".
3. **Failures stay in the output.** Published results keep the failures visible rather
   than reporting only the passing subset.
4. **Say what is not there.** Every artifact states its own boundaries.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## 中文说明

本仓刻意保持很小：**只放能跑的东西，不放宣传册。**

当前内容：一个实验包 —— [缺口驱动的自进化](experiments/gap_driven_evolution/)，
用 60 个**完全同构、无任何角色预设**的智能体，测出两条定律：

1. **分工空间由世界的缺口结构决定** —— 1 类缺口时动作熵恰好 0.0000；
   想让智能体分化，先改**世界提供多少种缺口**，而不是给它们加角色。
2. **判据强度决定诚实下限，但把伪造率压到 0 的是「有得抄」** ——
   只查格式的判据与**没有判据**表现完全一致（0.8125 对 0.8125）；
   同一个弱判据下把真实编号放进素材，伪造接受率直接归 0。

**为什么这个仓这么小**：我们先前做过相反的事 —— 一个 README 描述了完整的框架架构，
却没有一行代码。结果是 0 星、八周零提交。**描述你并未发布的架构不是占位符，是负债。**

所以本仓现在只发布**一件能跑的事**，连同它的数字、随机种子和边界。
下一件能跑的事出现时，它会变大。
