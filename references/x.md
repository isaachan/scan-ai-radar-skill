# X / Twitter 抓取参考

## 目标

用 X 捕捉企业 AI Adoption Lead 需要最快知道的一手信号，包括：

- 基础研究：模型发布、论文、benchmark、evals、推理、多模态、agent、robotics、world model
- 企业应用：企业 AI adoption、AI 平台、治理、ROI、案例、工具链、组织模式、研发提效
- 汽车与工业：automotive AI、SDV、仿真、测试验证、需求工程、工程知识管理、工业软件、制造工程
- 创业前沿：AI-native 产品、agent startup、新交互、垂直工具、未来可能迁移到企业的应用

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

- 一旦某个端口通过标准可用条件，本次后续 X 搜索和账号扫描都使用同一个端口。
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

必须至少跑完以下 4 组搜索 URL。目的不是凑数量，而是保证基础研究、企业应用、汽车/工业、创业前沿都被覆盖。

### 1. 基础研究 / 模型动向

```text
https://x.com/search?q=("frontier+model"+OR+"reasoning+model"+OR+"multimodal+model"+OR+"world+model"+OR+"AI+benchmark"+OR+"SWE-bench"+OR+"agent+benchmark"+OR+"long+context"+OR+"robotics+foundation+model"+OR+evals)+(release+OR+paper+OR+benchmark+OR+SOTA+OR+launch+OR+update)+min_faves:200+-is:retweet+lang:en+since:{since_date}&src=typed_query&f=top
```

### 2. 企业 AI 应用 / Adoption

```text
https://x.com/search?q=("enterprise+AI"+OR+"AI+adoption"+OR+"AI+transformation"+OR+"AI+governance"+OR+"AI+ROI"+OR+"AI+copilot"+OR+"internal+AI+platform"+OR+"AI+center+of+excellence"+OR+"AI+risk+management"+OR+"developer+productivity")+(case+study+OR+rollout+OR+governance+OR+platform+OR+workflow+OR+productivity+OR+security)+min_faves:100+-is:retweet+lang:en+since:{since_date}&src=typed_query&f=top
```

### 3. 汽车研发 / 工业 AI

```text
https://x.com/search?q=("automotive+AI"+OR+"software-defined+vehicle"+OR+SDV+OR+"autonomous+driving+AI"+OR+"simulation+AI"+OR+"digital+twin+AI"+OR+"test+automation+AI"+OR+"requirements+engineering"+OR+MBSE+OR+PLM+OR+ALM)+(AI+OR+agent+OR+copilot+OR+automation+OR+platform+OR+workflow)+min_faves:50+-is:retweet+lang:en+since:{since_date}&src=typed_query&f=top
```

### 4. 创业前沿 / AI-native 应用

```text
https://x.com/search?q=("AI+startup"+OR+"AI-native"+OR+"vertical+AI"+OR+"AI+agent+startup"+OR+"browser+agent"+OR+"coding+agent"+OR+"design+agent"+OR+"research+agent"+OR+"generative+UI"+OR+"MCP+app"+OR+"agent+marketplace"+OR+"vibe+coding")+(demo+OR+launch+OR+workflow+OR+product+OR+viral+OR+case+study)+min_faves:100+-is:retweet+lang:en+since:{since_date}&src=typed_query&f=top
```

### 中文补充搜索

如果英文信号不足，或需要观察中文企业/汽车语境，补充：

```text
https://x.com/search?q=(企业AI+OR+AI落地+OR+AI治理+OR+研发提效+OR+汽车AI+OR+智能汽车+OR+软件定义汽车+OR+AI智能体+OR+AI创业)+(案例+OR+实践+OR+发布+OR+工具+OR+方法论+OR+趋势)+min_faves:50+-is:retweet+lang:zh+since:{since_date}&src=typed_query&f=top
```

## 补充抓取：账号关注列表

除了关键词搜索，再做一轮 `账号时间线/近期帖子` 扫描。至少覆盖 12 个账号，且必须覆盖四类账号。

### 基础研究 / 模型

```text
@OpenAI
@AnthropicAI
@GoogleDeepMind
@MetaAI
@MistralAI
@deepseek_ai
@karpathy
@simonw
@JeffDean
@ylecun
```

### 企业平台 / Adoption / 治理

```text
@Microsoft
@MSFTCopilot
@GoogleCloud
@awscloud
@nvidia
@salesforce
@ServiceNow
@UiPath
@BCG
@McKinsey
@Gartner_inc
@CIOonline
```

### 汽车 / 工业 / 工程软件

```text
@NVIDIADrive
@BoschGlobal
@Siemens
@Dassault3DS
@BMWGroup
@MercedesBenz
@VWGroup
@ToyotaMotorCorp
@Tesla_AI
```

### 创业前沿 / AI-native 产品

```text
@cursor_ai
@vercel
@Replit
@lovable_dev
@LangChainAI
@browserbasehq
@ComposioHQ
@modal_labs
@levelsio
@steipete
```

### 扫描规则

- 先跑搜索组，再看账号；不要只看账号时间线
- 至少跑完 4 组搜索 URL；如果某组失败，记录失败原因和页面状态
- 账号扫描至少覆盖 12 个账号，其中必须包含 `@OpenAI`、`@AnthropicAI`、`@GoogleDeepMind` 或 `@MetaAI` 之一、`@Microsoft` 或 `@GoogleCloud` 之一、`@nvidia` 或 `@NVIDIADrive` 之一、`@cursor_ai`、`@simonw`
- 默认只看近 7 天；如果用户指定某一天，就优先看该日期前后 48 小时
- 优先原帖、官方发布、长帖、企业案例、工程复盘、产品演示、治理/风险讨论；低信息量转发可跳过
- 如果同一事件在搜索组里已经抓到，账号帖子只作为补充来源或企业判断，不单独重复记一条趋势
- 如果某个账号明显连续多天主导同一话题，可在 `跟进清单` 里记录该账号，而不是重复写多条

## 抓取字段

- 作者 / 机构
- 正文摘要
- 点赞 / 转发 / 浏览（如页面可见）
- 发布时间
- 原帖 URL
- 抓取方式：搜索页 / 账号时间线 / 趋势页
- 抓取状态：成功 / 登录失效 / 风控 / 页面不可读 / CDP 不可用
- 初步分类：基础研究 / 企业应用 / 创业前沿 / 风险信号
- 对汽车研发中心的潜在影响

## 保留标准

- 原帖、官方发布、论文、企业案例、产品演示优先于搬运号
- 有明确事件、能力变化、企业采用案例、治理风险、工具链变化或讨论升级
- 至少能提炼一个企业影响、采用门槛或后续动作
- 对纯个人效率工具或营销帖，只有在能代表未来企业工作流迁移时才保留

## X 候选不足时的处理

如果最终 X 没有进入 Top Trends，必须在 `### X` 小节说明：

- CDP 是否可用
- 跑了哪几组搜索
- 扫了哪些账号
- 为什么候选被过滤
- 后续应该修复连接、降低阈值，还是继续观察

不要只写“没有足够高置信信号”。这句话无法区分“X 真没信号”和“没有真正抓到 X”。

## 观察重点

- 哪些能力可能影响企业 AI 平台和工具选型
- 哪些企业已经把 AI 从试点推向规模化部署
- 哪些治理、安全、成本、数据问题被反复提及
- 哪些汽车/工业场景出现真实采用迹象
- 哪些创业产品代表未来可能进入企业的 AI-native 工作流
