# 消息评价功能改进计划

## 概述

改进 AI 消息的点赞/点踩功能，增强用户反馈体验。

**创建日期**: 2026-03-04
**状态**: 进行中

---

## 已完成的改进

### 1. 基础功能实现 ✅

- [x] 后端 API 实现（`/api/chat/messages/{message_id}/rating`）
- [x] 前端评价按钮组件（`MessageRating.tsx`）
- [x] 点踩原因选择弹窗（`DownvoteReasonModal.tsx`）
- [x] 数据库模型（`MessageRating`）

### 2. 消息 ID 传递 ✅

**问题**: 前端无法显示评价按钮，因为消息缺少 `messageId`

**解决方案**:
- 修改后端 `_save_db_message()` 函数，返回消息 ID
- 在 SSE 流中发送 `message_id` 元数据
- 前端接收并保存到消息的 `meta.messageId` 字段

**修改文件**:
- `fate/app/chat/service.py`
- `fate-frontend/app/panel/page.tsx`
- `fate-frontend/app/lib/chat/types.ts`

### 3. 视觉反馈增强 ✅

**改进**:
- 点赞后：金色背景（20% 透明度）+ 填充图标 + 阴影
- 点踩后：红色背景（20% 透明度）+ 填充图标 + 阴影
- 已评价状态更明显

**修改文件**:
- `fate-frontend/app/components/chat/MessageRating.tsx`

### 4. 点踩限制 ✅

**功能**: 点踩后不能重复点击

**实现**:
- 点踩后按钮变为禁用状态
- 添加 `cursor-not-allowed` 样式
- 点击已点踩的按钮不会再打开弹窗

---

## 待完成的改进

### 5. 自定义理由输入 🚧

**需求**: 当用户选择"其他"原因时，提供文本输入框，要求至少 15 个字

**前端实现** ✅:
- [x] 添加 `customReason` 状态
- [x] 显示 textarea 输入框（选择"其他"时）
- [x] 字数统计显示（x / 15 字）
- [x] 验证至少 15 个字
- [x] 错误提示

**后端调整** ⏳:
- [ ] 数据库迁移：扩展 `reason` 字段长度
- [ ] 修改 API 接收自定义理由文本

**修改文件**:
- `fate-frontend/app/components/chat/DownvoteReasonModal.tsx` ✅
- `fate/app/models/message_rating.py` ⏳
- `fate/app/schemas/message_rating.py` ⏳

---

## 数据库迁移

### 迁移说明

**目标**: 扩展 `message_ratings.reason` 字段长度，支持自定义理由文本

**当前结构**:
```sql
reason VARCHAR(50) NULL
```

**目标结构**:
```sql
reason VARCHAR(500) NULL
```

### 迁移 SQL

```sql
-- ============================================
-- 消息评价功能改进 - 扩展理由字段长度
-- 创建时间: 2026-03-04
-- 说明: 支持用户输入自定义点踩理由（最多 500 字符）
-- ============================================

-- 1. 扩展 reason 字段长度
ALTER TABLE message_ratings
MODIFY COLUMN reason VARCHAR(500) NULL
COMMENT '点踩原因：预设选项或自定义文本（最多500字符）';

-- 2. 验证修改
DESCRIBE message_ratings;

-- 3. 回滚 SQL（如需要）
-- ALTER TABLE message_ratings
-- MODIFY COLUMN reason VARCHAR(50) NULL;
```

### 执行步骤

1. **备份数据库**（生产环境必须）:
```bash
mysqldump -u fate_app -p fate > backup_fate_$(date +%Y%m%d_%H%M%S).sql
```

2. **执行迁移**:
```bash
mysql -u fate_app -p fate < migration.sql
```

3. **验证结果**:
```sql
SHOW COLUMNS FROM message_ratings WHERE Field = 'reason';
```

预期输出:
```
+--------+--------------+------+-----+---------+-------+
| Field  | Type         | Null | Key | Default | Extra |
+--------+--------------+------+-----+---------+-------+
| reason | varchar(500) | YES  |     | NULL    |       |
+--------+--------------+------+-----+---------+-------+
```

---

## API 调整

### 前端请求格式

**当前**:
```typescript
{
  rating_type: 'down',
  reason: 'inaccurate',  // 预设选项
  paipan_data?: Paipan
}
```

**改进后**:
```typescript
{
  rating_type: 'down',
  reason: 'other',  // 选择"其他"
  custom_reason: '这里是用户输入的自定义理由，至少15个字...',  // 新增字段
  paipan_data?: Paipan
}
```

### 后端处理逻辑

**文件**: `fate/app/routers/message_rating.py`

**修改**:
```python
# 1. 更新 Schema
class MessageRatingCreate(BaseModel):
    rating_type: RatingType
    reason: Optional[RatingReason] = None
    custom_reason: Optional[str] = None  # 新增
    paipan_data: Optional[dict] = None

# 2. 保存逻辑
if req.reason == 'other' and req.custom_reason:
    # 保存自定义理由到 reason 字段
    existing_rating.reason = req.custom_reason[:500]  # 截断到 500 字符
else:
    # 保存预设选项
    existing_rating.reason = req.reason
```

---

## 前端完整实现

### DownvoteReasonModal 组件

**关键功能**:
1. 选择预设原因或"其他"
2. 选择"其他"时显示输入框
3. 验证自定义理由至少 15 个字
4. 字数实时统计
5. 错误提示
6. 提交后重置状态

**状态管理**:
```typescript
const [selectedReason, setSelectedReason] = useState<RatingReason | null>(null);
const [customReason, setCustomReason] = useState('');
const [error, setError] = useState('');
```

**验证逻辑**:
```typescript
if (selectedReason === 'other') {
  const trimmed = customReason.trim();
  if (trimmed.length < 15) {
    setError('请输入至少15个字的理由');
    return;
  }
}
```

**提交按钮禁用条件**:
```typescript
disabled={
  !selectedReason ||
  isSubmitting ||
  (selectedReason === 'other' && customReason.trim().length < 15)
}
```

---

## 测试计划

### 前端测试

- [ ] 点赞功能：点击后图标变金色并填充
- [ ] 点踩功能：点击后打开弹窗
- [ ] 预设原因：选择后可以直接提交
- [ ] 自定义理由：
  - [ ] 选择"其他"后显示输入框
  - [ ] 字数统计正确显示
  - [ ] 少于 15 字时提交按钮禁用
  - [ ] 少于 15 字时显示错误提示
  - [ ] 达到 15 字后可以提交
- [ ] 提交后：
  - [ ] 弹窗关闭
  - [ ] 按钮状态更新
  - [ ] 不能重复点踩

### 后端测试

- [ ] API 接收自定义理由
- [ ] 自定义理由正确保存到数据库
- [ ] 理由长度超过 500 字符时正确截断
- [ ] 查询评价时正确返回自定义理由

### 数据库测试

- [ ] 字段长度扩展成功
- [ ] 现有数据不受影响
- [ ] 可以保存 500 字符的理由
- [ ] 回滚 SQL 可以正常执行

---

## 部署清单

### 开发环境

1. [ ] 执行数据库迁移 SQL
2. [ ] 更新后端代码
3. [ ] 更新前端代码
4. [ ] 重启后端服务
5. [ ] 重新构建前端
6. [ ] 功能测试

### 生产环境

1. [ ] 备份数据库
2. [ ] 在维护窗口执行迁移
3. [ ] 部署后端代码
4. [ ] 部署前端代码
5. [ ] 验证功能正常
6. [ ] 监控错误日志

---

## 未来优化

1. **评价统计**：
   - 统计每条消息的点赞/点踩数量
   - 管理后台展示评价数据
   - 分析常见点踩原因

2. **评价管理**：
   - 用户可以修改或撤销评价
   - 管理员可以查看所有评价
   - 导出评价数据用于分析

3. **AI 改进**：
   - 根据点踩原因优化提示词
   - 识别常见问题并改进
   - A/B 测试不同的提示词策略

4. **用户反馈闭环**：
   - 点踩后提供改进建议
   - 用户可以看到问题是否被修复
   - 通知用户相关改进

---

## 相关文件

### 后端
- `fate/app/models/message_rating.py` - 数据模型
- `fate/app/routers/message_rating.py` - API 路由
- `fate/app/schemas/message_rating.py` - 请求/响应 Schema
- `fate/app/chat/service.py` - 消息保存逻辑

### 前端
- `fate-frontend/app/components/chat/MessageRating.tsx` - 评价按钮
- `fate-frontend/app/components/chat/DownvoteReasonModal.tsx` - 点踩弹窗
- `fate-frontend/app/components/chat/MessageList.tsx` - 消息列表
- `fate-frontend/app/lib/chat/rating.ts` - 评价 API 客户端
- `fate-frontend/app/lib/chat/types.ts` - 类型定义
- `fate-frontend/app/panel/page.tsx` - 主页面

---

## 参考资料

- [消息评价 API 文档](../fate/app/routers/message_rating.py)
- [排盘逻辑文档](./paipan-logic.md)
- [CLAUDE.md 开发规范](../CLAUDE.md)
