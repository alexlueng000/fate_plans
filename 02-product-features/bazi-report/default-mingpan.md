# 默认命盘功能设计方案

## 功能目标

让用户可以保存自己的出生信息作为"默认命盘"，下次使用时一键填充，无需重复输入。

---

## 用户场景

1. **新用户**: 首次输入出生信息后，不用提示，自行选择是否设为默认命盘
2. **老用户**: 登录后，如果有默认命盘，提示是否加载默认命盘信息
3. **切换命盘**: 用户可以为他人算命，但保留自己的默认设置

---

## 当前状态分析

### 已有的存储机制

| 存储位置 | 内容 | 特点 |
|---------|------|------|
| `localStorage` | `chat:last_paipan` | 仅存储计算结果，不含原始输入 |
| `sessionStorage` | `me` (用户对象) | 无出生信息字段 |
| 数据库 `User` 表 | 基本用户信息 | 无出生信息字段 |

### 需要存储的字段

```typescript
interface DefaultBirthData {
  gender: '男' | '女';
  calendar: 'gregorian' | 'lunar';
  birthDate: string;      // YYYY-MM-DD
  birthTime: string;      // HH:MM
  birthPlace: string;     // 城市名
}
```

---

## 实现方案

### 方案选择：前后端结合

- **已登录用户**: 存储到数据库，跨设备同步
- **未登录用户**: 存储到 localStorage，本地持久化

---

## 修改文件清单

### 后端 (fate/)

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/user.py` | 修改 | 添加 `default_birth_data` 字段 |
| `app/routers/users.py` | 修改 | 添加更新默认命盘的 API |
| `app/schemas/user.py` | 修改 | 添加请求/响应模型 |
| `migrations/versions/xxx.py` | 新建 | 数据库迁移脚本 |

### 前端 (fate-frontend/)

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/lib/auth.tsx` | 修改 | 扩展 User 类型，添加更新方法 |
| `app/lib/birthData.ts` | 新建 | 默认命盘存储/加载逻辑 |
| `app/panel/page.tsx` | 修改 | 加载默认值，添加保存按钮 |

> **注意**: 首页 (`app/page.tsx`) 不添加"设为默认命盘"按钮，仅在 Panel 页面提供此功能。

---

## 详细实现步骤

### 步骤 1: 后端 - 扩展用户模型

**文件**: `fate/app/models/user.py`

```python
from sqlalchemy import Column, Text

class User(Base):
    # ... 现有字段 ...

    # 默认命盘数据 (JSON 字符串)
    default_birth_data = Column(Text, nullable=True, comment='默认出生信息 JSON')
```

### 步骤 2: 后端 - 数据库迁移

**使用 Alembic 生成迁移**:
```bash
cd fate
alembic revision --autogenerate -m "add default_birth_data to user"
alembic upgrade head
```

**或手动执行 SQL**:
```sql
-- 添加 default_birth_data 字段到 users 表
ALTER TABLE users
ADD COLUMN default_birth_data TEXT NULL
COMMENT '默认出生信息 JSON';

-- 验证字段已添加
DESCRIBE users;
```

**回滚 SQL** (如需撤销):
```sql
ALTER TABLE users DROP COLUMN default_birth_data;
```

### 步骤 3: 后端 - 添加 API 端点

**文件**: `fate/app/routers/users.py`

```python
from pydantic import BaseModel

class DefaultBirthDataRequest(BaseModel):
    gender: str
    calendar: str
    birth_date: str
    birth_time: str
    birth_place: str

@router.patch("/me/default-birth-data")
def update_default_birth_data(
    payload: DefaultBirthDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_tx)
):
    import json
    current_user.default_birth_data = json.dumps(payload.dict())
    db.commit()
    return {"success": True, "data": payload.dict()}

@router.delete("/me/default-birth-data")
def clear_default_birth_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_tx)
):
    current_user.default_birth_data = None
    db.commit()
    return {"success": True}
```

### 步骤 4: 前端 - 创建存储模块

**文件**: `fate-frontend/app/lib/birthData.ts`

```typescript
import { api } from './api';
import { getAuthToken, currentUser } from './auth';

export interface DefaultBirthData {
  gender: '男' | '女';
  calendar: 'gregorian' | 'lunar';
  birthDate: string;
  birthTime: string;
  birthPlace: string;
}

const STORAGE_KEY = 'default_birth_data';

// 加载默认命盘
export async function loadDefaultBirthData(): Promise<DefaultBirthData | null> {
  const token = getAuthToken();

  // 已登录：从服务器获取
  if (token) {
    try {
      const resp = await fetch(api('/me'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      const user = await resp.json();
      if (user.default_birth_data) {
        return JSON.parse(user.default_birth_data);
      }
    } catch (e) {
      console.error('Failed to load from server:', e);
    }
  }

  // 未登录或服务器无数据：从 localStorage 获取
  const local = localStorage.getItem(STORAGE_KEY);
  return local ? JSON.parse(local) : null;
}

// 保存默认命盘
export async function saveDefaultBirthData(data: DefaultBirthData): Promise<boolean> {
  // 始终保存到 localStorage
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

  // 已登录：同步到服务器
  const token = getAuthToken();
  if (token) {
    try {
      await fetch(api('/me/default-birth-data'), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          gender: data.gender,
          calendar: data.calendar,
          birth_date: data.birthDate,
          birth_time: data.birthTime,
          birth_place: data.birthPlace
        })
      });
    } catch (e) {
      console.error('Failed to save to server:', e);
    }
  }

  return true;
}

// 清除默认命盘
export async function clearDefaultBirthData(): Promise<void> {
  localStorage.removeItem(STORAGE_KEY);

  const token = getAuthToken();
  if (token) {
    try {
      await fetch(api('/me/default-birth-data'), {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error('Failed to clear from server:', e);
    }
  }
}
```

### 步骤 5: 前端 - 修改 Panel 页

**文件**: `fate-frontend/app/panel/page.tsx`

```typescript
import { loadDefaultBirthData, saveDefaultBirthData, DefaultBirthData } from '@/app/lib/birthData';

// 在组件内添加
const [hasDefault, setHasDefault] = useState(false);

// 页面加载时自动填充
useEffect(() => {
  loadDefaultBirthData().then(data => {
    if (data) {
      setGender(data.gender);
      setCalendarType(data.calendar);
      setBirthDate(data.birthDate);
      setBirthTime(data.birthTime);
      setBirthPlace(data.birthPlace);
      setHasDefault(true);
    }
  });
}, []);

// 保存为默认按钮
const handleSaveAsDefault = async () => {
  await saveDefaultBirthData({
    gender,
    calendar: calendarType,
    birthDate,
    birthTime,
    birthPlace
  });
  setHasDefault(true);
  // 显示成功提示
};
```

**UI 添加保存按钮** (在表单区域):
```tsx
{birthDate && birthTime && (
  <button
    onClick={handleSaveAsDefault}
    className="text-sm text-[var(--color-primary)] hover:underline"
  >
    {hasDefault ? '更新默认命盘' : '保存为默认命盘'}
  </button>
)}
```

---

## UI 交互设计

### Panel 页表单区域

```
┌─────────────────────────────────────┐
│  性别: [男] [女]                     │
│  历法: [阳历] [农历]                 │
│  日期: [____年__月__日]              │
│  时间: [__:__]                       │
│  地点: [北京____________]            │
│                                      │
│  [排盘]                              │
│                                      │
│  ☑ 保存为我的默认命盘               │
└─────────────────────────────────────┘
```

### 已有默认命盘时

```
┌─────────────────────────────────────┐
│  ✓ 已加载您的默认命盘               │
│  [清除默认]                          │
│                                      │
│  性别: [男] [女]                     │
│  ...                                 │
└─────────────────────────────────────┘
```

---

## 验证方案

1. **后端测试**
   ```bash
   cd fate
   pytest tests/test_users.py -v
   ```

2. **前端测试**
   - 未登录状态：保存/加载 localStorage
   - 登录状态：保存/加载服务器数据
   - 跨设备同步：在另一设备登录后验证数据同步

3. **端到端测试**
   ```bash
   cd fate-frontend
   npm run dev
   ```
   - 首次访问：表单为空
   - 填写信息并保存为默认
   - 刷新页面：自动填充
   - 登录后：数据同步到服务器
   - 另一设备登录：数据自动加载

---

## 后续优化

1. **多命盘管理**: 允许用户保存多个命盘（家人、朋友）
2. **命盘命名**: 给保存的命盘起名字
3. **快速切换**: 下拉菜单快速切换不同命盘
4. **导入导出**: 支持命盘数据的导入导出
