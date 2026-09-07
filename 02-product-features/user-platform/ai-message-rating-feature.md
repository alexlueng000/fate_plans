# AI回复评价功能实现计划

## 功能概述

为Web端每条AI回复添加点赞/点踩评价功能：
- 点击 👍 直接提交点赞
- 点击 👎 弹出原因选择框，选择后提交
- **点踩时需保存用户的八字命盘数据，用于后续分析**

## 点踩原因选项

```
- 内容不准确 (inaccurate)
- 内容不相关 (irrelevant)
- 表述不清晰 (unclear)
- 内容不合适 (inappropriate)
- 其他 (other)
```

---

## 后端实现

### 1. 创建数据模型

**新建文件**: `fate/app/models/message_rating.py`

```python
class MessageRating(Base):
    __tablename__ = "message_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    rating_type: Mapped[str] = mapped_column(Enum("up", "down", name="rating_type"))
    reason: Mapped[Optional[str]] = mapped_column(String(50))

    # 命盘数据（点踩时保存，用于后续分析）
    paipan_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_message_ratings_message_user", "message_id", "user_id", unique=True),
    )
```

**命盘数据结构**（`paipan_data` 字段）：
```json
{
  "gender": "男",
  "four_pillars": {
    "year": ["甲", "子"],
    "month": ["丙", "寅"],
    "day": ["戊", "午"],
    "hour": ["庚", "申"]
  },
  "dayun": [
    {"age": 2, "start_year": 2000, "pillar": ["丁", "卯"]},
    ...
  ]
}
```

### 2. 创建Schema

**新建文件**: `fate/app/schemas/message_rating.py`

```python
class MessageRatingCreate(BaseModel):
    rating_type: Literal["up", "down"]
    reason: Optional[Literal["inaccurate", "irrelevant", "unclear", "inappropriate", "other"]] = None
    # 点踩时需要传递命盘数据
    paipan_data: Optional[Dict[str, Any]] = None

class MessageRatingResp(BaseModel):
    id: int
    rating_type: str
    reason: Optional[str]
    created_at: datetime

class UserRatingResp(BaseModel):
    message_id: int
    user_rating: Optional[MessageRatingResp]
```

### 3. 创建路由

**新建文件**: `fate/app/routers/message_rating.py`

- `POST /api/chat/messages/{message_id}/rating` - 提交评价
- `GET /api/chat/messages/{message_id}/rating` - 获取当前用户的评价状态

### 4. 修改配置

**修改**: `fate/app/models/__init__.py`
- 添加 `from .message_rating import MessageRating`

**修改**: `fate/main.py`
- 添加 `from app.routers import message_rating`
- 注册路由: `app.include_router(message_rating.router, prefix="/api")`

### 5. 数据库迁移

**手动执行SQL**（推荐）：

```sql
-- 创建消息评价表
CREATE TABLE message_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message_id INT NOT NULL,
    user_id INT NULL,
    rating_type ENUM('up', 'down') NOT NULL,
    reason VARCHAR(50) NULL,
    paipan_data JSON NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_message_ratings_message_id (message_id),
    INDEX idx_message_ratings_user_id (user_id),
    UNIQUE INDEX idx_message_ratings_message_user (message_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

**或使用 Alembic 迁移**：

```bash
cd fate
alembic revision --autogenerate -m "add message_ratings table"
alembic upgrade head
```

---

## UI 设计

### 评价按钮（位于AI消息底部右侧）

```
┌─────────────────────────────────────────────────────────┐
│  [AI头像]  AI回复内容...                                 │
│            内容继续...                                   │
│                                                         │
│                                            [👍] [👎]   │
└─────────────────────────────────────────────────────────┘

未评价状态：灰色按钮
已点赞状态：👍 金色高亮  👑 灰色禁用
已点踩状态：👍 灰色禁用  👑 红色高亮
```

### 点踩原因弹窗

```
┌──────────────────────────────────────┐
│          告诉我们原因         [×]     │
├──────────────────────────────────────┤
│                                      │
│  请选择不满意的理由：                 │
│                                      │
│  ○ 内容不准确                        │
│    解读与命盘信息不符                 │
│                                      │
│  ○ 内容不相关                        │
│    未回答我的问题                     │
│                                      │
│  ○ 表述不清晰                        │
│    内容难以理解                       │
│                                      │
│  ○ 内容不合适                        │
│    包含不当内容                       │
│                                      │
│  ○ 其他                              │
│                                      │
├──────────────────────────────────────┤
│                    [取消]  [提交]    │
└──────────────────────────────────────┘
```

---

## 前端实现

### 1. 扩展类型定义

**修改**: `fate-frontend/app/lib/chat/types.ts`

```typescript
export type Msg = {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  meta?: {
    kind: string;
    messageId?: number;  // 新增：关联后端消息ID
  };
  userRating?: {  // 新增：当前用户的评价状态
    ratingType: 'up' | 'down';
    reason?: string;
  };
};
```

### 2. 创建API客户端

**新建文件**: `fate-frontend/app/lib/chat/rating.ts`

```typescript
export async function submitRating(
  messageId: number,
  ratingType: 'up' | 'down',
  reason?: string,
  paipanData?: Paipan  // 点踩时传递命盘数据
)
export async function getRating(messageId: number): Promise<UserRatingResp | null>
```

### 3. 创建评价按钮组件

**新建文件**: `fate-frontend/app/components/chat/MessageRating.tsx`

```tsx
interface Props {
  messageId: number;
  userRating?: { ratingType: 'up' | 'down'; reason?: string };
  paipanData?: Paipan;  // 命盘数据（点踩时需要）
  onRated: (rating: { ratingType: 'up' | 'down'; reason?: string }) => void;
}
```

功能：
- 显示 👍/👎 按钮
- 点击 👍 直接提交
- 点击 👎 打开弹窗，传递 `paipanData` 给弹窗
- 已评价时显示对应状态

### 4. 创建点踩原因弹窗

**新建文件**: `fate-frontend/app/components/chat/DownvoteReasonModal.tsx`

```tsx
interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (reason: string, paipanData?: Paipan) => void;  // 提交时带回命盘数据
  paipanData?: Paipan;  // 保存命盘数据用于提交
}
```

### 5. 集成到消息列表

**修改**: `fate-frontend/app/components/chat/MessageList.tsx`

在 assistant 消息气泡底部添加评价按钮：

```tsx
{isAssistant && !m.streaming && (
  <div className="flex justify-end mt-1">
    <MessageRating
      messageId={m.meta?.messageId}
      userRating={m.userRating}
      onRated={(rating) => handleRating(i, rating)}
    />
  </div>
)}
```

---

## 文件清单

### 后端
| 操作 | 文件 |
|------|------|
| 新建 | `fate/app/models/message_rating.py` |
| 修改 | `fate/app/models/__init__.py` |
| 新建 | `fate/app/schemas/message_rating.py` |
| 新建 | `fate/app/routers/message_rating.py` |
| 修改 | `fate/main.py` |

### 前端
| 操作 | 文件 |
|------|------|
| 修改 | `fate-frontend/app/lib/chat/types.ts` |
| 新建 | `fate-frontend/app/lib/chat/rating.ts` |
| 新建 | `fate-frontend/app/components/chat/MessageRating.tsx` |
| 新建 | `fate-frontend/app/components/chat/DownvoteReasonModal.tsx` |
| 修改 | `fate-frontend/app/components/chat/MessageList.tsx` |

---

## 验证步骤

1. **启动后端**，运行数据库迁移
2. **启动前端**，进行八字解读
3. **验证功能**：
   - 点赞按钮点击后高亮
   - 点踩按钮点击后弹出原因选择框
   - 选择原因后提交，按钮变为高亮
   - 刷新页面后评价状态保持
4. **检查数据库**：
   - `message_ratings` 表有正确记录
   - 点踩记录的 `paipan_data` 字段包含完整的命盘 JSON 数据
