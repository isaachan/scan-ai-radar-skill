# X / Twitter 抓取参考

## 目标

用 X 捕捉 AI 圈最快的原始信号，包括：

- 模型发布与更新
- 产品演示与病毒传播
- 工作流新范式
- 社区立场突然转向

## 前提

- Chrome 已登录 X
- CDP 调试端口已开放。优先使用 `--remote-debugging-port=9223` 的 `Chrome-CDP` profile；如果 9223 不可用，再检查 9222。

## CDP 连通性检查

X 是默认主信号源。抓取前先确认能控制“已登录 X 的 Chrome”，不要把 Obsidian Electron 的 `dev:cdp` 当成 Chrome。

手动检查时先探测 9223，再探测 9222：

```bash
for port in 9223 9222; do
  echo "=== localhost:${port} /json/version ==="
  curl --noproxy '*' -sS "http://localhost:${port}/json/version"
  echo
  echo "=== localhost:${port} /json/list ==="
  curl --noproxy '*' -sS "http://localhost:${port}/json/list"
  echo
done
```

注意：

- 当前环境可能设置了 `http_proxy` / `https_proxy` / `all_proxy`，访问本机 CDP 端点时必须绕过代理，否则请求会被公司代理转发并失败。
- 本机实测可用端口可能是 `9223`。不要固定假设 `9222` 可用；先检查 `9223`，再检查 `9222`。
- 如果某个端口 `/json/version` 或 `/json/list` 返回 404、空响应、HTML 错误页，说明该端口不符合标准 Chrome CDP endpoint，不能继续假设 X 可抓。
- 如果 `lsof` 显示 Chrome 监听某个端口，但 `/json/version` 返回 404，该端口仍然不可用；继续探测其他候选端口。
- 如果只有 `obsidian dev:cdp` 可用，那只是 Obsidian Electron CDP，不能用于已登录 X 抓取。
- 如果 CDP 不可用，必须在输出笔记的 `### X` 小节写明具体失败点，并停止声称“X 没有热点”。

标准可用条件：

- `/json/version` 返回 JSON，包含 `Browser` / `Protocol-Version` 等字段
- `/json/list` 返回 page targets
- 至少一个 target 是 `x.com`，或者能新开 / 导航到 X 搜索页并读取内容

记录实际使用端口：

- 一旦某个端口通过标准可用条件，本次后续 X 搜索和 KOL 扫描都使用同一个端口。
- 在抓取日志或失败记录里写明实际使用的端口，例如 `CDP port: 9223`。

如果 Chrome 没有用调试端口启动，重新启动示例：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-CDP" \
  --profile-directory="Default" \
  --no-first-run
```

`Chrome-CDP` 应该是从原始 `Chrome` profile 复制出来的非默认数据目录。不要直接拿默认 `Chrome` 目录开 CDP，否则 Chrome 可能拒绝远程调试，或和现有实例 / singleton 锁冲突。

如果已有 Chrome 正在运行，可能需要先完全退出 Chrome，再用调试端口启动。不要在未确认用户接受的情况下关闭用户浏览器。

诊断端口占用时使用：

```bash
lsof -nP -iTCP:9223 -sTCP:LISTEN
lsof -nP -iTCP:9222 -sTCP:LISTEN
ps -p <PID> -o pid,ppid,command=
```

如果 9222 被普通 Chrome 进程占用且命令行没有 `--remote-debugging-port=9222`，而 9223 由 `Chrome-CDP` profile 启动并返回标准 JSON，则使用 9223。

## 搜索窗口

`{since_date}` = 今天 -7 天，格式 `YYYY-MM-DD`

## 推荐搜索组

```text
https://x.com/search?q=(Claude+OR+ChatGPT+OR+Gemini+OR+Grok+OR+DeepSeek+OR+Cursor+OR+"Claude+Code"+OR+Manus)+(release+OR+launch+OR+update+OR+new+OR+demo)+min_faves:300+-is:retweet+lang:en+since:{since_date}&src=typed_query&f=top

https://x.com/search?q=("AI+agent"+OR+"browser+use"+OR+MCP+OR+"computer+use"+OR+n8n+OR+workflow)+(demo+OR+tutorial+OR+launch+OR+viral)+min_faves:200+-is:retweet+lang:en+since:{since_date}&src=typed_query&f=top

https://x.com/search?q=(Claude+OR+GPT+OR+Gemini+OR+Kimi+OR+豆包+OR+DeepSeek+OR+Manus)+(发布+OR+更新+OR+实测+OR+教程+OR+爆火)+min_faves:80+-is:retweet+lang:zh+since:{since_date}&src=typed_query&f=top
```

## 补充抓取：KOL 关注列表

除了关键词搜索，再做一轮 `账号时间线/近期帖子` 扫描。目的不是凑数量，而是补足：

- 一线产品/模型发布者的原始信号
- AI 工具重度用户的真实体验
- 技术、产品、增长视角的判断

优先关注以下账号：

```text
@borischen
@addyosmani
@simonw
@karpathy
@AnthropicAI
@OpenAI
@deepseek_ai
@levelsio
@steipete
@sama
@gregisenberg
@paulg
@mattshumer_
@nikitabier
@AYi_AInotes
```

### 账号分组意图

- `模型/产品官方`：`@AnthropicAI`, `@OpenAI`, `@deepseek_ai`
- `核心开发者/技术实践`：`@borischen`, `@addyosmani`, `@simonw`, `@karpathy`, `@steipete`
- `产品/增长/KOL`：`@levelsio`, `@gregisenberg`, `@mattshumer_`, `@nikitabier`, `@AYi_AInotes`
- `宏观判断/行业叙事`：`@sama`, `@paulg`

### 扫描规则

- 先跑搜索组，再看 KOL；不要只看 KOL 时间线
- 至少跑完三组搜索 URL；如果某组失败，记录失败原因和页面状态
- KOL 扫描至少覆盖 8 个账号，其中必须包含 `@OpenAI`、`@AnthropicAI`、`@simonw`、`@borischen`、`@steipete`
- 默认只看近 7 天；如果用户指定某一天，就优先看该日期前后 48 小时
- 优先原帖、长帖、演示帖、复盘帖；低信息量转发可跳过
- 如果同一事件在搜索组里已经抓到，KOL 帖子只作为补充来源或社区判断，不单独重复记一条趋势
- 如果某个 KOL 明显连续多天主导同一话题，可在 `跟进清单` 里记录该账号，而不是重复写多条
- 对中文 AI 圈信号，`@AYi_AInotes` 可作为中文高互动补充源，但不能替代英文原始发布源

### KOL 帖子保留标准

- 帖子本身带来新信息：发布、实测、对比、限制、成本、采用反馈
- 或者评论区明显出现高质量分歧、质疑、迁移信号
- 或者该账号的判断足以影响我对某工具/模型的看法

### 特别关注什么

- `@borischen`, `@steipete`, `@simonw`：Claude Code / agent workflow / MCP 的真实使用摩擦
- `@addyosmani`, `@karpathy`：技术范式变化是否值得进入长期学习清单
- `@levelsio`, `@gregisenberg`, `@nikitabier`, `@mattshumer_`：AI 产品化和增长玩法是否出现新模式
- `@sama`, `@paulg`：宏观叙事是否发生明显转向
- `@AnthropicAI`, `@OpenAI`, `@deepseek_ai`：官方发布是否和社区体感一致

## 抓取字段

- 作者
- 正文摘要
- 点赞 / 转发
- 发布时间
- 原帖 URL
- 抓取方式：搜索页 / 账号时间线 / 趋势页
- 抓取状态：成功 / 登录失效 / 风控 / 页面不可读 / CDP 不可用

## 保留标准

- 原帖优先于搬运号
- 有明确事件、演示、判断或讨论升级
- 至少能提炼一个学习点或监控点

## X 候选不足时的处理

如果最终 X 没有进入 Top Trends，必须在 `### X` 小节说明：

- CDP 是否可用
- 跑了哪几组搜索
- 扫了哪些账号
- 为什么候选被过滤
- 后续应该修复连接、降低阈值，还是继续观察

不要只写“没有足够高置信信号”。这句话无法区分“X 真没信号”和“没有真正抓到 X”。

## 观察重点

- 哪些产品被反复提到
- 哪些演示正在改变用户预期
- 哪些评论区出现了明显质疑或失望
- 哪些关键词值得加入长期监控
