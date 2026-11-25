# FateInsight 海外繁体版开发进度

更新日期：2026-11-25。

当前状态：分阶段开发中，尚未达到全量验收或上线条件。用户中心暂缓，优先完成八字对话与六爻问事。没有推送、合并或部署国内生产环境。

## 分支与代码位置

三个独立仓库使用 feature/overseas-i18n：

| 内容 | 工作目录 | 代码基线 |
|---|---|---|
| 后端 | E:/claude_projects/chat/overseas-worktrees/fate | stage 的 2c12a63 |
| Web | E:/claude_projects/chat/overseas-worktrees/fate-frontend | stage 的 7f316a0 |
| 文档 | E:/claude_projects/chat/docs | 原文档仓库 main |

业务目录是Git worktree，共享原仓库历史，不是复制的新项目。原stage/develop分支不改；原Web的app/panel/page.tsx未提交修改以及docs原有运营文档均不纳入本次提交。fate_personal、fate_wechat、fate-mobile-expo未修改。

## 已完成

- 接入next-intl 4.16.1，提供zh-CN/zh-TW资源、cookie语言选择、请求级配置和html lang；保留原URL结构。zh-HK/en尚未开放。
- 首页主体、示例卡片、步骤、FAQ及页脚支持简繁资源。按用户要求海外版隐藏语言选择器及公司版权/备案区；国内配置保留。
- 登录、邮箱注册、找回和重设密码页面文案抽取；海外Web默认邮箱登录，隐藏手机号入口，邀请码、密码规则及授权检查不变。登录/注册与排盘页面metadata已本地化。
- 八字排盘表单、按钮和结果静态标签；八字对话欢迎区、背景面板、操作和已知快捷问题；六爻问事场景预填、输入、起卦方式、结果静态标签和解读入口已接入资源。共用输入框和快捷操作已有翻译。
- JSON/SSE及主要聊天、六爻请求传Accept-Language；后端白名单解析、q权重处理和请求上下文隔离，缺省保持zh-CN。
- 八字System Prompt组装、报告User Prompt及六爻System Prompt增加台湾繁体约束。不转换JSON key、枚举、计算标识、RAG证据或用户历史原文。
- 海外套餐/会员页面不挂载购买流程；微信前端调用、支付router与部分服务入口增加地区限制；海外即使误设支付开关为true也不能启用国内支付策略。额度及扣费规则未放宽。
- 邮箱重复、邮箱/密码错误、账户不可用三类后端认证错误支持繁体。

## AI输出的实际状态

已写入Prompt语言要求，但没有完成真实AI端到端验证，不能保证所有入口都已持续输出繁体。

旧开场/报告缓存和历史回复保留原文，不自动重生成、不重复扣费。会话语言持久化、历史恢复、游客与异步任务路径仍需补齐并验证。每轮请求传语言与会话持久化语言不是同一项能力。

## 测试证据与边界

| 检查 | 结果 | 边界 |
|---|---|---|
| npm run build | 最近一轮通过 | 默认构建配置，不能代替海外独立部署验收 |
| npx tsc --noEmit | 通过 | 静态类型检查 |
| 认证/排盘定向ESLint | 通过 | 没有声称全仓库lint无历史问题 |
| 后端unittest | 7项通过 | 语言解析、并发隔离、Prompt规则、认证文案与地区策略；不连接业务数据库 |
| tests/auth-locale.cjs | 通过 | 四页面展示与校验，不寄信、不注册账号 |
| tests/conversation-locale.cjs | 通过 | 模拟API验证六爻预填/空输入和八字对话UI，不消耗真实额度 |
| tests/home-locale.cjs | 提交前复核通过 | cookie语言、示例切换、刷新保留及海外隐藏语言选择器/版权区 |

Python测试环境单独建于后端worktree的.venv，使用Python3.12、FastAPI0.165.0/Pydantic2.14.4；不是生产依赖锁定证明。原本机Python环境有损坏/沙箱执行问题，测试使用独立环境完成。

## 尚未完成与已知问题

1. 两条核心流程的真实AI开场、至少三轮追问、断流重试和历史恢复验证。
2. 动态卦名、十神等命理展示字段，部分恢复错误、后台动态快捷内容、分享图和共用消息操作仍有简体内容；不可宣称完整zh-TW。
3. 首页/根布局等其余SEO与结构化数据仍需全量语言审计；目前不是全站metadata已完成。
4. 海外出生地区支持白名单及明确拒绝策略尚未落实。旧入口固定120°E经度修正，新引擎虽有IANA支持，但DST歧义时间、节气跨日及均时差仍需单独确认，不改核心算法。
5. 用户中心、历史、其他内容页暂缓；地区币种/域名/登录方式的统一配置契约尚不完整。
6. 需要完整支付路径零外呼测试、国内回归和小程序原请求兼容回放。已有单元测试不等于全部支付入口已经端到端验收。
7. cookie读取使页面动态服务端渲染，后续评估缓存/性能。语言切换保留表单状态尚需完整测试矩阵。
8. npm安装时报告15项依赖漏洞（3 moderate、10 high、2 critical），未做可能破坏兼容的自动升级，需定位依赖来源。

## 配置与启动

已实现变量：后端FATE_REGION、FATE_PAYMENTS_ENABLED；Web NEXT_PUBLIC_REGION、NEXT_PUBLIC_DEFAULT_LOCALE、NEXT_PUBLIC_PAYMENTS_ENABLED。沿用NEXT_PUBLIC_API_BASE和NEXT_PUBLIC_SITE_URL。两端提供.env.overseas.example，无真实密钥。NEXT_PUBLIC配置需在启动开发服务或构建前设置。

本地Web预览示例（PowerShell）：

```powershell
Set-Location E:/claude_projects/chat/overseas-worktrees/fate-frontend
$env:NEXT_PUBLIC_REGION='overseas'
$env:NEXT_PUBLIC_DEFAULT_LOCALE='zh-TW'
$env:NEXT_PUBLIC_PAYMENTS_ENABLED='false'
$env:NEXT_PUBLIC_API_BASE='http://127.0.0.1:8000'
$env:NEXT_PUBLIC_SITE_URL='http://localhost:3019'
$env:NEXT_DIST_DIR='.next-overseas-visible'
npm run dev -- --hostname 127.0.0.1 --port 3019
```

现有预览为http://127.0.0.1:3019，主要查看页面，不代表真实后端已联调。后端安装完整项目依赖并配置测试数据库/Redis/模型密钥后，执行python -m uvicorn main:app --host 127.0.0.1 --port 8000。不得使用国内生产配置进行测试。

后端回归：.venv/Scripts/python.exe -m unittest app.test.test_i18n app.test.test_region_policy。浏览器测试使用本地Chrome，启动预览后执行node tests/auth-locale.cjs、node tests/conversation-locale.cjs、node tests/home-locale.cjs。

## 数据库及下一步

本轮无数据库迁移；未来若持久化会话/报告locale需要改表，提交原生SQL和回滚说明。

优先补齐八字/六爻剩余文案及真实AI语言链路，再执行计算跨语言一致性、支付零外呼、国内与小程序兼容回归。英文版复用资源key与地区配置，另做英文术语和Prompt审校，不改变命理算法和RAG检索逻辑。

实际逐文件清单以本次三个仓库提交的git show --stat为准；审计与计划见同目录overseas-i18n-audit.md、overseas-i18n-plan.md，部署细节见overseas-deployment.md。
