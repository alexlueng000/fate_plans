# 商业化核心指标埋点执行计划

## 目标

当前产品已经上线内测，但系统还没有完整记录商业化前需要观察的核心漏斗指标。本计划目标是用最小改造补齐数据采集能力，让后台或 SQL 能稳定回答以下问题：

- 新用户完成排盘率是多少？
- 首次解读后有多少用户继续追问？
- 用户 7 日内是否回来继续使用？
- 付费入口、下单、支付成功之间的转化率是多少？
- 反馈、投诉、退款相关问题是否可追踪？

第一版不追求复杂 BI，只先把关键事件可靠记录下来，保证后续能算指标。

## 当前系统现状

### 已有能力

- 用户注册、登录、来源字段已有基础记录。
- 已登录用户的会话和消息会写入 `conversations`、`messages`。
- 订单和支付已有 `orders`、`payments` 基础表。
- 用户反馈已有 `feedbacks` 表。
- 后台已有基础统计接口，例如用户数、会话数、消息数、来源分布。

### 主要缺口

- `/bazi/calc_paipan` 目前主要是日志记录，没有结构化入库事件。
- `UsageLog` 模型存在，但核心业务流程里没有稳定调用，不能覆盖产品漏斗。
- 匿名用户在排盘、首次解读、追问、付费入口浏览等行为上缺少统一标识。
- 当前只能看“有多少会话/消息”，无法准确还原“从进入页面到排盘成功再到追问/付费”的漏斗。
- 订单表能看付费结果，但缺少来源页面、入口、产品实验版本等上下文。

## 执行原则

1. 先做轻量自有事件表，不引入第三方埋点平台。
2. 事件命名稳定，属性灵活扩展，避免频繁改表。
3. 同时支持 Web、微信小程序、后端关键事件写入。
4. 匿名用户也要能追踪同一设备/浏览器内的行为链路。
5. 先用 SQL 验证指标，后台可视化放到第二阶段。
6. 不记录敏感出生信息明文到事件属性里，必要时只记录状态、类型、是否成功。

## 阶段拆分

### 第一阶段：最小可用埋点

预计耗时：0.5-1 天。

交付内容：

- 新增 `user_events` 表。
- 新增后端事件上报接口。
- Web 前端关键节点打点。
- 微信小程序关键节点打点。
- 后端在支付、反馈等关键业务动作中补充服务端事件。
- 提供核心指标 SQL。

第一阶段完成后，可以开始从生产数据库直接查询核心商业化指标。

### 第二阶段：后台统计接口

预计耗时：1-2 天。

交付内容：

- 新增后台漏斗统计 API。
- 新增留存统计 API。
- 新增付费转化统计 API。
- 新增反馈/投诉趋势统计 API。
- 管理后台展示基础图表和时间筛选。

### 第三阶段：精细化运营分析

预计耗时：2-3 天。

交付内容：

- 渠道参数追踪。
- 活动码、邀请码、KOC 分佣标识。
- A/B 实验版本字段规范。
- 付费报告类型维度分析。
- 用户分层，例如新用户、活跃用户、已付费用户、高频追问用户。

## 数据表设计

第一版建议新增一张通用事件表：`user_events`。

### 原生 SQL

```sql
CREATE TABLE user_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  event_name VARCHAR(80) NOT NULL COMMENT '事件名',
  user_id BIGINT UNSIGNED NULL COMMENT '登录用户ID',
  anonymous_id VARCHAR(64) NULL COMMENT '匿名设备/浏览器标识',
  session_id VARCHAR(64) NULL COMMENT '前端会话ID',
  source VARCHAR(32) NULL COMMENT '来源端: web/miniapp/server',
  path VARCHAR(255) NULL COMMENT '页面路径或接口路径',
  referrer VARCHAR(512) NULL COMMENT '来源页面',
  utm_source VARCHAR(80) NULL COMMENT '渠道来源',
  utm_medium VARCHAR(80) NULL COMMENT '渠道媒介',
  utm_campaign VARCHAR(120) NULL COMMENT '活动名称',
  properties JSON NULL COMMENT '事件扩展属性',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_user_events_event_time (event_name, created_at),
  KEY ix_user_events_user_time (user_id, created_at),
  KEY ix_user_events_anonymous_time (anonymous_id, created_at),
  KEY ix_user_events_session_time (session_id, created_at),
  KEY ix_user_events_source_time (source, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 字段说明

| 字段 | 用途 |
|---|---|
| `event_name` | 统一事件名，用于统计漏斗 |
| `user_id` | 登录后绑定用户 |
| `anonymous_id` | 未登录时识别同一设备或浏览器 |
| `session_id` | 一次访问会话，用于短链路漏斗 |
| `source` | 区分 Web、小程序、服务端 |
| `path` | 页面路径或接口路径 |
| `referrer` | 来源页面 |
| `utm_*` | 推广渠道参数 |
| `properties` | 事件上下文，例如产品码、订单号、是否成功、错误码 |

## 后端改造计划

### 新增模型

文件建议：

- `E:\claude_projects\chat\fate\app\models\user_event.py`

模型字段对应 `user_events` 表。

### 新增服务

文件建议：

- `E:\claude_projects\chat\fate\app\services\events.py`

职责：

- 校验事件名长度和属性大小。
- 自动填充 `user_id`、`source`、`path`。
- 捕获异常但不影响主业务流程。
- 对服务端关键事件提供便捷函数。

### 新增路由

文件建议：

- `E:\claude_projects\chat\fate\app\routers\events.py`

接口：

```http
POST /api/events/track
```

请求体草案：

```json
{
  "event_name": "paipan_completed",
  "anonymous_id": "anon_xxx",
  "session_id": "sess_xxx",
  "source": "web",
  "path": "/report",
  "referrer": "https://fateinsight.site/",
  "utm_source": "xiaohongshu",
  "utm_medium": "post",
  "utm_campaign": "2026-liunian",
  "properties": {
    "success": true,
    "use_true_solar": true
  }
}
```

### 服务端补充事件

建议在以下后端位置补服务端事件：

| 业务动作 | 建议事件 |
|---|---|
| 排盘接口成功 | `paipan_completed` |
| 排盘接口失败 | `paipan_failed` |
| 对话创建成功 | `chat_started` |
| 追问成功写入 | `followup_sent` |
| 创建订单 | `order_created` |
| 支付成功 webhook | `payment_success` |
| 支付失败或关闭 | `payment_failed` |
| 反馈提交 | `feedback_submitted` |

说明：前端事件适合记录用户点击和页面行为，服务端事件适合记录最终成功状态。关键指标以服务端成功事件为准。

## Web 前端改造计划

### 新增工具

文件建议：

- `E:\claude_projects\chat\fate-frontend\app\lib\analytics.ts`

职责：

- 生成并保存 `anonymous_id`。
- 每次页面会话生成 `session_id`。
- 读取 URL 中的 `utm_source`、`utm_medium`、`utm_campaign`。
- 封装 `track(eventName, properties)`。
- 上报失败时静默处理，不影响用户体验。

### Web 打点点位

| 页面/动作 | 事件名 | 说明 |
|---|---|---|
| 进入首页 | `page_view` | 记录 `path` |
| 进入排盘/报告页 | `paipan_page_viewed` | 漏斗起点 |
| 用户提交出生信息 | `paipan_started` | 表单提交 |
| 排盘成功 | `paipan_completed` | 排盘完成率分子 |
| 排盘失败 | `paipan_failed` | 记录错误类型 |
| 开始 AI 解读 | `chat_started` | 首次解读开始 |
| 首次 AI 回复完成 | `first_reply_completed` | 内容触达 |
| 用户发送追问 | `followup_sent` | 追问率 |
| 进入定价页 | `pricing_viewed` | 付费漏斗起点 |
| 点击购买 | `purchase_clicked` | 购买意图 |
| 创建订单成功 | `order_created` | 服务端也记录 |
| 支付成功页/回调确认 | `payment_success_viewed` | 前端确认 |

## 微信小程序改造计划

### 新增工具

文件建议：

- `E:\claude_projects\chat\fate_wechat\miniprogram\utils\analytics.ts`

职责：

- 使用本地存储保存 `anonymous_id`。
- 启动时生成 `session_id`。
- 封装 `track(eventName, properties)`。
- 自动带上页面路径、来源端 `miniapp`。

### 小程序打点点位

| 页面/动作 | 事件名 |
|---|---|
| 首页展示 | `page_view` |
| 打开排盘弹窗 | `paipan_form_opened` |
| 提交排盘 | `paipan_started` |
| 排盘成功 | `paipan_completed` |
| 进入结果页 | `result_viewed` |
| 开始聊天 | `chat_started` |
| 发送追问 | `followup_sent` |
| 进入我的/账户页 | `account_viewed` |
| 提交反馈 | `feedback_submitted` |

## 事件命名规范

统一使用小写蛇形命名：

- 页面浏览：`*_viewed`
- 用户主动点击：`*_clicked`
- 流程开始：`*_started`
- 流程完成：`*_completed`
- 流程失败：`*_failed`
- 业务结果：`payment_success`、`order_created`

第一版核心事件清单：

```text
page_view
paipan_page_viewed
paipan_form_opened
paipan_started
paipan_completed
paipan_failed
chat_started
first_reply_completed
followup_sent
pricing_viewed
purchase_clicked
order_created
payment_success
payment_failed
feedback_submitted
refund_requested
refund_success
```

## 核心指标计算 SQL

以下 SQL 以最近 7 天为例，实际可替换时间范围。

### 新用户完成排盘率

定义：首次进入排盘页或提交排盘的用户中，最终完成排盘的比例。

```sql
SELECT
  COUNT(DISTINCT completed.actor_id) / NULLIF(COUNT(DISTINCT started.actor_id), 0) AS paipan_completion_rate,
  COUNT(DISTINCT started.actor_id) AS started_users,
  COUNT(DISTINCT completed.actor_id) AS completed_users
FROM (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id
  FROM user_events
  WHERE event_name IN ('paipan_page_viewed', 'paipan_started')
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) started
LEFT JOIN (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id
  FROM user_events
  WHERE event_name = 'paipan_completed'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) completed ON completed.actor_id = started.actor_id;
```

### 首次解读后追问率

定义：完成首次 AI 回复的用户中，后续发送追问的比例。

```sql
SELECT
  COUNT(DISTINCT f.actor_id) / NULLIF(COUNT(DISTINCT r.actor_id), 0) AS followup_rate,
  COUNT(DISTINCT r.actor_id) AS first_reply_users,
  COUNT(DISTINCT f.actor_id) AS followup_users
FROM (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id, MIN(created_at) AS first_reply_at
  FROM user_events
  WHERE event_name = 'first_reply_completed'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  GROUP BY COALESCE(CAST(user_id AS CHAR), anonymous_id)
) r
LEFT JOIN (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id, created_at
  FROM user_events
  WHERE event_name = 'followup_sent'
) f ON f.actor_id = r.actor_id AND f.created_at > r.first_reply_at;
```

### 7 日复访率

定义：某天首次完成核心行为的用户，在 7 日内是否再次发生核心行为。

```sql
SELECT
  COUNT(DISTINCT retained.actor_id) / NULLIF(COUNT(DISTINCT cohort.actor_id), 0) AS retention_7d,
  COUNT(DISTINCT cohort.actor_id) AS cohort_users,
  COUNT(DISTINCT retained.actor_id) AS retained_users
FROM (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id, DATE(MIN(created_at)) AS cohort_date
  FROM user_events
  WHERE event_name IN ('paipan_completed', 'chat_started', 'followup_sent')
    AND created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
    AND created_at < DATE_SUB(CURDATE(), INTERVAL 7 DAY)
  GROUP BY COALESCE(CAST(user_id AS CHAR), anonymous_id)
) cohort
LEFT JOIN (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id, created_at
  FROM user_events
  WHERE event_name IN ('paipan_completed', 'chat_started', 'followup_sent')
) retained
  ON retained.actor_id = cohort.actor_id
 AND retained.created_at >= DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY)
 AND retained.created_at < DATE_ADD(cohort.cohort_date, INTERVAL 8 DAY);
```

### 付费转化率

定义：进入定价页的用户中，支付成功的比例。

```sql
SELECT
  COUNT(DISTINCT paid.actor_id) / NULLIF(COUNT(DISTINCT viewed.actor_id), 0) AS payment_conversion_rate,
  COUNT(DISTINCT viewed.actor_id) AS pricing_view_users,
  COUNT(DISTINCT paid.actor_id) AS paid_users
FROM (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id
  FROM user_events
  WHERE event_name = 'pricing_viewed'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) viewed
LEFT JOIN (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id
  FROM user_events
  WHERE event_name = 'payment_success'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) paid ON paid.actor_id = viewed.actor_id;
```

### 投诉/反馈率

定义：核心使用用户中，提交反馈、投诉、退款请求的比例。

```sql
SELECT
  COUNT(DISTINCT issue.actor_id) / NULLIF(COUNT(DISTINCT active.actor_id), 0) AS issue_rate,
  COUNT(DISTINCT active.actor_id) AS active_users,
  COUNT(DISTINCT issue.actor_id) AS issue_users
FROM (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id
  FROM user_events
  WHERE event_name IN ('paipan_completed', 'chat_started', 'followup_sent', 'payment_success')
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) active
LEFT JOIN (
  SELECT COALESCE(CAST(user_id AS CHAR), anonymous_id) AS actor_id
  FROM user_events
  WHERE event_name IN ('feedback_submitted', 'refund_requested')
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
) issue ON issue.actor_id = active.actor_id;
```

## 后台展示建议

第一版可以先不做页面，只保留 SQL。第二阶段后台建议增加一个“商业指标”页面：

- 时间范围：今天、7 天、30 天、自定义。
- 漏斗：排盘页访问 -> 排盘提交 -> 排盘完成 -> 开始解读 -> 首次回复完成 -> 追问。
- 付费：定价页访问 -> 点击购买 -> 创建订单 -> 支付成功。
- 留存：次日、3 日、7 日复访。
- 反馈：反馈数、投诉数、退款请求数。
- 渠道：按 `utm_source` 查看转化。

## 验收标准

第一阶段验收：

- Web 端完成一次排盘后，数据库出现 `paipan_started`、`paipan_completed`。
- Web 端完成一次首次解读后，数据库出现 `chat_started`、`first_reply_completed`。
- Web 端发送追问后，数据库出现 `followup_sent`。
- 小程序完成排盘和追问后，数据库能看到 `source = miniapp` 的事件。
- 创建订单和支付成功时，数据库能看到对应服务端事件。
- 上述 SQL 能返回非空统计结果。
- 埋点接口失败不影响排盘、聊天、支付主流程。

第二阶段验收：

- 管理后台可以按时间范围查看核心漏斗。
- 后台数据与 SQL 抽查结果一致。
- 可按 Web / 小程序 / 渠道拆分查看。

## 风险与注意事项

- 匿名用户清缓存后会生成新的 `anonymous_id`，无法跨设备识别，这是第一版可接受限制。
- 登录前后的匿名 ID 与用户 ID 需要在事件上同时保留，后续可以做身份合并。
- `properties` 不要存完整命盘、出生日期、用户输入的完整问题内容，避免隐私和合规风险。
- 事件上报要做异常吞掉，不能因为统计失败影响核心业务。
- 服务端成功事件比前端点击事件更可靠，核心指标应优先使用服务端成功事件。
- 事件量增长后需要定期归档或按月分区，第一版暂不处理。

## 建议实施顺序

1. 新增数据库表和 SQL 迁移文档。
2. 新增后端 `UserEvent` 模型、事件服务、上报接口。
3. Web 前端新增 `analytics.ts`，先接入排盘、聊天、定价、订单关键点。
4. 小程序新增 `analytics.ts`，接入首页、排盘、结果、聊天、反馈关键点。
5. 后端在订单、支付 webhook、反馈提交处补服务端事件。
6. 用测试账号跑完整流程，检查数据库事件链路。
7. 用 SQL 产出第一版指标。
8. 再决定是否进入后台可视化阶段。

## 工期估算

| 阶段 | 时间 | 说明 |
|---|---:|---|
| 第一阶段 | 0.5-1 天 | 能采集数据，能用 SQL 算指标 |
| 第二阶段 | 1-2 天 | 后台 API 和基础图表 |
| 第三阶段 | 2-3 天 | 渠道、实验、用户分层和精细分析 |

建议先做第一阶段，连续观察 3-7 天数据后，再决定后台图表和运营分析的优先级。
