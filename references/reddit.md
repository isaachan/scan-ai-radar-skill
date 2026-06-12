# Reddit 抓取参考

## 目标

用 Reddit 看普通用户、开发者、企业员工和重度玩家的真实反馈，重点发现：

- 企业工具真实采用体验
- 模型、agent、coding tool 的踩坑与替代方案
- AI 工具在团队和公司环境里的限制
- 安全、隐私、成本、合规、幻觉、组织反弹等风险信号
- 前沿产品是否开始被真实工作流采用

## 优先板块

### 模型 / 技术

- `r/LocalLLaMA`
- `r/MachineLearning`
- `r/artificial`
- `r/ArtificialIntelligence`

### 工具 / 用户反馈

- `r/ChatGPT`
- `r/ClaudeAI`
- `r/Cursor`
- `r/ChatGPTCoding`
- `r/learnmachinelearning`

### 企业 / 工程 / 汽车相关

- `r/devops`
- `r/programming`
- `r/softwarearchitecture`
- `r/datascience`
- `r/cars`
- `r/SelfDrivingCars`
- `r/automotive`

## 抓取方式

- 搜索过去 7 天高互动帖子
- 优先 `top / hot / rising`
- 留意“真实体验”“踩坑”“替代方案”“公司禁用”“安全问题”“成本失控”“生产环境”“团队 rollout”
- 如果 Reddit 匿名 JSON endpoint 超时或失败，记录失败原因；不要编造 Reddit 信号

## 抓取字段

- 帖子标题
- 子版块
- 分数 / 评论数
- 发布时间
- 帖子 URL
- 高赞评论中的关键信号
- 初步分类：基础研究 / 企业应用 / 创业前沿 / 风险信号
- 对企业 adoption 或汽车研发中心的潜在影响

## 保留标准

- 不只是一句情绪宣泄
- 评论区有信息增量，能看出真实采用、真实失望、真实迁移或风险暴露
- 能帮助判断工具是否适合企业环境、团队工作流或研发中心场景
- 对个人生产力工具的讨论，只有在能推断团队/企业迁移可能性时保留

## 观察重点

- 用户在企业或团队环境里放弃什么，转向什么
- 哪些模型或工具的口碑在真实使用中变化
- 哪类限制条件被反复抱怨：隐私、上下文、幻觉、成本、速度、权限、集成、审计
- 哪些帖子值得后续持续跟楼，作为 adoption 风险样本
- 汽车、自动驾驶、工程研发相关社区是否出现 AI 工具真实采用或抵触
