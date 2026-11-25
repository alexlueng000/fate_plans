# 海外国际化代码审计

日期：2026-11-25。阶段：只读代码审计与方案；未实现国际化，未运行生产请求或修改数据库。以下为静态证据，不代表端到端验收通过。

## 仓库边界和工作区

工作区根 E:/claude_projects/chat 的 git rev-parse 失败，不能当作总仓库提交。以下均为独立仓库；路径均以该工作区绝对路径表示。

| 仓库 | 原分支 | 实际职责及技术栈 | 原有未提交改动 |
|---|---|---|---|
| E:/claude_projects/chat/fate | stage | FastAPI、SQLAlchemy/MySQL、lunar_python 1.4.8、DeepSeek、RAG、Redis | 无 |
| E:/claude_projects/chat/fate-frontend | stage | 主业务 Web，Next 15.5.21、React 19.1、TS5、Tailwind4，standalone | app/panel/page.tsx |
| E:/claude_projects/chat/fate_personal | main | 独立「见山」测试引流站，Next 15.5.24；人格/能量/关系测试，本地草稿，聚合埋点 | README.md、scripts/prepare-standalone.mjs、deploy/、scripts/prepare-standalone.check.mjs |
| E:/claude_projects/chat/fate_wechat | main | 微信小程序，Bearer API 客户端 | project.config.json |
| E:/claude_projects/chat/fate-mobile-expo | main | Expo56、RN0.85.3、React19.2.3、Expo Router；独立移动客户端 | 无 |
| E:/claude_projects/chat/docs | main | 产品、设计、商业、工程、运营文档独立仓库 | 多份运营文档、图片及脚本；全部保留 |

docs 已从当前 main 新建 feature/overseas-i18n，仅新增本任务文档。业务仓库尚未切换分支。后端 stage 比 develop 多16个提交，Web多21个，均无反向独有提交。若直接从 develop 实施，会漏掉当前审计的部分功能；开始业务修改前必须明确基线。

## 产品约束

已阅读 E:/claude_projects/chat/AGENTS.md、PRODUCT.md、DESIGN.md：保留视觉、首页核心表达、移动优先、现有命理行为；短信登录仅涉及后端与Web，小程序登录不改。fate_personal README 明确当前不接业务后端、不登录、不付费，不能误当主业务站。建议本期仅改主Web和后端，个人站及两移动客户端做兼容观察。

## 路由、文案与依赖

E:/claude_projects/chat/fate-frontend/app 使用 App Router，无现成 next-intl 依赖。核心页面有 /、/paipan、/liuyao、/chat、/panel、/profile/create、/history、/account、/membership、/pricing；认证位于 (auth) 路由组，还有 /try、/analysis、/reading、/reports、/career、/relationship、/xinji、/knowledge、/videos 等可达页面，不能只翻译首页。

中文散布在 page/layout、components、lib 的展示表、错误提示及 metadata。后端也返回展示文本和后台配置快捷按钮，不能仅提取 JSX。需区分注释、内部中文枚举、用户原文和真正可翻译文案。

E:/claude_projects/chat/fate-frontend/next.config.ts 将 /api/* 转发至 NEXT_PUBLIC_API_BASE，默认 localhost:8000；本地预览有独立 mock 路由，不可用来证明真实鉴权或扣费成功。构建忽略 ESLint，必须独立执行 lint。

## API、AI、数据和支付

- E:/claude_projects/chat/fate/app/routers/bazi.py：calc_paipan 与经度修正；E:/claude_projects/chat/fate/app/bazi_engine 为另一套结构化计算模块。不可整体替换或转换返回字典。
- E:/claude_projects/chat/fate/app/liuyao/paipan.py、prompts.py、chat_service.py：起卦、提示词、开场及续聊；router另有 guest_liuyao，需覆盖游客入口。
- E:/claude_projects/chat/fate/app/chat/service.py、utils.py：从DB加载普通/报告 system prompt，组合命盘与检索证据；多条开场、续聊、报告路径需要同一语言策略。
- E:/claude_projects/chat/fate/app/chat/rag.py：八字/六爻分索引，支持 KB_BAZI_INDEX_DIR、KB_LIUYAO_INDEX_DIR、旧 KB_INDEX_DIR，缓存并检索 top-k。保持查询、索引及排序算法不变，翻译不得作用于原始证据。
- E:/claude_projects/chat/fate/app/chat/store.py：Redis会话，未配置REDIS_URL时使用进程内后备；不是文档概述中的纯内存实现。历史恢复及 pinned prompt 都要考虑 locale。
- E:/claude_projects/chat/fate/app/routers/users.py：Web邮箱注册登录、mp登录、短信验证码登录、密码重置，旧 auth/login 标记 deprecated。前端认证状态与小程序请求使用Bearer；端点最终前缀须以main.py路由挂载核对。
- E:/claude_projects/chat/fate/app/routers/payments.py 已有微信 Native、JSAPI 入口；orders、webhooks、membership、entitlements、quota及services/payments.py、quota.py组成交易与授权链。只隐藏支付按钮不足以隔离海外支付。
- E:/claude_projects/chat/fate/app/models 下存在 user/profile/chat/liuyao/order/payment/refund/product/entitlement/quota/quota_ledger/usage_log、开场请求和会话摘要模型。翻译不得改变枚举、金额、幂等键和授权语义。此次未连接数据库，实际DDL与迁移状态待测试库核实。
- E:/claude_projects/chat/fate_wechat/miniprogram/utils/request.ts 和 E:/claude_projects/chat/fate-mobile-expo/src/lib/api.ts 是现有客户端兼容重点，不要求它们新增语言参数。

## 海外出生时间风险

1. 旧入口以120°E为基准，每度4分钟；地名使用geo_amap，失败会回退原钟表时间。海外路径不得沿用这种静默回退。
2. 新引擎 schemas.py 校验IANA时区，calendar.py用历史标准偏移推算中央经线；这不等于所有API已接入，也不等于完整历史夏令时支持。
3. calendar.py通过replace(tzinfo=ZoneInfo)附加时区，需要专门验证DST不存在时间与重复时间；当前adjust_birth_time直接在当地钟表时间加经度差，夏令时修正正确性未获证明。
4. 均时差明确未实现（请求时抛NotImplementedError），当前“真太阳时”实际为经度修正，不可宣传为完整实现。
5. 节气边界、23点/0点换日、跨年月、经度跨日和农历闰月必须建立独立黄金样例。本轮不修改算法。

上线前使用地区支持白名单；输入城市、时区、经纬度不能可靠确定时，前后端均明确拒绝计算，不能默认为上海。支持台湾语言不代表支持所有台湾历史出生时间。

## 验证现状

已完成目录、依赖、Git状态、关键调用静态检查；未运行构建、类型检查、业务自动化或真实模型调用。测试目录已存在 E:/claude_projects/chat/fate/app/test，含quota、paid_entitlements、opening_request等回归资产。所有10项业务验收仍待实现后执行；不得将静态审计标为通过。
