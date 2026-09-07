# Fate 文档中心

本目录集中存放 FateInsight / 易占大师的产品、设计、研发、运营和商业化资料，现已按用途归档。

> 当前有效产品由 `fate_backend/` 与 `fate_frontend/` 组成。微信小程序已停止维护，相关资料位于 `90-archive/mini-program/`。

## 目录结构

```text
fate_plans/
├── 01-product-strategy/          产品战略、评审与路线图
├── 02-product-features/          产品功能设计
│   ├── bazi-report/              八字、排盘、报告与 Prompt
│   ├── liuyao/                   六爻设计、Prompt 与实现总结
│   ├── xinjing/                  心镜灯与人生观察
│   └── user-platform/            用户、对话、反馈、后台与指标
├── 03-commercialization/         定价、计费、支付与商业化
├── 04-design/                    UI、品牌与页面设计
│   └── prototypes/               HTML 页面原型
├── 05-growth-content/            增长与内容运营
│   ├── articles/                 文章策划稿
│   └── wechat/                   公众号成稿与封面素材
├── 06-engineering/               环境、部署、测试与迁移
│   └── migrations/               数据库迁移 SQL
├── 90-archive/                   历史与待确认资料
└── 99-assets/                    独立图片素材
```

## 快速入口

| 场景 | 推荐先读 |
| --- | --- |
| 了解项目全貌 | [项目进度报告](01-product-strategy/project-progress-report.md)、[Web 产品路线图](01-product-strategy/Web产品评估与优化路线图-2026-07-29.md) |
| 查看产品方向 | [八字 Agent 路线图](01-product-strategy/2026-08-01-bazi-agent-roadmap.md)、[三功能整合路线图](01-product-strategy/三功能整合开发路线图.md) |
| 开发八字排盘 | [排盘逻辑](02-product-features/bazi-report/paipan-logic.md)、[排盘 UI 改造](02-product-features/bazi-report/paipan-ui-redesign.md) |
| 开发六爻 | [产品设计](02-product-features/liuyao/liuyao-design-doc.md)、[Prompt](02-product-features/liuyao/liuyao-prompts.md)、[开发总结](02-product-features/liuyao/六爻功能开发总结.md) |
| 开发心镜灯 | [产品整合方案](02-product-features/xinjing/心镜灯产品整合方案.md)、[人生观察 V1 PRD](02-product-features/xinjing/人生观察记录_V1_功能需求文档.md) |
| 开发计费支付 | [次数计费规划](03-commercialization/quota-billing.md)、[实现说明](03-commercialization/quota-implementation.md)、[真实支付接入](03-commercialization/真实微信支付宝付费接入实施文档.md) |
| 做内容运营 | [30 天推广计划](05-growth-content/2026-08-24-marketing.md)、[内容创作方案](05-growth-content/2026-08-25-content-strategy.md)、[公众号启动包](05-growth-content/wechat-oa-launch-package.md) |
| 搭建与部署 | [开发环境](06-engineering/dev-environment-setup.md)、[部署流程](06-engineering/deployment-workflow.md) |

## 分类说明

### 01. 产品战略

[进入目录](01-product-strategy/) · 包含项目进度、产品评审、综合路线图、Agent 规划、App 路线图、留存策略与工作台规划。

重点文档：

- [项目进度报告](01-product-strategy/project-progress-report.md)
- [Web 产品评估与优化路线图](01-product-strategy/Web产品评估与优化路线图-2026-07-29.md)
- [10 位产品经理综合评审](01-product-strategy/product-review-10-world-class-pms.md)
- [八字 Agent V2 开发设计](01-product-strategy/2026-08-02-bazi-agent-development-design.md)

### 02. 功能设计

- [八字与报告](02-product-features/bazi-report/)：排盘逻辑、默认命盘、报告 Prompt 和排盘 UI。
- [六爻](02-product-features/liuyao/)：产品设计、Prompt、开发总结和产品评审。
- [心镜灯与人生观察](02-product-features/xinjing/)：产品方案、PRD、开发总结和迁移指南。
- [用户与平台能力](02-product-features/user-platform/)：登录、对话、评价、反馈、后台、指标和日志。

### 03. 商业化

[进入目录](03-commercialization/) · 包含商业化规划、定价、次数包、订阅、支付接入、退款和估值评审。

重点文档：

- [2026 定价方案](03-commercialization/pricing-strategy-2026.md)
- [次数收费模型](03-commercialization/quota-billing.md)
- [Quota 实现说明](03-commercialization/quota-implementation.md)
- [微信与支付宝真实支付](03-commercialization/真实微信支付宝付费接入实施文档.md)

### 04. 设计与原型

[进入目录](04-design/) · 包含 Web UI 评估、设计系统、前端重构、落地页、图标和 Logo 方案。

- [Web UI 评估](04-design/Web-UI评估与优化建议-2026-07-29.md)
- [Web UI 重设计](04-design/ui-redesign-plan.md)
- [落地页重设计](04-design/landing-page-redesign.md)
- [HTML 页面原型](04-design/prototypes/)

### 05. 增长与内容

[进入目录](05-growth-content/) · 包含增长策略、推广计划、公众号运营体系、文章策划和成稿。

- [30 天推广计划](05-growth-content/2026-08-24-marketing.md)
- [多平台内容方案](05-growth-content/2026-08-25-content-strategy.md)
- [公众号启动包](05-growth-content/wechat-oa-launch-package.md)
- [文章策划稿](05-growth-content/articles/)
- [公众号成稿及封面](05-growth-content/wechat/)

### 06. 工程与运维

[进入目录](06-engineering/) · 包含环境搭建、部署、API 测试、发布、分支报告和数据库迁移。

- [开发环境搭建](06-engineering/dev-environment-setup.md)
- [部署流程](06-engineering/deployment-workflow.md)
- [API 测试命令](06-engineering/api-test-commands.md)
- [数据库迁移 SQL](06-engineering/migrations/)

### 90. 历史资料

- `90-archive/mini-program/`：已停止维护的微信小程序文档。
- `90-archive/uncategorized/function_upgrade.md`：缺少一级标题，待确认定位。
- `90-archive/uncategorized/modular-spinning-eagle.md`：与 Quota 文档主题重叠，待确认是否为旧版。

### 99. 素材

- [小易头像候选](99-assets/小易头像候选/)：AI 生成的头像候选图。
- [公众号封面素材](05-growth-content/wechat/covers/)：背景图、导出图和生成脚本。

## 文档维护规范

新文档建议使用 `YYYY-MM-DD-主题.md` 命名，并在开头注明状态、负责人、创建日期、最后更新日期和关联代码或 Issue。

1. 同一功能只保留一个主文档；实现总结和迁移指南作为关联文档。
2. 失效方案移入 `90-archive/`，不直接删除，并注明替代文档。
3. Prompt、SQL、HTML 原型和图片素材放入对应子目录。
4. 路径、域名、接口和技术栈以当前代码为准。
5. 新增或移动文件后同步更新本索引。
