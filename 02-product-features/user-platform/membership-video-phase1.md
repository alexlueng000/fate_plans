# 会员与视频学习第一阶段设计

日期：2026-06-18

范围：只做 Web + 后端，不做微信小程序。

## 已确认规则

- 39 元会员月卡，有效期 1 个月。
- 会员期内发放 100 次八字额度，对应 `user_quotas.quota_type = 'chat'`。
- 会员期内发放 100 次六爻额度，对应 `user_quotas.quota_type = 'liuyao_chat'`。
- 会员期内可观看会员视频。
- 超出八字或六爻次数后，购买对应叠加包。
- 叠加包第一版按固定 90 天有效期设计。
- 视频文件不进后端服务器、不进数据库、不进 Git；后续放腾讯云 VOD 或对象存储 + CDN。

## 第一阶段产物

迁移 SQL：

- `E:\claude_projects\chat\fate\migrations\009_membership_video_phase1.sql`
- `E:\claude_projects\chat\fate\migrations\009_rollback_membership_video_phase1.sql`

这次第一阶段只建立数据基础，不改业务接口。

执行前提：

- `products` 表已经存在。
- `orders` 表已经存在。
- `user_quotas` 表已经存在。
- 已执行到 `E:\claude_projects\chat\fate\migrations\006_add_product_multi_quota.sql`，因为本迁移会读取 `products.bazi_quota` 和 `products.liuyao_quota` 做兼容回填。

## 表结构策略

项目里已经有：

- `products`
- `orders`
- `payments`
- `user_quotas`

所以这次不新建独立的 `membership_plans` 和 `topup_packages`，而是复用 `products`：

- `products.kind = 'subscription'` 表示会员月卡。
- `products.kind = 'topup'` 表示叠加包。
- `product_grants` 表示某个商品购买成功后发放哪些额度。
- `user_memberships` 表示用户的会员有效期。
- `video_courses` / `video_lessons` 只存视频元数据。
- `video_watch_progress` 记录用户观看进度。

## 初始商品

```text
member_monthly_39
- 类型：subscription
- 周期：monthly
- 价格：3900 分
- 八字额度：100
- 六爻额度：100
- 视频权限：有

bazi_topup_50
- 类型：topup
- 价格：990 分
- 八字额度：50
- 有效期：90 天

liuyao_topup_50
- 类型：topup
- 价格：990 分
- 六爻额度：50
- 有效期：90 天
```

叠加包价格后续可以调整，第一阶段先用占位配置，关键是把数据结构定下来。

## 后续发放逻辑

支付成功后：

1. 查询订单对应的 `products`。
2. 如果是 `subscription`：
   - 创建或续期 `user_memberships`。
   - 读取 `product_grants`，发放 `chat = 100`、`liuyao_chat = 100`。
3. 如果是 `topup`：
   - 读取 `product_grants`，发放对应额度。
4. 发放额度继续使用现有 `QuotaService.add_quota()`，避免重复实现额度系统。

## 视频鉴权逻辑

视频列表可以公开返回课程和课时基础信息。

播放地址必须走后端鉴权：

```text
用户请求播放
↓
后端检查登录
↓
后端检查 user_memberships 是否存在 active 且 current_period_end > NOW()
↓
后端检查视频 access_level
↓
有效会员返回临时播放地址
```

会员视频未授权时返回：

```text
403 MEMBERSHIP_REQUIRED
```

未登录时返回：

```text
401 UNAUTHENTICATED
```

## 视频存储建议

正式环境推荐腾讯云 VOD：

- 大文件播放不经过 FastAPI。
- 支持转码。
- 支持 CDN。
- 支持防盗链和临时播放地址。
- 后续如果恢复小程序，也更容易复用。

第一版开发时可以临时使用 `video_lessons.source_url`，但只能通过 `/play` 鉴权后返回，不能直接在列表接口暴露给前端。

## 下一阶段

第二阶段建议做后端模型和服务：

- `E:\claude_projects\chat\fate\app\models\product_grant.py`
- `E:\claude_projects\chat\fate\app\models\membership.py`
- `E:\claude_projects\chat\fate\app\models\video.py`
- `E:\claude_projects\chat\fate\app\services\membership_service.py`
- `E:\claude_projects\chat\fate\app\services\video_service.py`

并把 `products` 发放逻辑从旧的 `bazi_quota` / `liuyao_quota` 逐步迁到 `product_grants`。
