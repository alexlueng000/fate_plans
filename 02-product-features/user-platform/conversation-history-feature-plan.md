# 八字 / 六爻 对话历史功能

## Context

`/chat`（八字）和 `/liuyao`（六爻）两个对话流目前**已经把对话写进 `conversations` + `messages` 表**，但前端没有任何"历史会话列表"页面。`Header.tsx:179` 已经放了"我的解读记录" → `/history` 的入口，可点了就 404，因为页面根本不存在。

实质上是地基都打好了，差地面建筑：
- 数据：`Conversation` 表通过 `profile_id IS NOT NULL`（八字）/ `liuyao_hexagram_id IS NOT NULL`（六爻）天然区分两类。
- Schema：`fate/app/schemas/chat.py` 已定义 `ConversationItem` / `MessageItem` / `HistoryResp`，未被任何端点使用。
- 删除：`fate/app/routers/chat_basic.py:60-70` 已有 `POST /conversations/delete`，可直接复用。

要补的是：
1. 后端 2 个查询端点：列表 + 取详
2. 前端 `/history` Tab 页（八字 / 六爻）
3. `/chat`、`/liuyao` 接收 `?conv_id=xxx` 恢复历史

确认的关键决策：
- 历史页布局：**单页 Tab**（八字 / 六爻）
- 点击列表项：**跳回原页继续聊**（`/chat?conv_id=...` / `/liuyao?conv_id=...`）
- 列表项展示：标题 + 更新时间 + 八字四柱摘要 / 六爻本卦→变卦 + 最后消息预览
- 操作：**仅删除**（首版不做重命名）

---

## 后端改动

### 1. 新增 `fate/app/routers/conversations.py`

避开八字 / 六爻 router 的耦合，单独一个 router 管对话级 CRUD。注册到 `main.py`。

#### 1.1 `GET /conversations`

入参 query：
- `type: Literal["bazi", "liuyao"]`
- `limit: int = 20`（最大 50）
- `offset: int = 0`（首版用 offset，量级够）

过滤条件（按 `type`）：
```sql
-- bazi
WHERE user_id = :me AND profile_id IS NOT NULL AND liuyao_hexagram_id IS NULL
-- liuyao
WHERE user_id = :me AND liuyao_hexagram_id IS NOT NULL
ORDER BY updated_at DESC, id DESC
LIMIT :limit OFFSET :offset
```

返回：
```python
class ConversationListItem(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    last_user_message: Optional[str]      # 截 60 字
    last_assistant_preview: Optional[str] # 截 60 字
    # 八字才有
    bazi_summary: Optional[str]           # "丙午·癸巳·庚辰·癸未"
    # 六爻才有
    hexagram: Optional[dict]              # {hexagram_id, main_gua, change_gua, question}

class ConversationListResp(BaseModel):
    items: List[ConversationListItem]
    total: int                            # 给前端做翻页
    has_more: bool
```

实现要点：
- "最后一条消息预览" 通过子查询拿 — 单条列表查询后再针对每条 conv 取 `Message` 表的最后一行 user / assistant 即可；
  - 性能优化：用 `func.row_number() over (partition by conversation_id order by id desc)` 单次拿前 2 条。但首版可以朴素 N 次小查询，limit 20 没事。
- 八字摘要：JOIN `user_profiles`，从 `bazi_chart["mingpan"]["four_pillars"]` 拼字符串 `f"{year}·{month}·{day}·{hour}"`（每柱取首两字）。
- 六爻 hexagram：JOIN `liuyao_hexagrams`，取 `hexagram_id, main_gua, change_gua, question`。

#### 1.2 `GET /conversations/{id}`

完整恢复一个对话，用于前端 URL 参数跳转。

返回：
```python
class ConversationDetailResp(BaseModel):
    id: int
    type: Literal["bazi", "liuyao"]       # 由 profile_id / liuyao_hexagram_id 推断
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageItem]           # 复用现有 schema (chat.py:33-40)
    # 八字才有
    profile: Optional[dict]               # {bazi_chart: mingpan}
    # 六爻才有
    hexagram: Optional[dict]              # 复用 HexagramDetailResponse 的字段
```

所有权校验：`Conversation.user_id == current_user.id`，否则 404。

实现要点：
- 八字：`profile = db.query(UserProfile).get(conv.profile_id)` → 把 `profile.bazi_chart["mingpan"]` 直接塞回去；前端能直接复用现有 `setPaipan`。
- 六爻：`hexagram = db.query(LiuyaoHexagram).get(conv.liuyao_hexagram_id)` → 用现有 `HexagramDetailResponse.model_validate(hexagram).model_dump()` 序列化，前端 setResult 直接吃。
- messages：按 `id ASC` 全部拉出（一个 conversation 不会太多）。

#### 1.3 `DELETE /conversations/{id}`

直接做新端点，比复用 `chat_basic.py:60-70` 的 `POST /conversations/delete` 语义更清晰（RESTful）。

```python
@router.delete("/{conversation_id}")
def delete_conversation(...):
    # 校验所有权
    # db.delete(conv)，messages 通过 cascade 自动清
```

注：`Conversation.messages` 已配 `cascade="all, delete-orphan"`（`models/chat.py:79`），表级也有 `ON DELETE CASCADE`。

### 2. 八字会话恢复时 in-memory history 缺失

`fate/app/chat/service.py:368-393` 的 from-DB recover 路径只把 system_prompt + paipan 写回 `set_conv`，**不恢复历史消息**。如果用户从历史页跳回 `/chat?conv_id=xxx`，发首条追问时 AI 看不到之前聊过的内容。

修复（同一处增加几行）：
```python
# 当走 recover 分支时，把 DB 中的 messages 加载回 in-memory history
db_msgs = db.query(Message).filter_by(conversation_id=db_conv_id).order_by(Message.id).all()
history = [{"role": m.role, "content": m.content} for m in db_msgs if m.role in ("user", "assistant")]
set_conv(conversation_id, {
    "pinned": composed,
    "history": history,   # ← 之前是 []
    ...
})
```

六爻 `_send_streaming_message`（`fate/app/liuyao/chat_service.py:233-...`）当前没有 from-DB recover 分支 — 直接 `raise ValueError("会话不存在")`。本次新增 recover 逻辑，参考八字的写法：
- conv 不存在但 `conversation_id` 形如 `conv_{db_conv_id}` 时，从 DB 拉 conversation + 校验所有权 + 拉 messages 重建 in-memory state。

### 3. 注册新 router

`fate/main.py` 加：
```python
from app.routers.conversations import router as conversations_router
app.include_router(conversations_router, prefix="/api")
```

---

## 前端改动

### 1. 新增 `fate-frontend/app/lib/history/api.ts`

```ts
export type HistoryType = 'bazi' | 'liuyao';

export type ConversationListItem = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  last_user_message: string | null;
  last_assistant_preview: string | null;
  bazi_summary?: string | null;
  hexagram?: { hexagram_id: string; main_gua: string; change_gua: string | null; question: string } | null;
};

export const historyApi = {
  list: (type: HistoryType, offset = 0, limit = 20) => ...,
  detail: (id: number) => ...,
  delete: (id: number) => ...,
};
```

### 2. 新增 `fate-frontend/app/(auth)/history/page.tsx`

布局：
```
┌────────────────────────────────┐
│ 我的解读记录                    │  ← h1
│ [八字 7]  [六爻 3]              │  ← 两个 Tab，带计数 badge
├────────────────────────────────┤
│ ┌──────────────────────────┐   │
│ │ 八字 · 丙午·癸巳·庚辰·癸未  │   │  ← 卡片标题（八字 fallback）
│ │ 03-05 14:32              │   │  ← 相对时间
│ │ "我最近事业有变动..."      │   │  ← 最后 user / assistant 预览
│ │                       [×] │   │  ← 删除按钮
│ └──────────────────────────┘   │
│ ...                             │
│ [上一页] 1/3 [下一页]           │
└────────────────────────────────┘
```

行为：
- 卡片整体 Click → `router.push('/chat?conv_id=' + id)` 或 `/liuyao?conv_id=' + id`
- 删除按钮：弹 confirm + 调 `historyApi.delete()` + 本地列表 splice
- 空状态：插画 + 文案"还没有解读记录" + 按钮跳 `/panel` 或 `/liuyao`

标题语义化（前端兜底）：
- 六爻：直接用后端 `title`（已经是 `六爻｜{question}`）
- 八字：`title === '八字解读'` 时显示 `八字 · {bazi_summary}`，否则显示 `title`

### 3. 修改 `fate-frontend/app/chat/page.tsx` 接收 conv_id

bootstrap useEffect（约 line 74-189）开头加：
```ts
const sp = new URLSearchParams(window.location.search);
const urlConvId = sp.get('conv_id');

if (urlConvId) {
  // 从后端恢复
  const detail = await historyApi.detail(Number(urlConvId));
  setConversationId(`conv_${detail.id}`);
  setPaipan(detail.profile.bazi_chart);  // setPaipan 已存在
  setMsgs(detail.messages.map(m => ({
    role: m.role,
    content: m.content,
    meta: { messageId: m.id },
  })));
  // 同步到 sessionStorage / localStorage
  sessionStorage.setItem('conversation_id', `conv_${detail.id}`);
  setBooting(false);
  return;
}
// 否则走原有 localStorage 恢复 / start 新会话流程
```

注意：八字 `setMsgs` 后第一条很可能是后端注入的"我的命盘信息如下：..."长 prompt，UI 里展示出来很丑。**过滤策略**：跳过第一条 role=user 且包含特殊标志（如开头是"我的命盘信息如下"）的消息。或者把这条消息标 `meta.kind = 'intro_paipan'`，让 `MessageList.tsx:87` 已有的 `isIntro` 分支处理（折叠 / 不显示）。**首版用字符串前缀过滤即可**。

### 4. 修改 `fate-frontend/app/liuyao/page.tsx` 接收 conv_id

useEffect 里加同样逻辑，但需要先 setResult（卦象详情来自 detail.hexagram），再 setConversationId / setMsgs：
```ts
if (urlConvId) {
  const detail = await historyApi.detail(Number(urlConvId));
  // detail.hexagram 形状与 HexagramDetail 类型一致 → 直接 setResult
  setResult(detail.hexagram as HexagramDetail);
  setConversationId(`conv_${detail.id}`);
  setMsgs(detail.messages.map(...));
  // 同步存 LIUYAO_ACTIVE_CONV_KEY
  return;
}
```

六爻第一条 user 消息也是后端注入的 `build_opening_user_message` 结果，同样需过滤或折叠。

### 5. Header.tsx 顺手加 active 态（可选，小改）

`Header.tsx:179` 当前没用 `usePathname`。加个：
```ts
const pathname = usePathname();
const isActive = pathname === '/history';
```
"我的解读记录"链接条件加 `bg-...` 表示当前。这个不是核心，可以留 P1。

---

## 关键文件改动清单

| 文件 | 类型 | 说明 |
|---|---|---|
| `fate/app/routers/conversations.py` | 新增 | 列表 / 取详 / 删除 3 端点 |
| `fate/app/schemas/chat.py` | 修改 | 新增 `ConversationListItem` / `ConversationListResp` / `ConversationDetailResp`（也可放进新 router 文件内） |
| `fate/main.py` | 修改 | 注册 conversations_router |
| `fate/app/chat/service.py` | 修改 | recover 分支补 history 加载（约 +5 行） |
| `fate/app/liuyao/chat_service.py` | 修改 | `_send_streaming_message` 加 from-DB recover 分支 |
| `fate-frontend/app/lib/history/api.ts` | 新增 | API 客户端 |
| `fate-frontend/app/(auth)/history/page.tsx` | 新增 | 历史页 Tab + 列表 + 翻页 |
| `fate-frontend/app/chat/page.tsx` | 修改 | bootstrap 加 `?conv_id=` 分支（约 +30 行） |
| `fate-frontend/app/liuyao/page.tsx` | 修改 | 同上 |
| `fate-frontend/app/components/Header.tsx` | 可选 | active 态高亮 |

---

## 验证

### 后端

```bash
# 1. 列表
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/conversations?type=bazi&limit=5'
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/conversations?type=liuyao&limit=5'

# 2. 取详
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/conversations/42'

# 3. 删除
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/conversations/42'

# 4. 跨用户访问应 404
# 5. 删除后再 GET 应 404
```

### 前端

1. `/panel` 完成一次八字对话 → 进 `/history` 应见一条八字
2. `/liuyao` 完成一次六爻对话 → 进 `/history` 切换到六爻 tab 应见一条
3. 点击八字记录 → 跳 `/chat?conv_id=xxx` → 历史消息显示 → 输入框追问可继续，AI 上下文连贯（验证 service.py recover 路径修好了）
4. 同理点击六爻记录 → 跳 `/liuyao?conv_id=xxx` → 卦象图重建 + 历史消息显示
5. 点删除按钮 → confirm → 列表移除 + 后端 DB 行真删
6. 八字标题 fallback：DB 里 title=='八字解读' 的旧数据，列表显示成 `八字 · 四柱摘要`
7. 第一条系统注入的 user 消息（"我的命盘信息如下..."、"请基于以下卦象做第一次解读..."）在恢复后**不应**作为普通气泡出现
8. 翻页：>20 条数据时翻页正常
9. 删除别人的 conversation：后端 404，前端报错 toast
10. URL 直接访问 `/history` 未登录：被 `(auth)` 路由组重定向到 `/login`

### 边界

- 列表为空 → 友好空态
- 后端列表查询慢（消息预览 N+1）：首版接受，下版本用 `row_number()` 单次拿
- 服务器重启后从历史页恢复对话：service.py recover 分支应能 load 回 message history
- 八字 / 六爻交叉污染：六爻对话误出现在八字 tab，由 `profile_id IS NOT NULL AND liuyao_hexagram_id IS NULL` 严格区分排除
