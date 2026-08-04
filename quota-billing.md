# 用户提问次数收费模型 — 规划文档

## 2026-08-03 产品决策：去会员化，统一为次数包

### 决策结论

当前付费产品的核心权益主要是八字文化 AI 对话和六爻文化卦象解析的使用次数，不具备足够清晰的持续性会员价值。为降低用户理解成本，付费体系不再强调“会员”概念，统一调整为“次数包”或“次数中心”。

本次调整先保留八字与六爻两种独立额度，不立即合并成统一点数。待次数包模式稳定、获得真实使用比例与复购数据后，再评估是否将两类额度合并为通用点数。

### 调整原因

1. 当前基础版与高级版只有次数和有效期差异，本质上属于预付次数包。
2. “会员”容易让用户预期自动续费、每月恢复额度、专属折扣或持续内容服务，现有产品无法充分支撑这些预期。
3. 会员套餐与叠加包的定位重叠，且当前高级会员性价比明显高于叠加包，导致商品之间互相冲突。
4. 去会员化后，购买、使用和余额展示路径更直接，也便于后续增加新的次数商品。

### 第一阶段方案（推荐）

- 将“会员中心”改名为“次数中心”或“购买次数”。
- 将基础会员、高级会员改为不同档位的组合次数包。
- 所有新商品使用 `topup` 或一次性商品类型；支付成功后只发放额度，不再创建新的会员期限。
- 页面移除“会员状态”“会员到期时间”“开通会员”“续费”等表述。
- 额度卡明确显示“剩余 X 次”，同时补充总次数和已使用次数，避免 `0 / 10` 的含义不清。
- 已购买的存量会员权益继续保留至原到期日，不修改、不提前失效。
- 历史会员、订单、支付和退款记录继续保留，第一阶段不删除相关数据库表。

### 课程权限处理

当前系统并非完全只有次数差异，会员状态还被用于控制课程观看权限：

- `fate_backend/app/services/membership_service.py`：判断有效会员与课程权限。
- `fate_backend/app/services/video_service.py`：无有效会员时返回 `MEMBERSHIP_REQUIRED`。
- `fate_backend/app/models/membership.py`：保存会员状态和有效期。

去会员化时需要同步确定课程策略。第一阶段建议将现有课程免费开放；如果课程后续具有独立商业价值，则改为单独购买或单独内容权益，不再和次数包强绑定。

### 迁移与兼容策略

采用渐进迁移，不直接删除会员数据结构：

1. 下架旧的 `subscription` 商品，新增对应的次数包商品。
2. 新订单只发放八字、六爻额度，不调用会员创建或续期逻辑。
3. 老用户仍可通过现有会员记录使用权益至到期。
4. 退款逻辑继续识别历史会员订单和会员发放记录。
5. 等所有存量会员到期且退款观察期结束后，再评估删除会员路由、服务和数据表。

这种方式可以继续复用现有支付、订单、额度发放、额度流水和退款能力，避免一次性数据库迁移影响已付费用户。

### 预计工作量

| 范围 | 难度 | 预计时间 | 说明 |
|------|------|----------|------|
| 仅修改命名、页面结构和商品配置 | 低 | 0.5～1 天 | 保留后台会员结构，只对外去会员化 |
| 完成新旧商品兼容和课程权限调整 | 中 | 2～4 天 | 推荐实施范围，需覆盖支付、退款及存量用户 |
| 合并八字与六爻为统一点数 | 中偏高 | 3～5 天 | 涉及额度模型、扣减入口、余额迁移和退款追溯 |

### 第一阶段验收标准

1. 导航、首页、FAQ、定价页和购买页不再出现误导性的会员文案。
2. 次数中心正确显示八字与六爻的剩余、总计和已使用次数。
3. 购买任意新次数包后只增加对应额度，不产生新的会员记录或会员有效期。
4. 存量会员在原到期日前仍可正常使用已承诺权益。
5. 新旧订单支付回调保持幂等，重复回调不会重复发放额度。
6. 次数包退款只回收该订单尚未使用的额度，不影响其他订单发放的次数。
7. 课程权限按照最终选定策略执行，并移除与新次数包之间的隐性会员依赖。

### 第二阶段候选：统一点数

如后续数据表明用户经常出现某一类额度耗尽、另一类大量闲置，可将八字与六爻额度合并为通用点数：

- 八字 AI 对话按约定点数扣减。
- 六爻解析按约定点数扣减。
- 新人赠送、活动赠送和付费购买均进入统一余额。
- 新增紫微、姓名、流年等能力时可直接复用同一账户体系。

该阶段需要先确定历史余额换算规则和消耗优先级，不能与第一阶段同时仓促实施。

## Context

网站即将商业化，需要对用户的提问次数进行限制和收费。用户可以购买"提问次数包"，每次发起新对话（`/chat/start`）消耗 1 次，续聊（`/chat`）不消耗。

**好消息**：后端已经有完整的框架骨架（quota 模型、service、order 模型、支付路由、权益系统），核心逻辑已经接通。需要做的是：激活计费逻辑 + 补充产品配置 + 前端展示。

---

## 收费模型评估

### 模型选择：按次计费（非订阅制）

**为什么适合命理产品：**
- 用户使用频率天然低（一次完整解读可聊很久），订阅制会让用户感觉"交了钱用不上"
- 按次购买心理门槛低，容易冲动消费（"再买 10 次试试"）
- 续聊不消耗次数，用户可以深度探讨一次解读，体验感好
- 单次价值感强，适合高客单价定价

**推荐套餐设计：**
| 套餐 | 次数 | 价格 | 单次均价 | product_code |
|------|------|------|----------|--------------:|
| 体验包 | 5 次 | ¥9.9 | ¥1.98/次 | `chat_5` |
| 标准包 | 20 次 | ¥29.9 | ¥1.50/次 | `chat_20` |
| 超值包 | 50 次 | ¥59.9 | ¥1.20/次 | `chat_50` |
| 年度包 | 200 次 | ¥199 | ¥1.00/次 | `chat_200` |

**免费额度：**
- 新用户注册赠送 3 次（`source=free`）
- 目前内测阶段 `DEFAULT_FREE_QUOTA = -1`（无限），商业化时改为 3

---

## 现有代码状态

### 已有（无需新建）
- `fate/app/models/quota.py` — `UserQuota` 表（`total_quota`, `used_quota`, `period`, `source`）
- `fate/app/services/quota.py` — `QuotaService.check_and_consume()` 逻辑完整
- `fate/app/models/order.py` — `Order` 表
- `fate/app/services/entitlements.py` — `grant()` 幂等权益发放
- `fate/app/routers/payments.py` — `/prepay` 支付端点
- `fate/app/routers/chat.py` — quota 检查已接入 `chat_start`，仅需**激活**（改 default）

### 需要新建/修改
见下方实现路线。

---

## 实现路线（分阶段）

### 阶段一：后端激活计费

**1. 激活 quota 默认值**
- 文件：`fate/app/services/quota.py`
- 改 `DEFAULT_FREE_QUOTA = -1` → `DEFAULT_FREE_QUOTA = 3`
- `get_or_create_quota` 创建新用户 quota 时用此默认值

**2. 补充产品配置表**
- 新建 `fate/app/models/product.py`（或直接用配置字典）
- 字段：`product_code`, `name`, `price_fen`（分为单位）, `quota_amount`, `description`
- 初始可用硬编码字典，后期再做数据库化

**3. 补充订单创建端点**
- 文件：`fate/app/routers/orders.py`（已有或新建）
- `POST /api/orders` — 传入 `product_code`，创建 `Order` 记录，返回 `order_id`
- `GET /api/orders/{id}` — 查询订单状态

**4. 支付回调发放 quota**
- 文件：`fate/app/routers/webhooks.py`
- 微信支付成功回调时：调用 `QuotaService.add_quota(db, user_id, amount)` 增加次数
- `add_quota` 方法需在 `quota.py` service 里新增（目前只有 `check_and_consume`）

**5. 新增 quota 查询接口**
- 文件：`fate/app/routers/users.py` 或新增路由
- `GET /api/me/quota` — 返回 `{ total: int, used: int, remaining: int }`
- 供前端展示剩余次数

**6. 未登录用户限制**
- 文件：`fate/app/routers/chat.py`
- 目前未登录用户不检查 quota（内测放开）
- 商业化后：未登录用户给 1 次免费体验（session 级别，或要求登录后才能用）

---

### 阶段二：前端展示

**1. User 类型加 quota 字段**
- 文件：`fate-frontend/app/lib/auth.tsx`
- `User` 类型加 `quota_remaining?: number`
- 登录后顺带拉一次 `/api/me/quota` 存入 context

**2. 剩余次数展示**
- 文件：`fate-frontend/app/panel/page.tsx`
- 在输入框上方显示「剩余 X 次」badge
- 当剩余 ≤ 2 次时，显示橙色警告 + 「去购买」按钮

**3. 次数耗尽处理**
- 文件：`fate-frontend/app/panel/page.tsx` + `fate-frontend/app/lib/chat/sse.ts`
- 需识别 HTTP 429 状态码 → 显示专属提示："解读次数已用完，购买后继续"
- 拦截位置：`trySSE` 在 fetch 后检查 `res.status === 429`

**4. 购买页面**
- 新建 `fate-frontend/app/purchase/page.tsx`
- 展示套餐卡片，点击后：① 调 `POST /api/orders` 创建订单 → ② 调 `POST /api/payments/prepay` 拉起微信支付
- 支付成功后轮询订单状态，刷新剩余次数

---

### 阶段三：管理后台（可选）

- `fate-frontend/app/(auth)/admin/` 下新增 quota 管理页
- 支持手动给用户增减次数（调用 admin API）

---

## 关键文件路径汇总

| 文件 | 改动 |
|------|------|
| `fate/app/services/quota.py` | 改默认值、新增 `add_quota` 方法 |
| `fate/app/models/product.py` | 新建产品配置模型 |
| `fate/app/routers/orders.py` | 新建/完善订单端点 |
| `fate/app/routers/webhooks.py` | 支付回调发放 quota |
| `fate/app/routers/chat.py` | 未登录限制逻辑 |
| `fate-frontend/app/lib/auth.tsx` | User 类型加 quota 字段 |
| `fate-frontend/app/panel/page.tsx` | 剩余次数展示、429 处理 |
| `fate-frontend/app/purchase/page.tsx` | 新建购买页 |
| `fate-frontend/app/lib/chat/sse.ts` | 识别 429 状态 |

---

## 验证方式

1. 将 `DEFAULT_FREE_QUOTA` 改为 3，注册新用户，确认 quota 表插入 `total_quota=3`
2. 连续发起 3 次 `POST /api/chat/start`，第 4 次应返回 429
3. 前端显示「剩余 0 次」提示
4. 通过 admin 接口手动给用户加 5 次，确认可继续对话
5. 微信支付沙盒环境测试：回调触发后，`used_quota` 增加对应次数

---

## 不需要动的部分

- `QuotaService.check_and_consume` 核心逻辑 ✓
- JWT 认证体系 ✓
- SSE 流式响应 ✓
- 续聊（`/chat`）不消耗次数的设计 ✓（已正确实现）
