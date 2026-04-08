# 用户提问次数收费模型 — 规划文档

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
