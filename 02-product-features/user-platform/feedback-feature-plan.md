# 意见反馈功能实现计划

## 一、功能概述

为平台添加用户意见反馈功能，允许用户提交问题反馈、功能建议等，管理员可在后台查看和回复。

---

## 二、数据库设计

### 2.1 反馈表 (feedbacks)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| user_id | BIGINT UNSIGNED | 用户ID（可为空，支持匿名反馈） |
| type | VARCHAR(20) | 反馈类型：bug/feature/question/other |
| content | TEXT | 反馈内容 |
| contact | VARCHAR(100) | 联系方式（邮箱/手机） |
| status | VARCHAR(20) | 状态：pending/processing/resolved/closed |
| admin_reply | TEXT | 管理员回复内容 |
| replied_at | DATETIME | 回复时间 |
| replied_by | BIGINT UNSIGNED | 回复管理员ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2.2 SQL 建表语句

```sql
-- ============================================
-- 创建反馈表
-- 注意：user_id 和 replied_by 使用 BIGINT UNSIGNED 以匹配 users.id 类型
-- ============================================
CREATE TABLE IF NOT EXISTS feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id BIGINT UNSIGNED NULL COMMENT '用户ID（可为空，支持匿名）',
    type VARCHAR(20) NOT NULL DEFAULT 'other' COMMENT '反馈类型：bug/feature/question/other',
    content TEXT NOT NULL COMMENT '反馈内容',
    contact VARCHAR(100) NULL COMMENT '联系方式',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/processing/resolved/closed',
    admin_reply TEXT NULL COMMENT '管理员回复',
    replied_at DATETIME NULL COMMENT '回复时间',
    replied_by BIGINT UNSIGNED NULL COMMENT '回复管理员ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键约束
    CONSTRAINT fk_feedbacks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_feedbacks_admin FOREIGN KEY (replied_by) REFERENCES users(id) ON DELETE SET NULL,

    -- 索引
    INDEX idx_feedbacks_user_id (user_id),
    INDEX idx_feedbacks_status (status),
    INDEX idx_feedbacks_type (type),
    INDEX idx_feedbacks_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户反馈表';
```

### 2.3 查看表结构

```sql
DESCRIBE feedbacks;
```

---

## 三、后端实现

### 3.1 创建数据模型

**文件**: `fate/app/models/feedback.py`

```python
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Feedback(Base):
    """用户反馈表"""
    __tablename__ = "feedbacks"

    __table_args__ = (
        Index("idx_feedbacks_user_id", "user_id"),
        Index("idx_feedbacks_status", "status"),
        Index("idx_feedbacks_type", "type"),
        Index("idx_feedbacks_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="用户ID"
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="other", comment="反馈类型"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="反馈内容")
    contact: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="联系方式"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", comment="状态"
    )
    admin_reply: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="管理员回复"
    )
    replied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="回复时间"
    )
    replied_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="回复管理员ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联
    user = relationship("User", foreign_keys=[user_id], backref="feedbacks")
    admin = relationship("User", foreign_keys=[replied_by])
```

### 3.2 创建 API 路由

**文件**: `fate/app/routers/feedback.py`

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/feedback` | POST | 提交反馈 | 公开（可选登录） |
| `/api/feedback/my` | GET | 查看我的反馈 | 需登录 |
| `/api/admin/feedbacks` | GET | 管理员查看所有反馈 | 管理员 |
| `/api/admin/feedbacks/{id}` | GET | 查看反馈详情 | 管理员 |
| `/api/admin/feedbacks/{id}/reply` | POST | 回复反馈 | 管理员 |
| `/api/admin/feedbacks/{id}/status` | PUT | 更新反馈状态 | 管理员 |

### 3.3 注册路由

**文件**: `fate/main.py`

```python
from app.routers import feedback

app.include_router(feedback.router, prefix="/api", tags=["feedback"])
```

---

## 四、前端实现

### 4.1 修改反馈页面

**文件**: `fate-frontend/app/feedback/page.tsx`

- 接入真实 API `/api/feedback`
- 添加提交成功后的反馈 ID 显示

### 4.2 管理后台（可选）

**文件**: `fate-frontend/app/admin/feedbacks/page.tsx`

- 反馈列表（分页、筛选）
- 反馈详情查看
- 回复功能
- 状态更新

---

## 五、执行步骤

### 步骤 1: 执行 SQL 创建表

```bash
# 连接数据库
mysql -u root -p fate

# 执行建表语句
source /path/to/create_feedbacks.sql
```

或直接在 MySQL 客户端执行上面的 CREATE TABLE 语句。

### 步骤 2: 创建后端模型和路由

1. 创建 `fate/app/models/feedback.py`
2. 在 `fate/app/models/__init__.py` 中导入
3. 创建 `fate/app/routers/feedback.py`
4. 在 `fate/main.py` 中注册路由

### 步骤 3: 修改前端

1. 修改 `fate-frontend/app/feedback/page.tsx` 接入 API
2. （可选）创建管理后台页面

### 步骤 4: 测试

1. 测试提交反馈
2. 测试管理员查看和回复
3. 测试状态更新

---

## 六、状态流转

```
pending (待处理)
    ↓
processing (处理中)
    ↓
resolved (已解决) / closed (已关闭)
```

---

## 七、反馈类型说明

| 类型 | 说明 |
|------|------|
| bug | 问题反馈 - 功能异常、错误等 |
| feature | 功能建议 - 新功能需求 |
| question | 使用咨询 - 使用问题咨询 |
| other | 其他 - 其他类型反馈 |

---

## 八、预估工作量

| 任务 | 预估 |
|------|------|
| 数据库建表 | 5 分钟 |
| 后端模型 + 路由 | 30 分钟 |
| 前端接入 API | 15 分钟 |
| 管理后台页面（可选） | 1 小时 |
| 测试 | 15 分钟 |

---

## 九、后续扩展（可选）

1. **邮件通知**: 用户提交反馈后发送确认邮件
2. **管理员通知**: 新反馈时通知管理员
3. **反馈评分**: 用户对回复满意度评分
4. **附件上传**: 支持上传截图等附件
