# 对话次数统计与配额管理功能实现计划

## 功能目标

1. **统计展示**：管理员可查看用户对话次数统计
2. **配额管理**：支持限制用户对话次数（当前内测阶段设为无限制）
3. **聊天持久化**：修复当前内存存储问题，将对话和消息持久化到数据库

---

## 第一阶段：数据库模型

### 1.1 创建 `UserQuota` 模型
**文件**: `fate/app/models/quota.py`

```python
class UserQuota(Base):
    __tablename__ = "user_quotas"

    id: int (PK)
    user_id: int (FK -> users.id)
    quota_type: str  # "chat", "report" 等
    total_quota: int  # -1 = 无限制
    used_quota: int   # 已使用次数
    period: str       # "daily" / "monthly" / "never"
    last_reset_at: datetime
    source: str       # "free" / "paid" / "admin_grant"
    created_at, updated_at: datetime
```

### 1.2 创建 `UsageLog` 模型（可选，用于详细审计）
**文件**: `fate/app/models/usage_log.py`

```python
class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: int (PK)
    user_id: int (FK)
    usage_type: str  # "chat_start", "chat_send"
    conversation_id: int (FK, nullable)
    prompt_tokens, completion_tokens: int
    created_at: datetime
```

### 1.3 更新模型导出
**文件**: `fate/app/models/__init__.py` - 添加新模型导出

### 1.4 生成数据库迁移
```bash
alembic revision --autogenerate -m "add user_quotas and usage_logs tables"
alembic upgrade head
```

### 1.5 SQL 建表语句（手动执行或参考）

```sql
-- 用户配额表
CREATE TABLE user_quotas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    quota_type VARCHAR(50) NOT NULL DEFAULT 'chat' COMMENT '配额类型: chat, report 等',
    total_quota INT NOT NULL DEFAULT -1 COMMENT '总配额, -1 表示无限制',
    used_quota INT NOT NULL DEFAULT 0 COMMENT '已使用次数',
    period VARCHAR(20) NOT NULL DEFAULT 'never' COMMENT '重置周期: daily, monthly, never',
    last_reset_at DATETIME DEFAULT NULL COMMENT '上次重置时间',
    source VARCHAR(50) NOT NULL DEFAULT 'free' COMMENT '来源: free, paid, admin_grant',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_quotas_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_quota_type (user_id, quota_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户配额表';

-- 使用日志表（可选，用于详细审计）
CREATE TABLE usage_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    usage_type VARCHAR(50) NOT NULL COMMENT '使用类型: chat_start, chat_send',
    conversation_id INT DEFAULT NULL COMMENT '关联的对话ID',
    prompt_tokens INT NOT NULL DEFAULT 0 COMMENT '输入 token 数',
    completion_tokens INT NOT NULL DEFAULT 0 COMMENT '输出 token 数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usage_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_usage_logs_conv FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    INDEX idx_usage_logs_user_time (user_id, created_at),
    INDEX idx_usage_logs_type (usage_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='使用日志表';

-- 为现有用户初始化配额（内测阶段，无限制）
INSERT INTO user_quotas (user_id, quota_type, total_quota, used_quota, period, source)
SELECT id, 'chat', -1, 0, 'never', 'free'
FROM users
WHERE id NOT IN (SELECT user_id FROM user_quotas WHERE quota_type = 'chat');
```

---

## 第二阶段：聊天持久化

### 2.1 修改 `start_chat()` 函数
**文件**: `fate/app/chat/service.py`

修改内容：
1. 添加 `user_id: int` 和 `db: Session` 参数
2. 创建数据库 `Conversation` 记录
3. 使用数据库 ID 作为内存存储的 key（替代 UUID）
4. 在流式完成后持久化消息到数据库

```python
def start_chat(paipan, kb_index_dir, kb_topk, request, user_id: int, db: Session):
    # 1. 创建数据库对话记录
    db_conv = Conversation(user_id=user_id, title="八字解读")
    db.add(db_conv)
    db.commit()

    # 2. 使用数据库 ID 作为内存 key
    cid = str(db_conv.id)
    set_conv(cid, {"pinned": ..., "history": [], ...})

    # 3. 流式完成后保存消息
    # finally 块中调用 create_message()
```

### 2.2 修改 `send_chat()` 函数
**文件**: `fate/app/chat/service.py`

修改内容：
1. 添加 `user_id: int` 和 `db: Session` 参数
2. 在流式完成后持久化消息到数据库

### 2.3 修改路由层
**文件**: `fate/app/routers/chat.py`

修改内容：
1. 添加认证依赖 `get_current_user_optional` 或 `get_current_user`
2. 传递 `user_id` 和 `db` 到服务函数

```python
@router.post("/start")
def chat_start(
    req: ChatStartReq,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)  # 可选认证
):
    user_id = current_user.id if current_user else None
    result = start_chat(..., user_id=user_id, db=db)
```

### 2.4 扩展 `chat_store.py`
**文件**: `fate/app/services/chat_store.py`

添加函数：
- `create_conversation(db, user_id, title)` - 创建对话记录
- `save_message(db, conversation_id, user_id, role, content, tokens)` - 保存消息

---

## 第三阶段：配额服务

### 3.1 创建 `QuotaService`
**文件**: `fate/app/services/quota.py`

```python
class QuotaService:
    DEFAULT_FREE_QUOTA = -1  # 内测阶段无限制

    @staticmethod
    def get_or_create_quota(db, user_id, quota_type="chat") -> UserQuota

    @staticmethod
    def check_and_consume(db, user_id, quota_type="chat", amount=1) -> (bool, str, int)
        # 返回: (是否允许, 消息, 剩余次数)

    @staticmethod
    def get_user_stats(db, user_id) -> dict
        # 返回用户统计信息

    @staticmethod
    def reset_quota_if_needed(db, quota) -> None
        # 根据 period 重置配额
```

### 3.2 集成配额检查到聊天流程
**文件**: `fate/app/chat/service.py`

在 `start_chat()` 开头添加：
```python
if user_id:
    allowed, msg, remaining = QuotaService.check_and_consume(db, user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="配额已用完")
```

---

## 第四阶段：统计 API

### 4.1 用户端 API
**文件**: `fate/app/routers/user_stats.py` (新建)

```python
@router.get("/user/quota")
def get_my_quota(db, current_user):
    """获取当前用户配额信息"""

@router.get("/user/usage")
def get_my_usage(db, current_user):
    """获取当前用户使用统计"""
```

### 4.2 管理员 API
**文件**: `fate/app/routers/admin_stats.py` (扩展)

```python
@router.get("/admin/users/{user_id}/stats")
def get_user_stats(user_id, db, admin):
    """获取指定用户的详细统计"""

@router.get("/admin/users/ranking")
def get_users_ranking(limit, order_by, db, admin):
    """获取用户使用排行榜"""

@router.post("/admin/users/{user_id}/quota")
def set_user_quota(user_id, total_quota, period, db, admin):
    """设置用户配额"""
```

### 4.3 注册路由
**文件**: `fate/main.py`

```python
from app.routers import user_stats
app.include_router(user_stats.router, prefix="/api")
```

---

## 需要修改的文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/quota.py` | 新建 | UserQuota 模型 |
| `app/models/usage_log.py` | 新建 | UsageLog 模型（可选） |
| `app/models/__init__.py` | 修改 | 导出新模型 |
| `app/services/quota.py` | 新建 | QuotaService 类 |
| `app/services/chat_store.py` | 修改 | 添加持久化函数 |
| `app/chat/service.py` | 修改 | 添加持久化和配额检查 |
| `app/routers/chat.py` | 修改 | 添加认证依赖 |
| `app/routers/user_stats.py` | 新建 | 用户统计 API |
| `app/routers/admin_stats.py` | 修改 | 扩展管理员统计 |
| `main.py` | 修改 | 注册新路由 |
| `migrations/versions/xxx.py` | 新建 | 数据库迁移 |

---

## 实现顺序

1. **阶段一**：数据库模型（UserQuota）+ 迁移
2. **阶段二**：聊天持久化（修改 service.py + chat.py）
3. **阶段三**：配额服务（QuotaService）
4. **阶段四**：统计 API（user_stats.py + admin_stats.py）

---

## 验证方案

1. **数据库验证**：
   - 运行迁移后检查表结构
   - 手动插入测试数据验证

2. **聊天持久化验证**：
   - 发起对话后检查 `conversations` 和 `messages` 表
   - 重启服务后验证数据仍存在

3. **配额功能验证**：
   - 调用 `/api/user/quota` 验证返回数据
   - 设置有限配额后验证限制生效

4. **统计 API 验证**：
   - 调用管理员统计端点验证数据正确
   - 验证用户排行榜功能

---

## 注意事项

1. **向后兼容**：现有未登录用户仍可使用聊天（user_id 可为 null）
2. **内测阶段**：默认配额设为 -1（无限制），功能先上线
3. **WebSocket 端点**：`/ws/chat` 也需要同步修改以支持持久化
