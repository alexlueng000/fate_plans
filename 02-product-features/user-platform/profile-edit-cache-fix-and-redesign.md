# 档案修改功能优化：缓存清理 + UI 重设计

## 问题描述

用户反馈了两个关于档案修改功能的问题：

### 问题 1：缓存 Bug
用户修改档案（出生日期、时间、地点等）后，对话仍然使用旧的命盘数据，而不是更新后的数据。

**原因分析**：
- 档案更新成功重新计算并保存新的 bazi_chart 到数据库 ✓
- 但前端在 localStorage 中缓存了对话数据，包括旧的排盘信息
- 用户返回聊天时，从缓存恢复了旧对话和旧命盘数据
- 后端 `/chat/init` 端点确实从数据库加载最新数据，但 localStorage 恢复逻辑绕过了这一步

### 问题 2：设计不一致
档案修改页面使用硬编码颜色、间距不一致，没有遵循 `globals.css` 中建立的设计系统以及最近更新的注册/登录页面的设计模式。

## 解决方案概述

### 第一部分：修复缓存失效 Bug

**根本原因**：`clearAllChatData()` 函数存在于 `storage.ts` 中，但档案更新后从未被调用。

**修复方法**：在档案更新成功后调用 `clearAllChatData()` 强制下次聊天会话加载新数据。

**修改文件**：
- `fate-frontend/app/profile/edit/page.tsx` (第 142 行，成功更新后)

### 第二部分：重设计档案修改页面

**设计目标**：
- 使用 `globals.css` 中的 CSS 变量，而不是硬编码颜色
- 匹配更新后的注册页面的扁平、简洁设计
- 将输入框高度从 `py-3` 减少到 `h-10` (40px) 以保持一致性
- 使用正确的边框圆角（输入框使用 `rounded-lg`）
- 改善间距和视觉层次
- 添加细微的过渡和悬停状态

**修改文件**：
- `fate-frontend/app/profile/edit/page.tsx` (整个表单部分)

## 详细实现计划

### 步骤 1：在档案更新时添加缓存清理

**文件**：`fate-frontend/app/profile/edit/page.tsx`

**位置**：第 142 行，`router.push(returnTo)` 之前

**更改**：
1. 从 `@/app/lib/chat/storage` 导入 `clearAllChatData`
2. 在重定向前调用 `clearAllChatData()` 清除：
   - 活跃对话 ID
   - 缓存的排盘数据
   - 所有对话消息
   - sessionStorage 中的 conversation_id

**代码**：
```typescript
import { clearAllChatData } from '@/app/lib/chat/storage';

// 在 handleSubmit 中，成功更新后：
clearAllChatData(); // 清除缓存的聊天数据，强制使用新档案重新加载
router.push(returnTo);
```

**为什么有效**：
- 清除 localStorage 键：`chat:active`、`chat:last_paipan`、`chat:conv:*`
- 清除 sessionStorage：`conversation_id`
- 下次用户访问 chat/panel 时，找不到缓存的对话
- 后端 `/chat/init` 从数据库加载最新的 bazi_chart
- 用户获得使用更新后命盘数据的对话

### 步骤 2：重设计档案修改页面 UI

**文件**：`fate-frontend/app/profile/edit/page.tsx`

**设计系统参考**（来自 `globals.css`）：
- 主色：`var(--color-primary)` = `#B54434`
- 背景：`var(--color-bg)` = `#F7F3EE`
- 卡片背景：`var(--color-bg-card)` = `#FBF8F4`
- 主文本：`var(--color-text-primary)` = `#2A2522`
- 次要文本：`var(--color-text-secondary)` = `#7A7068`
- 弱化文本：`var(--color-text-muted)` = `#9B9087`
- 边框：`var(--color-border)` = `#E2D8CE`
- 边框圆角：`rounded-lg` (输入框 6px)，`rounded-xl` (卡片 8px)

**更改清单**：

1. **背景** (第 208 行)：
   - 改为：`bg-[var(--color-bg)]`、`text-[var(--color-text-primary)]`

2. **返回按钮** (第 212-217 行)：
   - 改为：`text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]`

3. **标题** (第 218-220 行)：
   - 改为：`text-[var(--color-text-primary)]`、`text-[var(--color-text-secondary)]`

4. **表单卡片** (第 223 行)：
   - 改为：`bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] shadow-sm`
   - 间距：`p-6`、`space-y-4`

5. **标签** (多处)：
   - 改为：`text-xs font-medium text-[var(--color-text-secondary)] mb-1.5`

6. **切换按钮** (性别、历法)：
   - 高度：`py-2.5`
   - 圆角：`rounded-lg`
   - 激活状态：使用 `var(--color-primary)` 相关变量
   - 非激活状态：使用 `var(--color-border)` 和 `var(--color-bg-elevated)`

7. **地点输入框** (第 319-329 行)：
   - 高度：`h-10`
   - 内边距：`px-3`
   - 圆角：`rounded-lg`
   - 边框：`border border-[var(--color-border)]`
   - 焦点：`focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/30`
   - 背景：`bg-[var(--color-bg-elevated)]`

8. **错误提示** (第 332-336 行)：
   - 改为：`bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-[var(--color-primary)]`
   - 圆角：`rounded-lg`

9. **提交按钮** (第 340-346 行)：
   - 高度：`h-11`
   - 圆角：`rounded-lg`
   - 颜色：`bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)]`
   - 阴影：`shadow-sm hover:shadow-md`

10. **删除按钮** (第 347-353 行)：
    - 高度：`h-11`
    - 圆角：`rounded-lg`
    - 使用主色系而非红色

11. **删除确认弹窗** (第 359-384 行)：
    - 使用 CSS 变量替换所有硬编码颜色

## 验证步骤

### 测试缓存失效：
1. 启动开发服务器：`cd fate-frontend && npm run dev`
2. 登录并导航到 `/panel`
3. 记录当前显示的命盘信息
4. 点击"修改资料"编辑档案
5. 更改出生日期/时间/地点
6. 点击"保存修改"
7. 验证重定向到 `/panel`
8. **预期**：聊天应使用新命盘数据重新初始化
9. **检查**：浏览器 DevTools → Application → Local Storage → 验证 `chat:active`、`chat:last_paipan` 和 `chat:conv:*` 键已清除
10. 发送消息并验证 AI 使用新的命盘数据

### 测试 UI 设计：
1. 导航到 `/profile/edit`
2. **视觉检查**：
   - 表单使用一致的 CSS 变量颜色（无硬编码十六进制）
   - 输入框高度为 40px（比之前更扁平）
   - 边框圆角一致（输入框使用 `rounded-lg`）
   - 切换按钮有正确的悬停状态
   - 输入框上出现主色焦点环
   - 错误消息使用主色
   - 按钮有正确的阴影和过渡
3. **响应式检查**：调整浏览器到移动宽度，验证布局适配
4. **交互检查**：点击所有按钮，验证悬停/激活状态工作
5. **对比**：并排打开 `/register` 页面，验证设计一致性

### 边缘情况：
1. 测试使用无效数据更新档案（空字段）→ 错误消息正确显示
2. 测试删除档案流程 → 弹窗显示正确样式
3. 测试存在缓存对话的情况 → 验证更新后缓存被清除
4. 测试快速多次更新档案 → 验证无竞态条件

## 关键文件

**修改**：
- `fate-frontend/app/profile/edit/page.tsx` - 添加缓存清理 + 重设计 UI

**参考**（无更改）：
- `fate-frontend/app/lib/chat/storage.ts` - 缓存清理函数
- `fate-frontend/app/globals.css` - 设计系统令牌
- `fate-frontend/app/(auth)/register/page.tsx` - 设计模式参考

## 成功标准

1. ✅ 档案更新后，localStorage 聊天数据被清除
2. ✅ 下次聊天会话从数据库加载最新命盘
3. ✅ 档案修改页面一致使用 CSS 变量
4. ✅ 表单输入框高度为 40px，间距合适
5. ✅ 所有颜色符合设计系统
6. ✅ 悬停和焦点状态正确工作
7. ✅ 设计与注册/登录页面一致
8. ✅ 移动端无视觉回归

## 数据流分析

### 当前流程（有 Bug）：
```
用户创建档案 → 开始聊天 → 对话存储到 localStorage（旧排盘）
     ↓
用户修改档案 → 新 bazi_chart 保存到数据库
     ↓
用户返回聊天 → getActiveConversationId() 找到旧对话 ID
     ↓
从 localStorage 加载旧对话（旧排盘数据）
     ↓
聊天继续使用过时的命盘数据 ❌
```

### 修复后流程：
```
用户创建档案 → 开始聊天 → 对话存储到 localStorage
     ↓
用户修改档案 → 新 bazi_chart 保存到数据库
     ↓
clearAllChatData() 清除所有缓存 ✓
     ↓
用户返回聊天 → 找不到缓存对话
     ↓
调用 /chat/init → 从数据库加载最新 bazi_chart
     ↓
聊天使用更新后的命盘数据 ✅
```

## 技术细节

### localStorage 缓存键：
- `chat:active` - 活跃对话 ID
- `chat:conv:{conversation_id}` - 对话消息
- `chat:last_paipan` - 最后的排盘数据

### clearAllChatData() 函数作用：
```typescript
export function clearAllChatData() {
  // 清理活跃会话 ID
  localStorage.removeItem('chat:active');
  // 清理排盘数据
  localStorage.removeItem('chat:last_paipan');
  // 清理所有会话数据
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('chat:conv:')) {
      localStorage.removeItem(key);
    }
  });
  // 清理 sessionStorage 中的会话 ID
  sessionStorage.removeItem('conversation_id');
}
```

### 后端对话存储：
- 位置：`fate/app/chat/store.py`
- 存储：内存字典或 Redis
- TTL：24 小时
- 存储内容：`pinned`（系统提示）、`history`、`kb_index_dir`
- **不存储排盘数据**（仅在初始消息中）

### 前端对话初始化：
- 位置：`fate-frontend/app/chat/page.tsx`、`fate-frontend/app/panel/page.tsx`
- 逻辑：
  1. 尝试从 localStorage 恢复旧对话（第 92-108 行）
  2. 如果找到，使用旧数据并提前返回 ❌
  3. 如果没有，调用 `/api/chat/start` 或 `/api/chat/init`
  4. 后端从数据库加载最新 profile.bazi_chart ✓

## 设计系统对比

### 修改前（不一致）：
- 硬编码颜色：`#a83232`、`#8c2b2b`、`neutral-*`
- 大圆角：`rounded-3xl`、`rounded-xl`
- 粗边框：`border-2`
- 大内边距：`py-3`、`py-4`、`p-6 sm:p-8`
- 无焦点环
- 无阴影

### 修改后（一致）：
- CSS 变量：`var(--color-primary)`、`var(--color-border)` 等
- 适中圆角：`rounded-lg` (6px)、`rounded-xl` (8px)
- 细边框：`border` (1px)
- 紧凑内边距：`h-10` (40px)、`py-2.5`、`p-6`
- 焦点环：`focus:ring-2 focus:ring-[var(--color-primary)]/30`
- 细微阴影：`shadow-sm`、`shadow-md`

## 参考页面

### 注册页面设计模式（已更新）：
- 文件：`fate-frontend/app/(auth)/register/page.tsx`
- 特点：
  - 输入框高度：`h-10` (40px)
  - 按钮高度：`h-11` (44px)
  - 圆角：`rounded-lg`
  - 焦点状态：`focus:ring-2 focus:ring-[var(--color-primary)]/30`
  - 标签：`text-xs font-medium text-[var(--color-text-secondary)] mb-1.5`
  - 错误消息：`text-xs text-[var(--color-primary)]`
  - 一致使用 CSS 变量

### 登录页面设计模式（已更新）：
- 文件：`fate-frontend/app/(auth)/login/page.tsx`
- 与注册页面保持一致的设计

### Panel 页面命盘信息（已更新）：
- 文件：`fate-frontend/app/panel/page.tsx`
- 特点：
  - 扁平设计：`bg-white/50`
  - 内联文本：无边框盒子
  - 分隔符：`·` 字符
  - 简洁排版

## 实现优先级

### 高优先级（必须）：
1. ✅ 添加 `clearAllChatData()` 调用 - 修复核心 Bug
2. ✅ 替换所有硬编码颜色为 CSS 变量 - 设计一致性
3. ✅ 统一输入框高度为 40px - 视觉一致性

### 中优先级（重要）：
4. ✅ 添加焦点环和过渡效果 - 用户体验
5. ✅ 统一边框圆角 - 设计细节
6. ✅ 优化间距和内边距 - 视觉平衡

### 低优先级（可选）：
7. ✅ 添加细微阴影 - 视觉深度
8. ✅ 优化删除确认弹窗样式 - 完整性

## 潜在风险

### 风险 1：清除缓存可能影响其他功能
- **缓解**：`clearAllChatData()` 只清除聊天相关数据，不影响认证令牌或用户信息

### 风险 2：用户可能在多个标签页打开聊天
- **缓解**：localStorage 在所有标签页共享，清除后所有标签页都会重新初始化

### 风险 3：设计更改可能破坏移动端布局
- **缓解**：保留响应式类（`sm:`），测试移动端视图

### 风险 4：自定义组件（日期/时间选择器）可能不匹配新设计
- **缓解**：这些组件有自己的主题系统，保持不变

## 后续优化建议

1. **后端会话失效**：考虑在档案更新时使后端对话存储失效
2. **版本控制**：在 profile 表添加 `version` 字段，检测过时对话
3. **用户提示**：档案更新后显示"命盘已更新"提示
4. **平滑过渡**：添加加载动画，改善用户体验
5. **设计系统文档**：创建组件库文档，确保未来一致性
