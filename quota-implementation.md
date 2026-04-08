# Quota 计费系统实现说明

## 已完成的工作

### 1. 后端核心功能

#### 新增文件：
- `app/models/product.py` - 商品模型（提问次数包）
- `app/routers/quota.py` - Quota 查询接口
- `app/test/test_quota.py` - 完整的模拟测试脚本
- `scripts/create_products_table.py` - 数据库表创建脚本

#### 修改文件：
- `app/services/quota.py` - 添加 `add_quota()` 方法用于购买后发放配额
- `app/models/__init__.py` - 导出 Product 模型

### 2. 商品套餐配置

| 套餐 | 次数 | 价格 | 单次均价 | product_code |
|------|------|------|----------|--------------|
| 体验包 | 5 次 | ¥9.9 | ¥1.98/次 | `chat_5` |
| 标准包 | 20 次 | ¥29.9 | ¥1.50/次 | `chat_20` |
| 超值包 | 50 次 | ¥59.9 | ¥1.20/次 | `chat_50` |
| 年度包 | 200 次 | ¥199 | ¥1.00/次 | `chat_200` |

### 3. 核心 API 端点

- `GET /api/quota/me` - 查询当前用户剩余次数
- `POST /api/orders` - 创建订单（已存在）
- `GET /api/orders/{id}` - 查询订单状态（已存在）

### 4. 关键服务方法

```python
# 检查并消费配额（已有）
QuotaService.check_and_consume(db, user_id, "chat", amount=1)

# 增加配额（新增）
QuotaService.add_quota(db, user_id, amount, "chat", "purchase")

# 设置配额（已有，用于管理员操作）
QuotaService.set_user_quota(db, user_id, "chat", total_quota, "never", "admin_grant")
```

## 数据库准备

### 创建 products 表

```sql
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '商品编码',
    name VARCHAR(100) NOT NULL COMMENT '商品名称',
    price_cents INT NOT NULL COMMENT '价格（分）',
    currency VARCHAR(8) NOT NULL DEFAULT 'CNY' COMMENT '币种',
    quota_amount INT NOT NULL COMMENT '提供的提问次数',
    description VARCHAR(500) NULL COMMENT '商品描述',
    active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否在售',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_code (code),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';
```

### 插入初始商品数据

```sql
INSERT INTO products (code, name, price_cents, quota_amount, description, active)
VALUES
    ('chat_5', '体验包', 990, 5, '5次提问，适合新用户体验', TRUE),
    ('chat_20', '标准包', 2990, 20, '20次提问，日常使用', TRUE),
    ('chat_50', '超值包', 5990, 50, '50次提问，深度探索', TRUE),
    ('chat_200', '年度包', 19900, 200, '200次提问，全年无忧', TRUE)
ON DUPLICATE KEY UPDATE name=name;
```

### 或使用脚本自动创建

```bash
cd fate
python scripts/create_products_table.py
```

## 如何运行测试

### 方式 1：完整模拟测试（推荐）

```bash
cd fate

# 1. 创建 products 表（二选一）
# 方式 A: 使用脚本
python scripts/create_products_table.py

# 方式 B: 手动执行上面的 SQL

# 2. 运行完整测试
python app/test/test_quota.py
```

测试脚本会自动：
- 创建测试用户
- 初始化商品数据
- 模拟完整购买流程
- 测试配额消费
- 测试配额耗尽（返回 429）
- 测试多次购买累加

### 方式 2：手动测试 API

```bash
# 1. 启动后端
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. 登录获取 token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# 3. 查询剩余次数
curl http://localhost:8000/api/quota/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. 开始对话（消耗 1 次）
curl -X POST http://localhost:8000/api/chat/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"paipan":{...}}'

# 5. 配额耗尽时会返回 429
# {"detail":"配额已用完：配额不足，剩余 0 次"}
```

## 验证数据库状态

### 查看商品列表

```sql
SELECT * FROM products;
```

### 查看用户配额

```sql
SELECT u.id, u.email, uq.quota_type, uq.total_quota, uq.used_quota, 
       (uq.total_quota - uq.used_quota) as remaining, uq.source
FROM users u
LEFT JOIN user_quotas uq ON u.id = uq.user_id
WHERE u.email = 'test_quota@example.com';
```

### 查看订单记录

```sql
SELECT o.id, o.user_id, o.product_id, p.name as product_name, 
       o.amount_cents, o.status, o.created_at
FROM orders o
JOIN products p ON o.product_id = p.id
ORDER BY o.created_at DESC
LIMIT 10;
```

### 手动给用户增加配额（测试用）

```sql
-- 方式 1: 直接更新 total_quota
UPDATE user_quotas 
SET total_quota = total_quota + 20 
WHERE user_id = 1 AND quota_type = 'chat';

-- 方式 2: 重置配额为指定值
UPDATE user_quotas 
SET total_quota = 50, used_quota = 0, source = 'admin_grant'
WHERE user_id = 1 AND quota_type = 'chat';

-- 方式 3: 设置为无限制（内测模式）
UPDATE user_quotas 
SET total_quota = -1, used_quota = 0, source = 'internal_test'
WHERE user_id = 1 AND quota_type = 'chat';
```

## 激活计费（生产环境）

### 修改默认配额

编辑 `app/services/quota.py`:

```python
# 改为 3 次免费额度
DEFAULT_FREE_QUOTA = 3  # 原来是 -1（无限制）
```

### 未登录用户限制

编辑 `app/routers/chat.py` 的 `chat_start` 函数：

```python
# 当前：未登录用户可以使用
if user_id:
    allowed, msg, remaining = QuotaService.check_and_consume(db, user_id, "chat")
    
# 改为：未登录用户必须登录
if not user_id:
    raise HTTPException(status_code=401, detail="请先登录")
    
allowed, msg, remaining = QuotaService.check_and_consume(db, user_id, "chat")
```

## 支付回调集成

需要在支付成功回调中调用：

```python
# app/routers/webhooks.py (需要创建或修改)
from app.services.quota import QuotaService

@router.post("/wechat/callback")
def wechat_payment_callback(request: Request, db: Session = Depends(get_db_tx)):
    # 1. 验证微信签名
    # 2. 解析支付结果
    # 3. 更新订单状态
    order.status = "PAID"
    db.commit()
    
    # 4. 发放配额
    product = db.query(Product).filter(Product.id == order.product_id).first()
    if product:
        QuotaService.add_quota(
            db, 
            order.user_id, 
            product.quota_amount, 
            "chat", 
            "purchase"
        )
    
    return {"code": "SUCCESS"}
```

## 前端集成要点

### 1. 显示剩余次数

```typescript
// 调用 GET /api/quota/me
const quota = await api.get('/quota/me');
// { total: 20, used: 5, remaining: 15, is_unlimited: false }
```

### 2. 处理 429 错误

```typescript
// 在 SSE 或 fetch 中捕获
if (response.status === 429) {
  showMessage("提问次数已用完，请购买套餐");
  router.push('/purchase');
}
```

### 3. 购买流程

```typescript
// 1. 创建订单
const order = await api.post('/orders', { product_code: 'chat_20' });

// 2. 发起支付
const payment = await api.post('/payments/prepay', { 
  order_id: order.id 
});

// 3. 拉起微信支付
wx.requestPayment(payment.params);

// 4. 支付成功后轮询订单状态
const checkOrder = setInterval(async () => {
  const updated = await api.get(`/orders/${order.id}`);
  if (updated.status === 'PAID') {
    clearInterval(checkOrder);
    // 刷新 quota
    refreshQuota();
  }
}, 2000);
```

## 测试场景覆盖

✓ 新用户注册（默认 3 次或无限制）
✓ 消费配额（每次 /chat/start 消耗 1 次）
✓ 续聊不消耗（/chat 不扣次数）
✓ 配额耗尽返回 429
✓ 购买后发放配额
✓ 多次购买累加
✓ 从无限制切换到有限制
✓ 管理员手动调整配额

## 常见问题排查

### 问题 1: 测试脚本报错 "Table 'products' doesn't exist"

**解决方案：**
```bash
# 先创建表
python scripts/create_products_table.py

# 或手动执行 SQL（见上方"数据库准备"章节）
```

### 问题 2: 用户配额一直是无限制（-1）

**原因：** `DEFAULT_FREE_QUOTA = -1`（内测模式）

**解决方案：**
```python
# 编辑 app/services/quota.py
DEFAULT_FREE_QUOTA = 3  # 改为 3 次免费额度
```

### 问题 3: 购买后配额没有增加

**排查步骤：**
```sql
-- 1. 检查订单状态
SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 1;

-- 2. 检查商品配置
SELECT * FROM products WHERE code = 'chat_20';

-- 3. 检查配额记录
SELECT * FROM user_quotas WHERE user_id = ?;

-- 4. 手动发放配额（测试）
UPDATE user_quotas 
SET total_quota = total_quota + 20 
WHERE user_id = ? AND quota_type = 'chat';
```

### 问题 4: 前端调用 /api/quota/me 返回 404

**原因：** 路由未注册

**解决方案：**
```python
# 在 main.py 中添加
from app.routers import quota

app.include_router(quota.router, prefix="/api")
```

### 问题 5: 测试时想重置所有配额

**SQL 脚本：**
```sql
-- 重置所有用户配额为 3 次
UPDATE user_quotas SET total_quota = 3, used_quota = 0, source = 'free';

-- 或删除所有配额记录（下次访问会自动创建）
DELETE FROM user_quotas;

-- 删除测试订单
DELETE FROM orders WHERE user_id IN (
    SELECT id FROM users WHERE email LIKE '%test%'
);
```

## 注意事项

1. **事务安全**：所有 quota 操作都在事务中，避免并发问题
2. **幂等性**：`add_quota` 可以多次调用，配额会累加
3. **无限制模式**：`total_quota = -1` 表示无限制，适合内测
4. **续聊不扣费**：只有 `/chat/start` 消耗配额，`/chat` 不消耗
5. **429 状态码**：前端需要特殊处理，引导用户购买

## 下一步工作

- [ ] 前端购买页面 (`fate-frontend/app/purchase/page.tsx`)
- [ ] 前端剩余次数显示
- [ ] 微信支付回调处理
- [ ] 管理后台配额管理
- [ ] 微信小程序购买流程
