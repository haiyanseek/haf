# Liveness Ledger · 存活凭证

海燕大模型每天一条存活记录，串成 hash 链。**这份账本的用途是让你自己检验我们是否还活着。**

## 这不是宣传

它只有一个数字意义上的主张：**我们每天都在产出，而且这件事你可以自己去算。**

## 自己核对（三步，不需要任何凭据）

```bash
curl -O https://raw.githubusercontent.com/haiyanseek/haf/main/liveness/chain.jsonl
curl -O https://raw.githubusercontent.com/haiyanseek/haf/main/liveness/verify_liveness.py
python3 -c "import json;print(json.load(open('head.json'))['head_hash'])"   # 或直接看 head.json
python3 verify_liveness.py --chain chain.jsonl --head <上面那个 hash>
```

校验器（纯标准库，无依赖）会做四件事并逐条报告：
逐条重算 hash、验证前后咬合、检查序号与日期连续、比对你手上的链头。

## 能发现什么 / 不能发现什么

**能发现**：记录被改动、中间被抽条、序号跳号或日期重复、**在你手上有链头时**尾部被删或被追加。

**不能发现**：整条链被从头重造（连所有 hash 一起重算）。

> 这正是这个 git 仓库存在的理由 —— commit 自带独立时间戳。
> 要重写历史，得同时改掉这里的历史，而那是**我们控制不了时间**的地方。

## 记录里有什么

只有聚合数字：项目数、在岗智能体、在跳动的中心、累计心跳、近 24h 产出、在线服务数。

**没有**：项目名、中心名、人名、余额、收入、token 花费。
要证明的是「系统活着并且一直在产出」，不是把内部摊开给人看。

## 链的契约

- 每天一条，**append-only**
- `hash = sha256(prev_hash + canonical_json(记录去 hash))`
- `canonical_json` = 键排序、无空白、UTF-8（`json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)`）
- 创世 `prev_hash` = 64 个 `0`
- 首条一旦对外发布，当天的记录就不再改写（写链器会拒绝）

配方全文：`canonical JSON = json.dumps(payload, sort_keys=True, separators=(',',':'), ensure_ascii=False) then .encode('utf-8'); hash = sha256( prev_hash_bytes + canonical_bytes ).hexdigest(); genesis prev_hash = 64 个 '0'`
