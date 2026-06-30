# 网页端微信 Native 支付开发路线图

## 目标范围

第一版只做网页端真实支付，不接小程序支付、JSAPI 支付、支付宝。

支付方式：

- 微信 Native 扫码支付
- 用户在网页端选择套餐，系统生成微信支付二维码
- 用户扫码付款后，后端通过微信支付回调确认支付成功
- 后端自动发放八字对话和六爻次数
- 前端轮询订单状态，支付成功后刷新权益

商品规则：

| 商品 | 价格 | 有效期 | 权益 |
|---|---:|---|---|
| 免费用户 | 0 元 | 不自动刷新 | 八字对话 10 次，六爻 10 次 |
| 月付会员 | 39.9 元 | 30 天，续费顺延 | 八字对话 100 次，六爻 100 次 |
| 叠加包 | 20 元 | 跟随当前会员期；非会员购买默认 30 天 | 八字对话 50 次，六爻 50 次 |

当前实现里，会员顺延已经落地；但“叠加包跟随会员期过期”和“次数按批次过期”还需要新增额度批次表后才能严格实现。

## 当前已实现

后端已有基础能力：

- `products` 商品模型
- `orders` 订单模型
- `payments` 支付记录模型
- `user_memberships` 会员模型
- `user_quotas` 配额模型
- `usage_logs` 使用记录模型
- 模拟支付接口
- 微信支付回调基础逻辑
- 八字、六爻额度扣减入口

本轮已补齐：

- 微信 Native 下单接口：`POST /api/payments/wechat/native`
- 微信支付 API v3 请求签名
- 商户私钥读取配置
- 微信 Native `code_url` 返回
- 前端二维码展示
- 前端订单状态轮询
- 支付回调幂等处理，重复通知不会重复发放权益
- 支付金额校验，防止回调金额与订单金额不一致
- 免费额度默认值改为八字 10 次、六爻 10 次
- 商品种子改为 `monthly_3990` 和 `topup_2000`
- 原生 SQL 脚本：`E:\claude_projects\chat\fate\scripts\sql_web_native_payment_products.sql`

## 后端接口设计

### 商品与会员

| 接口 | 方法 | 作用 |
|---|---|---|
| `/api/membership/plans` | GET | 获取月付会员商品 |
| `/api/membership/topup-packages` | GET | 获取叠加包商品 |
| `/api/membership/me` | GET | 获取当前会员状态 |
| `/api/quota/me/all` | GET | 获取八字和六爻剩余额度 |

### 订单与支付

| 接口 | 方法 | 作用 |
|---|---|---|
| `/api/payments/wechat/native` | POST | 创建订单并发起微信 Native 下单 |
| `/api/orders/{order_id}` | GET | 查询订单状态 |
| `/api/webhooks/wechatpay` | POST | 微信支付异步通知 |

`POST /api/payments/wechat/native` 请求：

```json
{
  "product_code": "monthly_3990"
}
```

响应：

```json
{
  "order": {
    "id": 123,
    "status": "CREATED",
    "out_trade_no": "20260630120000ABCD1234",
    "amount_cents": 3990
  },
  "payment": {
    "id": 456,
    "channel": "WECHAT_NATIVE",
    "status": "PENDING"
  },
  "code_url": "weixin://wxpay/bizpayurl?pr=..."
}
```

## 支付流程

1. 用户进入会员页。
2. 前端调用 `/api/membership/plans` 和 `/api/membership/topup-packages` 获取商品。
3. 用户点击购买。
4. 前端调用 `/api/payments/wechat/native`。
5. 后端创建本地订单，状态为 `CREATED`。
6. 后端调用微信支付 Native 下单接口。
7. 后端保存支付记录，返回 `code_url`。
8. 前端把 `code_url` 渲染成二维码。
9. 用户用微信扫码支付。
10. 微信支付通知 `/api/webhooks/wechatpay`。
11. 后端验签、解密、校验金额。
12. 后端把订单标记为 `PAID`。
13. 后端按商品发放八字和六爻额度。
14. 前端轮询 `/api/orders/{order_id}`，发现 `PAID` 后刷新会员和额度状态。

权益发放只能以后端回调或主动查单结果为准，不能以前端二维码页状态为准。

## 环境变量

生产环境需要配置：

```env
WECHAT_PAY_MODE=prod
WECHAT_PAY_APPID=
WECHAT_PAY_MCHID=
WECHAT_PAY_MERCHANT_SERIAL_NO=
WECHAT_PAY_PRIVATE_KEY_PATH=
WECHAT_PAY_PRIVATE_KEY_PEM=
WECHAT_PAY_NOTIFY_URL=https://api.fateinsight.site/api/webhooks/wechatpay
WECHAT_API_V3_KEY=
WECHAT_PLATFORM_PUBLIC_KEY_PEM=
```

说明：

- `WECHAT_PAY_APPID`：微信支付绑定的 AppID。
- `WECHAT_PAY_MCHID`：微信支付商户号。
- `WECHAT_PAY_MERCHANT_SERIAL_NO`：商户 API 证书序列号。
- `WECHAT_PAY_PRIVATE_KEY_PATH`：商户私钥文件路径。
- `WECHAT_PAY_PRIVATE_KEY_PEM`：商户私钥 PEM 内容。和 `WECHAT_PAY_PRIVATE_KEY_PATH` 二选一。
- `WECHAT_PAY_NOTIFY_URL`：微信支付异步通知地址。
- `WECHAT_API_V3_KEY`：API v3 密钥，用于回调资源解密。
- `WECHAT_PLATFORM_PUBLIC_KEY_PEM`：微信支付平台公钥，用于验签。

私钥、API v3 密钥、平台公钥不能提交到 Git。

## 数据库执行

部署代码后执行：

```sql
SOURCE E:/claude_projects/chat/fate/scripts/sql_web_native_payment_products.sql;
```

该 SQL 会做三件事：

1. 插入或更新 `monthly_3990` 月付会员商品。
2. 插入或更新 `topup_2000` 叠加包商品。
3. 下架旧商品：`REPORT_UNLOCK`、`VIP_30D`、`basic_combo`、`premium_combo`。
4. 把仍处于免费无限额度的用户收敛为 10 次免费八字和 10 次免费六爻。

## 前端页面

第一版使用：

- `E:\claude_projects\chat\fate-frontend\app\membership\page.tsx`

页面包含：

- 当前会员状态
- 八字剩余额度
- 六爻剩余额度
- 月付会员商品
- 叠加包商品
- 微信支付二维码面板
- 自动订单状态轮询
- 支付成功后刷新权益

后续可以再把 `/pricing` 与 `/membership` 统一，避免两个购买入口长期维护两套文案和流程。

## 风险与待补能力

### 1. 主动查单

当前第一版依赖微信异步通知和前端轮询本地订单状态。生产环境建议补：

- `GET /api/payments/wechat/orders/{out_trade_no}/sync`
- 后端调用微信查单接口
- 如果微信返回已支付，但本地未入账，则补记支付成功并发放权益

用途：

- 回调通知延迟
- 回调通知丢失
- 用户支付成功但前端一直显示等待

### 2. 额度批次表

当前 `user_quotas` 是累计总额模型，适合第一版上线，但不能严格表达：

- 某一批额度何时过期
- 叠加包跟随会员期过期
- 非会员叠加包 30 天过期
- 退款后扣回指定批次额度

建议新增 `quota_grants`：

```sql
CREATE TABLE quota_grants (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    order_id BIGINT UNSIGNED NULL,
    product_id INT NULL,
    quota_type VARCHAR(50) NOT NULL,
    amount INT NOT NULL,
    used_amount INT NOT NULL DEFAULT 0,
    source VARCHAR(50) NOT NULL,
    expires_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_quota_grants_user_type_expire (user_id, quota_type, expires_at),
    INDEX ix_quota_grants_order (order_id)
);
```

扣减时按 `expires_at ASC` 消耗，先消耗最早过期的额度。

### 3. 退款

第一版可以不做自动退款，但后台至少要能查到：

- 订单号
- 微信交易号
- 支付金额
- 发放权益
- 已使用次数

后续退款策略建议：

- 未使用额度：允许退款并扣回额度
- 已部分使用：按业务规则人工处理
- 已全部使用：默认不支持退款

### 4. 后台订单管理

建议补后台页：

- 订单列表
- 支付状态
- 微信交易号
- 商品名称
- 用户信息
- 回调原文
- 手动查单
- 手动补发权益

## 推荐开发顺序

1. 配置微信商户号、证书、API v3 密钥和回调地址。
2. 执行商品和免费额度 SQL。
3. 部署后端支付代码。
4. 部署前端会员页。
5. 用开发模式测试订单创建、二维码展示、回调入账。
6. 切换 `WECHAT_PAY_MODE=prod`。
7. 做 0.01 或小额真实支付联调。
8. 验证微信后台订单、后端订单、前端权益三方一致。
9. 补主动查单接口。
10. 补后台订单管理。
11. 补额度批次表，严格实现额度过期。
12. 再考虑 JSAPI、H5 或支付宝。

## 验收清单

- 用户未登录时点击购买，会跳转登录。
- 用户登录后点击月卡，可以生成微信支付二维码。
- 用户登录后点击叠加包，可以生成微信支付二维码。
- 支付成功后，微信回调能把订单改为 `PAID`。
- 重复回调不会重复增加次数。
- 回调金额不一致时不会发放权益。
- 前端轮询到 `PAID` 后会刷新会员状态和额度。
- 免费新用户默认有 10 次八字和 10 次六爻。
- 月卡支付后增加 100 次八字和 100 次六爻。
- 叠加包支付后增加 50 次八字和 50 次六爻。
- 八字对话会扣 `chat`。
- 六爻会扣 `liuyao_chat`。
