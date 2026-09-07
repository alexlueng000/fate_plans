# 八字AI平台管理后台功能规划

---

# 一、管理后台功能规划

## 1.1 当前功能现状

| 功能模块 | 后端API | 前端页面 | 完成度 |
|----------|---------|----------|--------|
| 邀请码管理 | ✅ 完整 | ✅ 完整 | 100% |
| 敏感词管理 | ✅ 完整 | ✅ 完整 | 100% |
| 系统提示词 | ✅ 完整 | ✅ 完整 | 100% |
| 快捷按钮 | ✅ 完整 | ✅ 完整 | 100% |
| 知识库管理 | ✅ 基础 | ✅ 基础 | 80% |
| 反馈管理 | ✅ 完整 | ❌ 缺失 | 50% |
| **统计分析** | ❌ 缺失 | ❌ 缺失 | 0% |
| **用户管理** | ❌ 缺失 | ❌ 缺失 | 0% |
| 订单管理 | ❌ 缺失 | ❌ 缺失 | 0% |

## 1.2 需要新增的功能

### 优先级 P0：统计分析仪表盘

**核心指标（首页展示）：**
```
┌─────────────────────────────────────────────────────────────┐
│                    数据概览 Dashboard                        │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  总用户数   │  今日新增   │  活跃用户   │   总对话数      │
│    156      │    +12      │    45       │     892         │
├─────────────┴─────────────┴─────────────┴─────────────────┤
│                                                             │
│  📈 用户注册趋势（近30天折线图）                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  📊 用户来源分布        │  📊 对话量趋势                    │
│  [饼图: Web/小程序]     │  [柱状图: 近7天]                  │
└─────────────────────────────────────────────────────────────┘
```

**统计维度：**
1. **用户统计**
   - 总用户数、今日/本周/本月新增
   - 用户来源分布（Web / 小程序）
   - 用户注册趋势图（按日/周/月）
   - 活跃用户数（今日/7日/30日）

2. **对话统计**
   - 总对话数、今日对话数
   - 对话量趋势图
   - 平均每用户对话数

3. **消息统计**
   - 总消息数
   - Token 消耗统计（输入/输出）
   - 平均响应延迟

4. **邀请码统计**
   - 邀请码使用率
   - 注册转化率

5. **反馈统计**
   - 待处理反馈数
   - 反馈类型分布

### 优先级 P1：用户管理

**功能列表：**
1. 用户列表（搜索、筛选、分页）
2. 用户详情（基本信息、对话历史）
3. 用户状态管理（封禁/解封）
4. 管理员权限设置

### 优先级 P2：反馈管理前端

**功能列表：**
1. 反馈列表（筛选、分页）
2. 反馈详情
3. 回复反馈
4. 状态更新

---

## 1.3 统计分析 API 设计

### 后端 API 端点

```python
# fate/app/routers/admin_stats.py

# 1. 总览统计
GET /api/admin/stats/overview
Response:
{
    "users": {
        "total": 156,
        "today": 12,
        "this_week": 45,
        "this_month": 89
    },
    "conversations": {
        "total": 892,
        "today": 34
    },
    "messages": {
        "total": 5678,
        "tokens_used": 1234567
    },
    "feedbacks": {
        "pending": 5
    }
}

# 2. 用户趋势
GET /api/admin/stats/users/trend?period=30d
Response:
{
    "period": "30d",
    "data": [
        {"date": "2026-01-05", "count": 8},
        {"date": "2026-01-06", "count": 12},
        ...
    ]
}

# 3. 用户来源分布
GET /api/admin/stats/users/source
Response:
{
    "data": [
        {"source": "web", "count": 89},
        {"source": "miniapp", "count": 67}
    ]
}

# 4. 对话趋势
GET /api/admin/stats/conversations/trend?period=7d
Response:
{
    "period": "7d",
    "data": [
        {"date": "2026-01-28", "count": 45},
        ...
    ]
}

# 5. Token 消耗统计
GET /api/admin/stats/tokens?period=30d
Response:
{
    "total_prompt_tokens": 567890,
    "total_completion_tokens": 345678,
    "daily_average": 30456
}
```

### 数据库查询示例

```python
# 今日新增用户
SELECT COUNT(*) FROM users
WHERE DATE(created_at) = CURDATE();

# 用户注册趋势（近30天）
SELECT DATE(created_at) as date, COUNT(*) as count
FROM users
WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date;

# 用户来源分布
SELECT source, COUNT(*) as count
FROM users
GROUP BY source;

# 活跃用户（7天内有登录）
SELECT COUNT(*) FROM users
WHERE last_login_at >= DATE_SUB(NOW(), INTERVAL 7 DAY);

# Token 消耗统计
SELECT
    SUM(prompt_tokens) as total_prompt,
    SUM(completion_tokens) as total_completion
FROM messages;
```

---

## 1.4 用户管理 API 设计

```python
# fate/app/routers/admin_users.py

# 1. 用户列表
GET /api/admin/users?page=1&size=20&search=xxx&status=1&source=web
Response:
{
    "total": 156,
    "page": 1,
    "size": 20,
    "items": [
        {
            "id": 1,
            "email": "user@example.com",
            "nickname": "用户昵称",
            "source": "web",
            "status": 1,
            "is_admin": false,
            "created_at": "2026-01-15T10:30:00",
            "last_login_at": "2026-02-01T14:20:00",
            "conversation_count": 12
        },
        ...
    ]
}

# 2. 用户详情
GET /api/admin/users/{user_id}
Response:
{
    "id": 1,
    "email": "user@example.com",
    "phone": "138****1234",
    "nickname": "用户昵称",
    "avatar_url": "...",
    "source": "web",
    "status": 1,
    "is_admin": false,
    "created_at": "2026-01-15T10:30:00",
    "last_login_at": "2026-02-01T14:20:00",
    "last_login_ip": "192.168.1.1",
    "stats": {
        "conversation_count": 12,
        "message_count": 89,
        "tokens_used": 12345
    }
}

# 3. 修改用户状态
PATCH /api/admin/users/{user_id}/status
Body: {"status": 0}  # 0=封禁, 1=正常

# 4. 设置管理员
PATCH /api/admin/users/{user_id}/admin
Body: {"is_admin": true}

# 5. 用户对话列表
GET /api/admin/users/{user_id}/conversations?page=1&size=10
```

---

## 1.5 前端页面设计

### 管理后台导航结构

```
/admin
├── /admin/dashboard          # 数据概览（新增）⭐
├── /admin/users              # 用户管理（新增）⭐
│   └── /admin/users/[id]     # 用户详情
├── /admin/feedbacks          # 反馈管理（新增）⭐
├── /admin/invitation-codes   # 邀请码管理（已有）
├── /admin/sensitive-words    # 敏感词管理（已有）
└── /admin/config
    ├── /system_prompt        # 系统提示词（已有）
    ├── /quick_buttons        # 快捷按钮（已有）
    └── /knowledge_base       # 知识库（已有）
```

### Dashboard 页面组件

```typescript
// fate-frontend/app/(auth)/admin/dashboard/page.tsx

// 使用的图表库：recharts（已在 package.json 中）
// 或者使用轻量级的 chart.js

// 组件结构：
// 1. StatCard - 统计卡片（总用户、今日新增等）
// 2. LineChart - 用户注册趋势
// 3. PieChart - 用户来源分布
// 4. BarChart - 对话量趋势
```

---

## 1.6 确定的实施计划：统计分析仪表盘

### 技术选型确认
- **图表库**：recharts
- **实施范围**：仅统计分析仪表盘（P0）

### 实施步骤

#### 步骤1：后端统计 API
**新增文件**：`fate/app/routers/admin_stats.py`

实现以下 API：
1. `GET /api/admin/stats/overview` - 总览统计
2. `GET /api/admin/stats/users/trend` - 用户注册趋势
3. `GET /api/admin/stats/users/source` - 用户来源分布
4. `GET /api/admin/stats/conversations/trend` - 对话趋势

#### 步骤2：注册路由
**修改文件**：`fate/main.py`
- 导入并注册 `admin_stats` 路由

#### 步骤3：安装图表库
```bash
cd fate-frontend
npm install recharts
```

#### 步骤4：创建 Dashboard 页面
**新增文件**：`fate-frontend/app/(auth)/admin/dashboard/page.tsx`

组件结构：
- StatCard 组件（4个统计卡片）
- LineChart 组件（用户注册趋势）
- PieChart 组件（用户来源分布）
- BarChart 组件（对话量趋势）

#### 步骤5：更新管理后台导航
**修改文件**：`fate-frontend/app/(auth)/admin/page.tsx`
- 添加 Dashboard 入口链接
- 将 Dashboard 设为默认首页

### 验证方式
1. 启动后端：`cd fate && uvicorn main:app --reload`
2. 启动前端：`cd fate-frontend && npm run dev`
3. 访问 `/admin/dashboard` 查看统计数据
4. 验证各项数据与数据库一致

### 后续扩展（暂不实施）
- 用户管理功能（P1）
- 反馈管理前端（P2）
- 订单管理功能

---

## 1.7 技术选型

### 图表库选择

| 库 | 优点 | 缺点 | 推荐度 |
|----|------|------|--------|
| recharts | React 原生、声明式、文档好 | 包体积较大 | ⭐⭐⭐⭐⭐ |
| chart.js | 轻量、功能全 | 需要 react-chartjs-2 封装 | ⭐⭐⭐⭐ |
| echarts | 功能强大、中文友好 | 包体积大 | ⭐⭐⭐ |

**推荐**：recharts（React 生态友好，API 简洁）

### 安装命令

```bash
cd fate-frontend
npm install recharts
```