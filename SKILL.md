---
name: scan-ai-radar
description: Use when the user says "AI趋势雷达", "抓AI热点到Obsidian", "scan-ai-radar", "多平台AI趋势", or wants to fetch AI trend signals from X/Twitter, YouTube, Reddit, Hacker News and similar communities, then store an enterprise AI adoption radar note into Obsidian.
---

# Scan-AI-Radar — 企业 AI Adoption 雷达与 Obsidian 入库

> 面向大型汽车企业研发中心的 AI Adoption Lead。目标是持续捕捉会影响企业 AI 采用策略、研发效率、工具选型、治理方式、组织能力和未来机会判断的关键信号。

---

## 核心规则

**跨平台抓取 AI 趋势信号，按企业 AI Adoption 价值筛选、去重、归因和判断，并写入 Obsidian Markdown 笔记。**

输出必须同时满足 4 件事：

- 有出处：每条趋势都要有原始链接
- 有企业价值：说明这条趋势对大型汽车企业研发中心可能有什么影响
- 有行动判断：说明是否值得评估、试点、战略跟踪或低频观察
- 有沉淀：最终写入 Obsidian，而不是只停留在聊天回复里

默认视角：

- 用户角色是大型汽车企业研发中心的 AI Adoption Lead
- 优先关注研发中心、软件定义汽车、工程效率、研发知识管理、测试验证、仿真、数据治理、安全合规、组织采用和 AI 平台能力
- 不把“AI 圈热闹”当作充分理由；必须能映射到企业采用判断或未来潜在机会

---

## 信息组合与权重

每日 Top Trends 应尽量按以下组合组织：

| 类别 | 目标占比 | 关注重点 |
|------|----------|----------|
| `基础研究` | 20% | 新模型、新论文、新 benchmark、新能力边界、推理、多模态、agent、robotics、world model、evals |
| `企业应用` | 50% | 企业 AI 落地方法、工具链、治理、ROI、案例、组织模式、安全合规、研发提效、平台化采用 |
| `创业前沿` | 30% | AI-native 产品、新交互、新业务模式、垂直 agent、未来可能迁移到企业的前沿应用 |

比例不是机械配额，但最终笔记必须避免被单一模型发布、单一创业 demo 或单一平台情绪刷屏。

Top Trends 建议保留 6-10 条：

- `基础研究`：1-2 条
- `企业应用`：3-5 条
- `创业前沿`：2-3 条

如果某类当天没有足够高质量信号，需要在对应小节说明原因，不要凑数。

---

## 第一步：确认 Obsidian 落点

优先使用 Obsidian CLI。

只有在用户明确允许时，才可以退回到底层文件写入；默认不要直接写 Vault 文件。

### 默认目录约定

写入 `personal` Vault 的目录（如果没有就创建）：

```text
AI Trend Radar/
```

每日汇总：

```text
AI Trend Radar/YYYY-MM-DD 企业AI Adoption雷达.md
```

需要单独拆成原子笔记时：

```text
AI Trend Radar/Clips/YYYY-MM-DD {趋势关键词}.md
```

### Vault 选择规则

- 不要假设“最近打开的 Vault”就是目标 Vault，优先显式指定：`vault="personal"`
- 先用 `obsidian vaults` 和 `obsidian vault="personal" vault info=path` 确认目标 Vault 名称与实际路径
- 如果当前机器上存在多个 Vault，禁止在未确认目标 Vault 的情况下写入

### CLI 执行规则

- 优先使用 `obsidian` CLI，而不是手写 Vault 路径
- 如果 `obsidian help` / `obsidian vaults` 在当前执行环境报 `unable to find Obsidian`，先判断是否为沙箱/GUI IPC 隔离问题
- 若沙箱内失败、非沙箱可用，应切换到非沙箱执行 `obsidian` CLI，而不是直接改用文件系统写入
- 写入前先验证 CLI 连通性，至少检查一次：

```bash
obsidian help
obsidian vault="personal" vault info=path
```

### 写入前检查

- 读取近 14 天的 `AI Trend Radar/` 笔记，避免重复归档同一趋势
- 如已存在相同事件或相同链接，更新原笔记或在今天笔记里标注“延续信号”，不要重复当成新趋势
- 优先用 `obsidian vault="personal" search ...` 检查是否已存在目标笔记、同主题笔记或同一主链接

---

## 第二步：按平台抓取

默认按以下顺序抓取，优先找原始发布、企业实践、真实反馈和工程讨论，而不是媒体二次转述：

1. `X / Twitter`
2. `YouTube`
3. `Reddit`
4. `Hacker News`
5. `官方博客 / 研究论文 / 企业案例`（当平台信号不足或需要确认时补充）

如果用户指定了特定平台或关键词，优先满足用户需求，但仍要遵守去重、企业价值和行动判断原则。

### X-first 执行门槛

默认任务必须把 X 当作主信号源之一，而不是可选补充源。

X 抓取是强制步骤。只要 X 的连通性、登录态、页面读取或风控出现技术问题，就立刻停止后续平台抓取，先修复 X；如果当次无法修复，直接通知用户当前阻塞原因，不要改用其他平台替代 X 主信号源。

如果在获取 X 时发现 CDP 失败，必须先进入排查流程，检查端口、Chrome 进程、启动参数和 profile 状态；如果排查后仍无法修复本次 CDP 链路，则此次 skill 执行必须中断，不得继续用其他平台替代 X 主信号源。

在进入 YouTube / Reddit / Hacker News 前，必须先完成一轮 X 抓取审计：

1. 读取 `references/x.md`
2. 验证 Chrome CDP 是否可用；优先探测 `9223`，再探测 `9222`，使用第一个返回标准 CDP JSON 且能看到 X target 的端口
3. 运行至少 4 组 X 搜索 URL：基础研究、企业应用、汽车研发/工业、创业前沿
4. 扫描至少 12 个账号，必须覆盖模型/研究、企业平台、汽车/工业、创业前沿四类账号
5. 从 X 候选里保留 6-12 条可复核信号，除非 X 抓取链路明确失败

### 抓取脚本：scripts/cdp.py（默认抓取方式）

X 抓取统一用本 skill 自带的 `scripts/cdp.py`，不要每次临时手写 CDP 代码。它解决了 X 时间线的虚拟滚动问题：边滚动边增量采集并按 `/status/` 链接去重，因此不会因为旧推文被卸载出 DOM 而丢内容；同时返回每条推文的 `datetime`，便于按近 7 天窗口过滤。

首次在新环境执行前，先做一次依赖自检。`cdp.py` 依赖 `websockets`；如果当前系统 Python 没装它，不要在失败后继续空跑搜索组或账号扫描，先补依赖再抓。

推荐做法：

```bash
cd .agents/skills/scan-ai-radar/scripts
python3 -m venv /tmp/scan-ai-radar-venv
/tmp/scan-ai-radar-venv/bin/pip install -r requirements.txt
```

```bash
# 必须先绕过代理，再调用本机 CDP
export no_proxy='*' NO_PROXY='*'
cd .agents/skills/scan-ai-radar/scripts

# 搜索：抓近窗信号时用 f=live（按时间倒序），不要只用 f=top（旧热帖会压住新帖）
/tmp/scan-ai-radar-venv/bin/python cdp.py "https://x.com/search?q=...&f=live" --port 9223 --scrolls 10 --json

# 账号时间线
/tmp/scan-ai-radar-venv/bin/python cdp.py "https://x.com/OpenAI" --port 9223 --scrolls 8 --json
```

使用要点：

- 端口先按 `references/x.md` 探测 `9223` → `9222`，把通过的端口传给 `--port`
- 搜索抓近窗用 `f=live`；需要看高热度共识再补一轮 `f=top`
- **新鲜度默认开启且关键**：脚本默认先开空白页 → `Network.setCacheDisabled` → 导航 → `Page.reload(ignoreCache)` 再采集。这是为了绕开 CDP / X 的强缓存——否则个人主页时间线会返回几天甚至几周前的旧帖，导致漏掉刚发生的大事件。除非明确要省时间，否则不要加 `--no-fresh`
- 校验新鲜度：用返回的 `items[].ts` 看是否有近 1-2 天的帖子；如果一个活跃官方账号（如 @AnthropicAI、@OpenAI）最新帖还停在一周前，说明拿到的是缓存，必须重抓而不是下结论
- `--scrolls` 控制翻页深度（默认 12），噪声多时配合更高 `min_faves`，而不是无限加深
- 输出 JSON 字段：`loggedOut`、`count`、`items[].url/ts/text`；用 `ts`（UTC datetime）做近 7 天过滤，不要只信页面上的相对时间
- 如果 `loggedOut` 为 true 或 `count` 异常偏低，按 `references/x.md` 的失败流程排查，不要假装“X 没有热点”
- 如果输出文件是空的、命令秒退，或看到 `ModuleNotFoundError: No module named 'websockets'`，先安装 `scripts/requirements.txt` 里的依赖；不要把“脚本没跑起来”误判成“X 没信号”

只有满足以下任一条件，才允许把 Hacker News、官方博客或其他平台作为主依据：

- Chrome CDP 不可用，且已经记录具体失败原因
- X 未登录、搜索页无法打开、页面被风控或无法读取正文
- 四组搜索和账号扫描都完成，但没有满足保留标准的近 7 天信号

如果 X 抓取失败，笔记的 `### X` 小节必须写清楚失败发生在哪一步，而不是只写“没有高置信信号”。例如：

```text
### X
- X 抓取失败：Chrome CDP endpoint `/json/version` 返回 404，无法枚举已登录 Chrome 页面。
- 已检查：`localhost` 访问已绕过代理；已依次探测 `localhost:9223`、`localhost:9222`；监听端口返回非标准结果，或没有可用的 X target。
- 本次不把 X 作为主依据，后续需要重新以 `--remote-debugging-port=9223` 启动 Chrome-CDP profile，或修复当前可用 CDP 端口。
```

默认建议用非默认的 `Chrome-CDP` 数据目录启动 Chrome；它应由原始 `Chrome` profile 复制得到，不能直接用默认 `Chrome` 目录开启远程调试。

禁止在未完成 X 抓取审计前，用 WebSearch、HN front page 或媒体文章替代 X 作为主信号源。

各平台的具体抓取方法、搜索组、保留标准和字段要求，分别读取以下参考文件：

- [references/x.md](./references/x.md)
- [references/youtube.md](./references/youtube.md)
- [references/reddit.md](./references/reddit.md)
- [references/hackernews.md](./references/hackernews.md)
- [references/official-research.md](./references/official-research.md)

只读取当前实际会用到的平台文件，不要一次性把所有参考内容都展开进上下文。

---

## 第三步：统一筛选规则

### 硬性过滤

- 去重：相同 URL 或明显是同一事件的多平台重复报道，只保留“原始信号最强”的一条，其余做补充来源
- 去旧：默认只保留近 7 天内容；重大趋势可放宽到 14 天，但必须标注
- 去水：纯情绪表达、无信息增量、无链接来源的内容丢弃
- 去转述：优先保留原作者、原演示、原讨论串、官方案例、论文或一手企业实践，而不是二手搬运
- 去泛化：无法映射到企业 AI adoption、汽车研发中心影响或未来机会判断的内容丢弃

### 趋势判断标准

保留的趋势至少满足以下之一：

- 可能影响企业 AI 工具选型或平台架构
- 可能改变 AI adoption roadmap、治理模型或组织能力建设
- 能提供可借鉴的企业落地案例、方法论、指标或失败经验
- 暴露安全、合规、成本、数据治理、供应商锁定、模型风险或组织风险
- 对汽车研发、SDV、测试验证、仿真、需求工程、工程知识管理、嵌入式软件或制造工程有潜在影响
- 虽不适合马上进入企业，但代表新型 AI-native 工作流、产品形态或创业方向
- 基础研究显著改变模型能力边界、评估方式、推理/多模态/agent 能力或工程可用性

### 影响等级

| 等级 | 含义 | 判断信号 |
|------|------|----------|
| `S` | 立即评估 | 多平台同时爆发，或直接影响企业 AI strategy / tooling / governance / automotive R&D |
| `A` | 值得试点或深入调研 | 单平台高质量信号，且能映射到明确企业场景或能力建设 |
| `B` | 战略跟踪 | 信号有潜力，但企业采用路径、成熟度或合规性仍不清晰 |
| `C` | 低频观察 | 暂不深入，只记录弱信号或远期机会 |

### 采用阶段

| 阶段 | 使用场景 |
|------|----------|
| `立即评估` | 可能影响当前路线、预算、工具选型、治理要求或试点计划 |
| `试点观察` | 有明确企业场景，可设计小范围 PoC 或用户访谈 |
| `战略跟踪` | 中长期重要，但短期还缺成熟产品、案例或合规路径 |
| `低频观察` | 早期、噪声高、企业适配度不明 |

### 分类标注

| 类别 | 说明 |
|------|------|
| `基础研究` | 新模型、新论文、新 benchmark、新能力边界、评估、安全、robotics/world model 等 |
| `企业应用` | 企业 adoption、平台、治理、ROI、案例、工具链、组织模式、研发提效 |
| `创业前沿` | AI-native 产品、agent startup、新交互、垂直工具、未来可能迁移到企业的应用 |
| `风险信号` | 可叠加标签，用于成本、安全、合规、供应商锁定、组织反弹、幻觉等风险 |

---

## 第四步：写入 Obsidian 的笔记结构

每日汇总笔记必须使用以下结构：

```markdown
---
date: 2026-06-04
type: enterprise-ai-adoption-radar
role: AI Adoption Lead
tags:
  - AI
  - TrendRadar
  - EnterpriseAI
  - AutomotiveR&D
sources:
  - X
  - YouTube
  - Reddit
  - HackerNews
  - Official
---

# 2026-06-04 企业AI Adoption雷达

## Executive Takeaways

- 用 3-5 条话写给大型汽车企业研发中心 AI Adoption Lead 的判断

## Portfolio View

| 类别 | 目标占比 | 今日占比 | 最重要信号 | 建议动作 |
|------|----------|----------|------------|----------|
| 基础研究 | 20% | ... | ... | ... |
| 企业应用 | 50% | ... | ... | ... |
| 创业前沿 | 30% | ... | ... | ... |

## Top Trends

| # | 趋势 | 类别 | 影响等级 | 采用阶段 | 对研发中心的意义 | 建议动作 | 主链接 |
|---|------|------|----------|----------|------------------|----------|--------|
| 1 | ... | 企业应用 | S | 立即评估 | ... | ... | https://... |

## 对汽车研发中心的影响

### 研发效率
- ...

### 软件工程 / SDV
- ...

### 知识管理 / 工程文档
- ...

### 测试验证 / 仿真
- ...

### 数据治理 / 安全合规
- ...

### 组织与人才
- ...

## 分平台信号

### X
- ...

### YouTube
- ...

### Reddit
- ...

### Hacker News
- ...

### Official / Research
- ...

## 跟进清单

- 需要继续观察的公司、产品、作者、论文、案例或讨论串
- 值得加入日后监控关键词的主题
- 值得形成 PoC、内部分享或供应商调研的问题

## 观察池

- 暂时不深入，但建议继续追踪的弱信号
```

### 写作要求

- `Executive Takeaways` 先写判断，再写事实
- `Top Trends` 至少保留 6 条，最多 10 条；除非平台抓取失败或当天信号不足
- 每条趋势至少带 1 个主链接；有补充来源可追加 1-2 个
- `对汽车研发中心的影响` 必须落到研发中心语境，不要停留在泛 AI 总结
- `建议动作` 必须可执行，例如：`内部分享`、`小范围 PoC`、`供应商调研`、`加入监控`、`暂不跟进`
- `跟进清单` 只记录对后续企业 adoption 判断真正有价值的项目

---

## 第五步：企业 Adoption 提炼规则

每条趋势补充以下判断：

- **一句话判断**：这件事为什么会影响企业 AI adoption 或汽车研发中心
- **企业影响**：影响工具选型、研发效率、治理、成本、组织、数据或安全的哪一部分
- **采用门槛**：数据、权限、集成、安全、预算、人才、流程或供应商依赖
- **风险关注**：合规、信息泄露、幻觉、成本、供应商锁定、组织阻力、评估缺失
- **建议动作**：立即评估、试点观察、战略跟踪、低频观察
- **跟进窗口**：`今天`, `3天内`, `1周内`, `本月`, `低频观察`

优先保留这三类信号：

1. 能改变企业 AI adoption roadmap、治理策略或平台架构判断的信号
2. 能暴露企业真实采用反馈、失败原因、ROI 或组织阻力的信号
3. 能帮助更新汽车研发中心的 AI 场景地图、供应商监控名单或 PoC backlog 的信号

---

## 红线

- **禁止** 未确认 Vault 名称就写入 Obsidian
- **禁止** 在 `obsidian` CLI 仅因沙箱不可连通时，直接绕过到 Vault 文件系统写入
- **禁止** 编造播放量、点赞数、评论数、分数、企业客户或案例
- **禁止** 只有平台名，没有原始链接
- **禁止** 把同一事件拆成多条伪趋势灌水
- **禁止** 只做摘要，不写企业影响和建议动作
- **禁止** 写入 Obsidian 前不检查近 14 天是否已归档
- **禁止** 把明显与 AI adoption、企业应用、基础研究或创业前沿无关的科技热点混入
- **禁止** 默认把趋势转成文章选题，除非用户明确要求
- **禁止** 用 WebSearch 替代已登录的 CDP 抓取，除非用户明确要求
- **禁止** 只追模型发布，忽略企业采用、治理和组织落地信号

---

## 相关技能协同

- 需要操作 Obsidian 时，优先配合 `obsidian-cli` 或 `obsidian-markdown`
- 用 CDP 控制已登录的 Chrome，抓取各平台的原始讨论和真实反馈；统一通过 `scripts/cdp.py` 调用，不要临时手写 CDP 逻辑

### 推荐 Obsidian CLI 用法

```bash
obsidian vault="personal" search query="2026-06-04 企业AI Adoption雷达" format=json
obsidian vault="personal" files folder="AI Trend Radar"
obsidian vault="personal" create path="AI Trend Radar/2026-06-04 企业AI Adoption雷达.md" content="..."
obsidian vault="personal" read path="AI Trend Radar/2026-06-04 企业AI Adoption雷达.md"
```

---

## 触发示例

- “抓今天的 AI 趋势，写进 Obsidian”
- “做一份企业 AI Adoption 雷达”
- “看看 X、YouTube、Reddit、HN 最近哪些 AI 事件会影响企业采用”
- “把 AI 趋势信号存成我的 Obsidian adoption 笔记”
