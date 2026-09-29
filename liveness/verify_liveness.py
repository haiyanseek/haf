#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存活链校验器 —— **给外人用的**，不是给我们用的。

这个文件的设计目标只有一条：一个陌生人拿到「链文件 + 这个脚本」，
不需要我们的任何凭据、不需要联网、不需要装任何库（纯标准库），
就能自己算一遍，自己判断我们有没有改过历史。

用法：
  python3 verify_liveness.py --chain chain.jsonl
  python3 verify_liveness.py --chain https://raw.githubusercontent.com/.../chain.jsonl
  python3 verify_liveness.py --chain chain.jsonl --head <公布的链头hash>

校验四件事，各自能抓什么 / 抓不到什么（写明白，不吹）：
  ① 逐条重算 hash         → 抓「某条记录被改动」
  ② prev_hash 链接一致    → 抓「中间抽掉/插入记录」
  ③ seq 与日期连续        → 抓「跳号」与「漏天」
  ④ 链头比对外部公布值    → 抓「删掉最后几条」（没给 --head 就判不了，会明说）

★ 本脚本**抓不到**的：如果整条链被从头重造（含重算所有 hash），
  本地文件层面无从分辨 —— 那要靠链头锚在我们控制不了的地方（如 git 提交）。
  这是实话，不是漏洞说明。
"""
import argparse
import hashlib
import json
import sys
import urllib.request

GENESIS = "0" * 64
RECIPE = ("canonical = json.dumps(payload_without_hash, sort_keys=True, "
          "separators=(',',':'), ensure_ascii=False).encode('utf-8'); "
          "hash = sha256(prev_hash.encode('ascii') + canonical).hexdigest()")


def canon(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def expected_hash(rec):
    """按公布的配方重算 —— 与前缀无关，纯看内容"""
    body = {k: v for k, v in rec.items() if k != "hash"}
    prev = body.get("prev_hash", GENESIS)
    return hashlib.sha256(prev.encode("ascii") + canon(body)).hexdigest()


def load(src):
    if src.startswith("http://") or src.startswith("https://"):
        with urllib.request.urlopen(src, timeout=30) as r:
            text = r.read().decode("utf-8")
    else:
        with open(src, encoding="utf-8") as f:
            text = f.read()
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception as e:
            print("  ✗ 第 %d 行不是合法 JSON：%s" % (i, e))
            sys.exit(2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", required=True, help="链文件路径或 URL")
    ap.add_argument("--head", help="外部公布的链头 hash（抓删尾用）")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    print("=" * 70)
    print("存活链校验（第三方可独立复跑 · 纯标准库 · 无需凭据）")
    print("=" * 70)
    print("  链来源 : %s" % a.chain)
    print("  配方   : %s" % RECIPE)
    print("")

    chain = load(a.chain)
    if not chain:
        print("  ✗ 链是空的")
        return 2
    print("  记录数 : %d  ｜  %s → %s" % (len(chain), chain[0].get("day"), chain[-1].get("day")))
    print("")

    ok = True

    # ── ① 逐条重算 ──
    bad = []
    for r in chain:
        if expected_hash(r) != r.get("hash"):
            bad.append(r.get("seq"))
    if bad:
        ok = False
        print("  [1/4] 逐条重算 hash ........ ✗ 第 %s 条内容与自身 hash 不符（被改过）" %
              ", ".join(str(x) for x in bad))
    else:
        print("  [1/4] 逐条重算 hash ........ ✓ %d 条全部自洽" % len(chain))

    # ── ② 链接 ──
    brk = []
    for i in range(1, len(chain)):
        if chain[i].get("prev_hash") != chain[i - 1].get("hash"):
            brk.append(chain[i].get("seq"))
    if chain[0].get("prev_hash") != GENESIS:
        brk.insert(0, chain[0].get("seq"))
    if brk:
        ok = False
        print("  [2/4] 前后链接 prev_hash ... ✗ 第 %s 条断链（中间被抽掉或插入）" %
              ", ".join(str(x) for x in brk))
    else:
        print("  [2/4] 前后链接 prev_hash ... ✓ 首条指向创世块，其余逐条咬合")

    # ── ③ 序号与日期连续 ──
    seqs = [r.get("seq") for r in chain]
    want = list(range(1, len(chain) + 1))
    gaps = []
    dates = [r.get("day") for r in chain]
    dup = [d for d in set(dates) if dates.count(d) > 1]
    if seqs != want:
        ok = False
        gaps.append("seq 期望 1..%d，实得 %s" % (len(chain), seqs))
    if dup:
        ok = False
        gaps.append("日期重复 %s" % sorted(dup))
    if gaps:
        print("  [3/4] 序号与日期连续 ...... ✗ %s" % "；".join(gaps))
    else:
        print("  [3/4] 序号与日期连续 ...... ✓ 1..%d 无跳号、无重复日" % len(chain))

    # ── ③b 日期缺口：**如实呈现，不算篡改** ──
    #  机器关着就没记录，这是事实信息，不是被改过的证据；
    #  把它和「hash 不符」混成同一等级，会让日报天天误报（机器一休眠就报"链失效"）。
    miss = []
    try:
        from datetime import date, timedelta
        ds = sorted(date.fromisoformat(d) for d in dates)
        for i in range(1, len(ds)):
            d = ds[i - 1] + timedelta(days=1)
            while d < ds[i]:
                miss.append(d.isoformat())
                d += timedelta(days=1)
    except Exception:
        pass
    if miss:
        print("  附注: 有 %d 天没有记录（机器关着就会这样，属事实不属篡改）：%s"
              % (len(miss), ", ".join(miss[:6]) + ("…" if len(miss) > 6 else "")))
    else:
        print("  附注: 逐日无缺（每条记录之间的日期是连着的）")

    # ── ④ 链头锚定 ──
    head = chain[-1].get("hash")
    if a.head:
        if a.head.strip() == head:
            print("  [4/4] 链头比对公布值 ...... ✓ 一致（末条未被删）")
        else:
            ok = False
            print("  [4/4] 链头比对公布值 ...... ✗ 不符")
            print("        公布值 %s" % a.head.strip())
            print("        实算值 %s" % head)
            print("        → 要么链被截断/追加，要么提供的是另一条链")
    else:
        print("  [4/4] 链头锚定 ............ ⚠ 未提供 --head，**删尾无法判断**（不是通过）")
        print("        当前链头 %s" % head)
        print("        请拿外部公布的链头（如 git 提交里的记录）比对")

    print("")
    print("-" * 70)
    print("  链头 hash : %s" % head)
    if ok:
        print("  结论      : ✅ 链完整 —— 内容自洽、链接咬合、序号连续")
    else:
        print("  结论      : ❌ 链已失效 —— 见上面标 ✗ 的项")
    print("  ⚠ 边界    : 本校验能发现「改动/抽条/跳号/删尾(给了head时)」；")
    print("             不能发现「整条链被从头重造」—— 那要靠外部时间锚。")
    print("-" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
