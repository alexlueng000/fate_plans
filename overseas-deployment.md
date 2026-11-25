# 海外独立部署草案

## 2026-11-25 基础层实施进度

按最新优先级暂停用户中心，处理八字对话/六爻问事：panel欢迎区、背景面板、操作菜单及快捷问题；liuyao输入、场景预填、起卦方式、结果区静态标签、解读入口；共用InputArea/QuickActions已接入Conversation资源和白名单文案映射。六爻普通API和游客起卦补语言头，SSE继续复用既有语言透传。计算枚举、用户问题原文、后台快捷Prompt和历史识别前缀保持原样。tests/conversation-locale.cjs以模拟API验证六爻游客场景繁体预填/空问题校验、八字欢迎区和输入框，已通过；前端构建、类型检查通过。真实AI、动态卦名/命理字段、部分恢复提示、分享图片和共用消息操作完整覆盖仍待继续，不将模拟UI测试当作后端联调验收。

认证页面批次：登录、邮箱注册、找回密码、重设密码的表单、前端校验、按钮、密码强度提示抽取到Auth资源；登录/注册metadata本地化。海外Web默认邮箱入口，隐藏手机登录链接，/register直接进入邮箱注册，国内原跳转策略保持。邮箱登录请求传语言头，后端邮箱重复、邮箱/密码错误、账户不可用三种错误支持繁体。未改变邀请码要求、密码强度、认证与授权规则。后端其他动态错误（邀请码服务、邮件服务、限流等）尚未完整翻译，真实邮件/登录联调未执行。

验证：tests/auth-locale.cjs无界面Chrome通过四页面繁体展示、海外邮箱默认和表单校验检查（不提交注册、不寄信）；认证页面ESLint、前端构建、类型检查通过；后端语言与地区策略共7项测试通过。用户中心、历史记录和六爻页面完整国际化仍待完成。

第二批：八字排盘page表单/表头/按钮/提示已抽到Paipan命名空间；排盘metadata按请求语言生成；chat/panel的初始化、重新解读和清空请求补语言头。八字build_full_system_prompt、报告User Prompt、六爻build_system_prompt增加仅面向展示文本的台湾繁体约束，默认简体返回空附加规则，计算与检索函数未改。新增语言规则切换测试，当前6项后端测试通过。尚未验证真实AI持续输出；缓存命中仍返回原历史文本，未重生成或改变扣费键。会话语言持久化、异步任务语言、游客流程、全站文案和浏览器切换表单状态测试仍待完成。排盘表中的动态命理名称、时间修正提示仍有待提取内容，不能视为完整台湾版。

业务修改位于 E:/claude_projects/chat/overseas-worktrees/fate 与 E:/claude_projects/chat/overseas-worktrees/fate-frontend，均为 feature/overseas-i18n。原目录仍为stage；原有panel未提交修改保留。尚未提交或部署。

已实现：next-intl依赖与锁文件、request语言配置、两套基础资源、保持组件实例的语言切换、html lang、导航部分文案、通用JSON/SSE语言请求头；后端Accept-Language解析与请求级上下文；地区支付入口及微信服务保护；海外套餐/会员页停止挂载支付组件；两端.env.overseas.example。

当前实际生效的新变量仅为：后端FATE_REGION和FATE_PAYMENTS_ENABLED；前端NEXT_PUBLIC_REGION、NEXT_PUBLIC_DEFAULT_LOCALE、NEXT_PUBLIC_PAYMENTS_ENABLED。下文其余拟定变量仍待实施。海外后端即便误设payments=true也拒绝国内支付。

验证：默认配置npm run build通过（联网下载原有字体）；npx tsc --noEmit通过；定向ESLint零错误，Header原有BookOpen未使用警告1条；语言解析、并发隔离、地区策略5项unittest通过。测试命令：在后端worktree执行 .venv/Scripts/python.exe -m unittest app.test.test_i18n app.test.test_region_policy。测试使用独立Python3.12环境、FastAPI0.165.0、Pydantic2.14.4；没有连接业务数据库、AI或支付服务。未完成海外配置构建和浏览器端到端验收。

限制：cookie语言解析使原可静态渲染页面动态化，部署需评估缓存成本。客户端切换目前只更新已接入词典的客户端组件，服务端文案与metadata后续接入。AI prompt、持久化会话locale、报告缓存、完整页面翻译、全部支付链接隐藏及海外出生时间校验仍未完成。npm安装审计报告15项依赖漏洞（3 moderate、10 high、2 critical），未执行可能破坏兼容性的自动升级；需后续定位引入来源。

实际修改文件分组：Web的.gitignore、package.json/package-lock.json、next.config.ts、app/layout.tsx、app/components/Header.tsx/PaymentsUnavailable.tsx、app/lib/api.ts/chat/sse.ts/wechat-payment.ts、app/pricing/page.tsx、app/membership/page.tsx、i18n/四文件、messages/两文件及环境示例；后端main.py、app/config.py、app/i18n.py、app/region.py、app/routers/payments.py、app/services/payments.py/wechat_jsapi.py、两份test及环境示例。无数据库迁移。

状态：设计文档，配置项尚未实现，未部署。国内现有生产服务保持原状。

## 配置契约

下列为拟新增变量，最终以实施后的示例文件为准；公共变量不得含密钥。

| 变量 | 国内 | 海外 | 作用 |
|---|---|---|---|
| FATE_REGION | cn | overseas | 服务端地区策略 |
| FATE_DEFAULT_LOCALE | zh-CN | zh-TW | 默认展示语言 |
| FATE_DEFAULT_CURRENCY | CNY | TWD（待业务确认） | 展示配置，不换算现有价格 |
| FATE_SITE_URL | 现有国内域名 | 待确认域名 | canonical/分享来源 |
| FATE_PAYMENTS_ENABLED | true | false | 服务端支付总开关 |
| FATE_PAYMENT_CHANNELS | 现有微信渠道 | 空列表 | 国内支付隔离 |
| FATE_LOGIN_METHODS | 现有方式 | email | 已有登录能力开关 |
| FATE_FEATURES | 国内现有集合 | 审核后开放集合 | 页面与能力开关 |
| NEXT_PUBLIC_REGION | cn | overseas | 前端可见地区 |
| NEXT_PUBLIC_DEFAULT_LOCALE | zh-CN | zh-TW | 初始渲染默认 |
| NEXT_PUBLIC_SITE_URL | 国内站 | 海外站 | Web站点地址 |

沿用NEXT_PUBLIC_API_BASE；应拆清浏览器请求与服务端rewrite目标，避免 /api/api 或相对URL被当作代理源。地区公共配置建议由服务端只读配置端点统一提供。NEXT_PUBLIC变量通常在构建时固化，国内外各自构建或验证专门运行时注入方案，不能只改运行容器变量就宣称切换成功。

沿用数据库、JWT、DeepSeek、SMTP、REDIS_URL和KB索引配置，仅从密钥管理注入，本文不复制任何真实值。海外使用独立环境、数据库及Redis，不默认连接国内生产；不注入国内微信支付密钥。必须防止配置缺失时自动回退到国内API。RAG资源可复用相同版本文件，但服务运行缓存独立。

## 本地启动与检查

以下是现有工程的启动方式；新增地区变量在实现前没有效果。先准备本地测试数据库、测试凭据及RAG索引，禁止使用生产凭据跑回归。

```powershell
Set-Location E:/claude_projects/chat/fate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

另一个终端：

```powershell
Set-Location E:/claude_projects/chat/fate-frontend
$env:NEXT_PUBLIC_API_BASE = 'http://127.0.0.1:8000'
npm run dev
```

构建/静态检查（本轮未执行）：

```powershell
Set-Location E:/claude_projects/chat/fate-frontend
npm run build
npx tsc --noEmit
npm run lint
```

后端使用工程虚拟环境和测试库执行 E:/claude_projects/chat/fate/app/test 中相关测试；执行前核对测试框架、fixture和数据库隔离，不能直接对生产库全量运行。

## 数据库与发布

本次文档阶段无数据库迁移。优先会话store保存locale，保持现有DB结构；若报告缓存/历史语言需要持久化，实施时提交原生SQL与回滚语句，不能提前声称无需迁移。

Web已有standalone输出，后端有Dockerfile。海外独立域名/TLS/CORS、API实例及密钥配置，代理必须支持SSE且关闭不当缓冲，检查超时。准备独立镜像版本与可回滚配置，先在海外测试环境跑10项验收再考虑发布。

尚待确认：海外域名、数据存储位置、默认币种、允许的出生地区和Git基线。上线阻断项：历史时区正确性、海外支付服务端隔离、完整zh-TW资源、会话恢复语言、默认客户端兼容性。未接海外支付前保持购买关闭，已有额度/授权检查继续有效。

## 本轮交付与测试结果

仅新增本文件及 E:/claude_projects/chat/docs/overseas-i18n-audit.md、E:/claude_projects/chat/docs/overseas-i18n-plan.md。未修改业务源码、未安装依赖、未改变任何生产部署。静态审计完成；构建、类型检查、自动化、真实AI及小程序联调均未执行，下一阶段逐项记录。
