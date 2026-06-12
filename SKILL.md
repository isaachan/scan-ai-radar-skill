---
name: scan-ai-radar
description: Use when the user says "AI趋势雷达", "抓AI热点到Obsidian", "scan-ai-radar", "多平台AI趋势", or wants to fetch AI trend signals from X/Twitter, YouTube, Reddit, Hacker News and similar communities, then store the results into Obsidian notes for personal learning and trend tracking.
---

# Scan-AI-Radar — 多平台 AI 趋势雷达与 Obsidian 入库

> 面向个人使用。目标是持续学习、跟进和沉淀 AI 趋势。

---

## 核心规则

**跨平台抓取 AI 趋势信号，做去重与归因，提炼成学习价值明确的判断，并写入 Obsidian Markdown 笔记。**

输出必须同时满足 3 件事：

- 有出处：每条趋势都要有原始链接
- 有学习价值：说明这条趋势让我学到什么、该跟进什么
- 有沉淀：最终写入 Obsidian，而不是只停留在聊天回复里

---

## 第一步：确认 Obsidian 落点

优先使用 Obsidian CLI。

只有在用户明确允许时，才可以退回到底层文件写入；默认不要直接写 Vault 文件。

### 默认目录约定

写入 `personal` Vault 的目录 (如果没有就创建)：

```text
AI Trend Radar/
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

### 文件命名

每日汇总：

```text
AI Trend Radar/YYYY-MM-DD AI趋势雷达.md
```

需要单独拆成原子笔记时：

```text
AI Trend Radar/Clips/YYYY-MM-DD {趋势关键词}.md
```

### 写入前检查

- 读取近 14 天的 `AI Trend Radar/` 笔记，避免重复归档同一趋势
- 如已存在相同事件或相同链接，更新原笔记，不重复新建
- 优先用 `obsidian vault="personal" search ...` 检查是否已存在目标笔记或同主题笔记

---

## 第二步：按平台抓取

默认按以下顺序抓取，优先找原始讨论和真实反馈，而不是媒体二次转述：

1. `X / Twitter`
2. `YouTube`
3. `Reddit`
4. `Hacker News`
5. 其他平台仅在前四个平台信号不足时补充

如果用户指定了特定平台或关键词，优先满足用户需求，但仍要遵守去重和学习价值原则。

### X-first 执行门槛

默认任务必须把 X 当作主信号源，而不是可选补充源。

X 抓取是强制步骤。只要 X 的连通性、登录态、页面读取或风控出现技术问题，就立刻停止后续平台抓取，先修复 X；如果当次无法修复，直接通知用户当前阻塞原因，不要改用其他平台替代主信号源。

在进入 YouTube / Reddit / Hacker News 前，必须先完成一轮 X 抓取审计：

1. 读取 `references/x.md`
2. 验证 Chrome CDP 是否可用；优先探测 `9223`，再探测 `9222`，使用第一个返回标准 CDP JSON 且能看到 X target 的端口
3. 运行至少 3 组 X 搜索 URL
4. 扫描至少 8 个 KOL / 官方账号
5. 从 X 候选里保留 3-8 条可复核信号，除非 X 抓取链路明确失败

只有满足以下任一条件，才允许把 Hacker News 或其他平台作为主依据：

- Chrome CDP 不可用，且已经记录具体失败原因
- X 未登录、搜索页无法打开、页面被风控或无法读取正文
- 三组搜索和 KOL 扫描都完成，但没有满足保留标准的近 7 天信号

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

只读取当前实际会用到的平台文件，不要一次性把所有参考内容都展开进上下文。

---

## 第三步：统一筛选规则

### 硬性过滤

- 去重：相同 URL 或明显是同一事件的多平台重复报道，只保留“原始信号最强”的一条，其余做补充来源
- 去旧：默认只保留近 7 天内容；重大趋势可放宽到 14 天，但必须标注
- 去水：纯情绪表达、无信息增量、无链接来源的内容丢弃
- 去转述：优先保留原作者、原演示、原讨论串，而不是二手搬运

### 趋势判断标准

保留的趋势至少满足以下之一：

- 新模型 / 新功能发布
- 新工具 / 新产品突然爆火
- 某类工作流被集中讨论
- 某个 AI 应用场景出现明确迁移
- 某项争议、失败案例、限制条件被反复提及

### 热度分级

| 等级 | 含义 | 判断信号 |
|------|------|----------|
| `S` | 立即跟进 | 多平台同时爆发，或单平台极高热度且有明确事件 |
| `A` | 值得跟进 | 单平台高热，且能提炼出清晰学习点 |
| `B` | 值得收藏 | 信号有意思，但还未形成广泛讨论 |
| `C` | 观察池 | 暂不深入，只记录待观察 |

### 学习类型标注

| 类型 | 说明 |
|------|------|
| `模型动向` | 新模型、新能力、新 benchmark、新限制 |
| `产品动向` | 新工具、新产品策略、新交互方式 |
| `工作流变化` | 某类做法开始普及、替代或失效 |
| `社区情绪` | 用户态度明显转向，如吹捧、失望、替代潮 |
| `风险信号` | 失败案例、限制条件、成本问题、合规风险 |

---

## 第四步：写入 Obsidian 的笔记结构

每日汇总笔记必须使用以下结构：

```markdown
---
date: 2026-06-04
type: ai-trend-radar
tags:
  - AI
  - TrendRadar
sources:
  - X
  - YouTube
  - Reddit
  - HackerNews
---

# 2026-06-04 AI趋势雷达

## 今日学习重点

- 用 3-5 条话总结今天最值得理解的趋势

## Top Trends

| # | 趋势 | 类型 | 热度 | 平台 | 我该关注什么 | 主链接 |
|---|------|------|------|------|--------------|--------|
| 1 | ...  | 产品动向 | S | X / YouTube | ... | https://... |

## 分平台信号

### X
- ...

### YouTube
- ...

### Reddit
- ...

### Hacker News
- ...

## 跟进清单

- 需要继续观察的公司、产品、作者或讨论串
- 值得加入日后监控关键词的主题
- 需要补看的视频、帖子、评论区

## 观察池

- 暂时不深入，但建议继续追踪的弱信号
```

### 写作要求

- `今日学习重点` 先写判断，再写事实
- `Top Trends` 至少保留 3 条，最多 10 条
- 每条趋势至少带 1 个主链接；有补充来源可追加 1-2 个
- `跟进清单` 只记录对后续学习和监控真正有价值的项目

---

## 第五步：学习导向的提炼规则

每条趋势补充以下内容：

- **一句话判断**：这件事为什么值得我关注
- **学习点**：我应该理解的能力、产品策略或社区变化是什么
- **后续动作**：要不要继续追作者、追产品、追评论区、追竞品
- **跟进窗口**：`今天`, `3天内`, `1周内`, `低频观察`

优先保留这三类信号：

1. 能改变我对 AI 工具或模型判断的信号
2. 能暴露行业真实使用反馈的信号
3. 能帮助我更新监控名单、关键词或学习地图的信号

---

## 红线

- **禁止** 未确认 Vault 名称就写入 Obsidian
- **禁止** 在 `obsidian` CLI 仅因沙箱不可连通时，直接绕过到 Vault 文件系统写入
- **禁止** 编造播放量、点赞数、评论数、分数
- **禁止** 只有平台名，没有原始链接
- **禁止** 把同一事件拆成多条伪趋势灌水
- **禁止** 只做摘要，不写学习判断
- **禁止** 写入 Obsidian 前不检查近 14 天是否已归档
- **禁止** 把明显与 AI 无关的科技热点混入
- **禁止** 默认把趋势转成文章选题，除非用户明确要求
- **禁止** 用WebSearch替代已登录的CDP抓取，除非用户明确要求

---

## 相关技能协同

- 需要操作 Obsidian 时，优先配合 `obsidian-cli` 或 `obsidian-markdown`
- 用 CDP 控制已登录的 Chrome，抓取各平台的原始讨论和真实反馈

### 推荐 Obsidian CLI 用法

```bash
obsidian vault="personal" search query="2026-06-04 AI趋势雷达" format=json
obsidian vault="personal" files folder="AI Trend Radar"
obsidian vault="personal" create path="AI Trend Radar/2026-06-04 AI趋势雷达.md" content="..."
obsidian vault="personal" read path="AI Trend Radar/2026-06-04 AI趋势雷达.md"
```

---

## 触发示例

- “抓今天的 AI 趋势，写进 Obsidian”
- “做一份多平台 AI 热点雷达，给我学习用”
- “看看 X、YouTube、Reddit、HN 最近 AI 在热什么”
- “把 AI 趋势信号存成我的 Obsidian 学习笔记”
