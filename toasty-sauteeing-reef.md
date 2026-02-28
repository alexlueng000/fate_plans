# 微信小程序Markdown渲染优化计划

## 用户需求

用户对当前的Markdown渲染功能提出了以下需求:
1. **了解红字突出功能的实现原理** - 用户认为这个功能做得很好,想了解技术实现
2. **增强红字功能** - 希望扩展或改进现有的红字突出功能
3. **减小标题字体大小** - 当前标题字体太大,需要调整
4. **说明####标记** - 用户不清楚四级标题的作用和效果

## 当前实现分析

### 红字突出功能实现原理

**文件**: `fate_wechat/miniprogram/pages/chat/chat.ts` (第102-166行)

**核心机制**:
1. **语法**: 使用中文书名号 `【xxx】` 标记需要突出显示的文本
2. **解析**: `parseInline()` 函数使用正则表达式识别并转换
3. **渲染**: 转换为 `<span class="highlight">xxx</span>` HTML标签
4. **样式**: 通过CSS类 `.highlight` 应用红色样式

**代码实现**:
```typescript
// chat.ts:102-166
function parseInline(text: string): string {
  // 1. 处理【xxx】强调语法 → <span class="highlight">
  text = text.replace(/【([^】]+)】/g, '<span class="highlight">$1</span>');

  // 2. 处理 **粗体**
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // 3. 处理 *斜体*
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  return text;
}
```

**样式定义**: `fate_wechat/miniprogram/pages/chat/chat.wxss` (第299-307行)
```css
/* 【xxx】强调样式 - 助手气泡 */
.bubble .md .highlight {
  color: var(--primary);  /* #c93b3a 红色 */
  font-weight: 600;
}
```

**优势**:
- ✅ 使用中文标点符号,符合中文输入习惯
- ✅ 视觉突出,易于识别重点信息
- ✅ 实现简单,性能高效
- ✅ 不与Markdown标准语法冲突

### 当前标题样式

**文件**: `fate_wechat/miniprogram/pages/chat/chat.wxss` (第205-240行)

| 标题级别 | 当前字体大小 | 字重 | 其他样式 |
|---------|-------------|------|---------|
| h1 (##) | 26rpx | 700 | 底部边框 |
| h2 (###) | 24rpx | 600 | 无 |
| h3 (####) | 23rpx | 600 | 无 |

**问题**:
- 标题字体相对正文(20rpx)偏大,视觉层次过于突出
- h1、h2、h3之间的差异较小(26/24/23),层次感不够明显

### #### 标记支持情况

**当前状态**:
- ✅ `formatMarkdownImpl()` 函数支持解析 `####` (h3级别)
- ✅ CSS中有 `.md h3` 样式定义
- ⚠️ 用户可能混淆了Markdown语法:
  - `##` → h1
  - `###` → h2
  - `####` → h3
  - `#####` → h4 (未定义样式)

## 优化方案

### 优化1: 增强红字突出功能

**新增功能**: 支持多种强调级别和颜色

**实现方案**:
1. **保留现有【xxx】语法** - 红色强调(主要)
2. **新增〖xxx〗语法** - 橙色强调(次要)
3. **新增《xxx》语法** - 蓝色强调(信息)

**代码修改**: `chat.ts` parseInline函数
```typescript
function parseInline(text: string): string {
  // 1. 【xxx】红色强调(主要) - 保持不变
  text = text.replace(/【([^】]+)】/g, '<span class="highlight">$1</span>');

  // 2. 〖xxx〗橙色强调(次要) - 新增
  text = text.replace(/〖([^〗]+)〗/g, '<span class="highlight-warning">$1</span>');

  // 3. 《xxx》蓝色强调(信息) - 新增
  text = text.replace(/《([^》]+)》/g, '<span class="highlight-info">$1</span>');

  // 4. **粗体**
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // 5. *斜体*
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  return text;
}
```

**样式定义**: `chat.wxss` 新增样式
```css
/* 〖xxx〗橙色强调(次要) */
.bubble .md .highlight-warning {
  color: #e67e22;  /* 橙色 */
  font-weight: 600;
}

/* 《xxx》蓝色强调(信息) */
.bubble .md .highlight-info {
  color: #3498db;  /* 蓝色 */
  font-weight: 600;
}
```

**使用场景**:
- 【重要】- 关键信息、警告、核心要点
- 〖注意〗- 次要提示、建议
- 《参考》- 补充信息、引用

### 优化2: 调整标题字体大小

**目标**: 减小标题字体,增强层次感

**新的字体大小方案**:

| 标题级别 | 当前大小 | 优化后大小 | 变化 | 说明 |
|---------|---------|-----------|------|------|
| 正文 | 20rpx | 20rpx | - | 基准 |
| h3 (####) | 23rpx | 21rpx | -2rpx | 略大于正文 |
| h2 (###) | 24rpx | 22rpx | -2rpx | 中等标题 |
| h1 (##) | 26rpx | 24rpx | -2rpx | 主标题 |

**代码修改**: `chat.wxss` (第205-240行)
```css
/* 标题样式 - 优化后 */
.bubble .md h1 {
  font-size: 24rpx;  /* 从26rpx减小 */
  font-weight: 700;
  color: #3D2E1D;
  margin: 16rpx 0 12rpx;
  padding-bottom: 8rpx;
  border-bottom: 2rpx solid rgba(201, 61, 47, 0.15);
  line-height: 1.4;
}

.bubble .md h2 {
  font-size: 22rpx;  /* 从24rpx减小 */
  font-weight: 600;
  color: #3D2E1D;
  margin: 14rpx 0 10rpx;
  line-height: 1.4;
}

.bubble .md h3 {
  font-size: 21rpx;  /* 从23rpx减小 */
  font-weight: 600;
  color: #3D2E1D;
  margin: 12rpx 0 8rpx;
  line-height: 1.4;
}
```

**优势**:
- 标题与正文的对比度降低,视觉更柔和
- 保持清晰的层次结构(24 > 22 > 21 > 20)
- 每级差异2rpx,层次感更明显

### 优化3: 完善标题支持和文档

**问题**: 用户对Markdown标题语法不清楚

**解决方案**: 在后端系统提示中添加Markdown语法说明

**文件**: 后端数据库 `app_config` 表的 `system_prompt` 字段

**建议添加的内容**:
```
## Markdown格式规范

在回复中,你可以使用以下Markdown语法来格式化内容:

### 标题
- ## 主标题 - 用于章节标题
- ### 次标题 - 用于小节标题
- #### 三级标题 - 用于要点标题

### 强调
- 【重要内容】- 红色强调,用于关键信息
- 〖注意事项〗- 橙色强调,用于次要提示
- 《参考信息》- 蓝色强调,用于补充说明
- **粗体文字** - 用于一般强调
- *斜体文字* - 用于轻微强调

### 列表
- 使用 - 或 * 开头创建无序列表
- 使用 1. 2. 3. 创建有序列表

### 注意事项
- 只使用 ## ### #### 三级标题,不要使用 # 或 #####
- 标题前后需要空行
- 列表项之间不要有空行
```

**前端优化**: 在聊天页面添加格式说明按钮

**文件**: `chat.wxml` 在操作按钮区域添加
```xml
<view class="action-btn" bindtap="onShowFormatGuide">
  <text class="action-icon">📝</text>
  <text>格式说明</text>
</view>
```

**文件**: `chat.ts` 添加处理函数
```typescript
onShowFormatGuide() {
  wx.showModal({
    title: "Markdown格式说明",
    content:
      "AI回复支持以下格式:\n\n" +
      "【重要】- 红色强调\n" +
      "〖注意〗- 橙色强调\n" +
      "《参考》- 蓝色强调\n\n" +
      "## 主标题\n" +
      "### 次标题\n" +
      "#### 三级标题\n\n" +
      "**粗体** *斜体*",
    showCancel: false,
    confirmText: "知道了"
  });
}
```

## 实施细节

### 修改1: 增强红字功能

**文件**: `fate_wechat/miniprogram/pages/chat/chat.ts`

**位置**: `parseInline()` 函数 (第102-166行)

**修改内容**:
```typescript
function parseInline(text: string): string {
  // 1. 【xxx】红色强调(主要)
  text = text.replace(/【([^】]+)】/g, '<span class="highlight">$1</span>');

  // 2. 〖xxx〗橙色强调(次要) - 新增
  text = text.replace(/〖([^〗]+)〗/g, '<span class="highlight-warning">$1</span>');

  // 3. 《xxx》蓝色强调(信息) - 新增
  text = text.replace(/《([^》]+)》/g, '<span class="highlight-info">$1</span>');

  // 4. **粗体**
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // 5. *斜体*
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  return text;
}
```

### 修改2: 添加新的强调样式

**文件**: `fate_wechat/miniprogram/pages/chat/chat.wxss`

**位置**: 在 `.highlight` 样式后添加 (约第307行后)

**修改内容**:
```css
/* 【xxx】红色强调(主要) - 保持不变 */
.bubble .md .highlight {
  color: var(--primary);  /* #c93b3a */
  font-weight: 600;
}

/* 〖xxx〗橙色强调(次要) - 新增 */
.bubble .md .highlight-warning {
  color: #e67e22;
  font-weight: 600;
}

/* 《xxx》蓝色强调(信息) - 新增 */
.bubble .md .highlight-info {
  color: #3498db;
  font-weight: 600;
}
```

### 修改3: 调整标题字体大小

**文件**: `fate_wechat/miniprogram/pages/chat/chat.wxss`

**位置**: 标题样式部分 (第205-240行)

**修改内容**:
```css
.bubble .md h1 {
  font-size: 24rpx;  /* 从26rpx改为24rpx */
  font-weight: 700;
  color: #3D2E1D;
  margin: 16rpx 0 12rpx;
  padding-bottom: 8rpx;
  border-bottom: 2rpx solid rgba(201, 61, 47, 0.15);
  line-height: 1.4;
}

.bubble .md h2 {
  font-size: 22rpx;  /* 从24rpx改为22rpx */
  font-weight: 600;
  color: #3D2E1D;
  margin: 14rpx 0 10rpx;
  line-height: 1.4;
}

.bubble .md h3 {
  font-size: 21rpx;  /* 从23rpx改为21rpx */
  font-weight: 600;
  color: #3D2E1D;
  margin: 12rpx 0 8rpx;
  line-height: 1.4;
}
```

### 修改4: 添加格式说明按钮(可选)

**文件**: `fate_wechat/miniprogram/pages/chat/chat.wxml`

**位置**: 操作按钮区域 (第66-81行)

**修改内容**: 在"清空对话"按钮后添加
```xml
<view class="action-btn" bindtap="onShowFormatGuide">
  <text class="action-icon">📝</text>
  <text>格式说明</text>
</view>
```

**文件**: `fate_wechat/miniprogram/pages/chat/chat.ts`

**位置**: 在其他事件处理函数后添加

**修改内容**:
```typescript
onShowFormatGuide() {
  wx.showModal({
    title: "Markdown格式说明",
    content:
      "AI回复支持以下格式:\n\n" +
      "【重要】- 红色强调\n" +
      "〖注意〗- 橙色强调\n" +
      "《参考》- 蓝色强调\n\n" +
      "## 主标题\n" +
      "### 次标题\n" +
      "#### 三级标题\n\n" +
      "**粗体** *斜体*",
    showCancel: false,
    confirmText: "知道了"
  });
}
```

## 关键文件

- 🔧 `fate_wechat/miniprogram/pages/chat/chat.ts` - 添加新的强调语法解析(第102-166行)
- 🔧 `fate_wechat/miniprogram/pages/chat/chat.wxss` - 添加新样式,调整标题大小(第205-240行, 第299-307行)
- 🔧 `fate_wechat/miniprogram/pages/chat/chat.wxml` - 添加格式说明按钮(可选,第66-81行)

## 验证步骤

### 测试用例1: 红字功能增强

**测试步骤**:
1. 打开微信开发者工具
2. 进入对话页面
3. 在后端系统提示中添加测试内容:
   ```
   【这是红色强调】
   〖这是橙色强调〗
   《这是蓝色强调》
   ```
4. 发送消息触发AI回复
5. 预期: 三种强调文本分别显示为红色、橙色、蓝色

### 测试用例2: 标题大小调整

**测试步骤**:
1. 在对话中触发包含标题的AI回复
2. 检查标题字体大小:
   - ## 主标题 → 24rpx
   - ### 次标题 → 22rpx
   - #### 三级标题 → 21rpx
3. 预期: 标题字体比之前小,但仍保持清晰的层次

### 测试用例3: 格式说明按钮(如果实现)

**测试步骤**:
1. 进入对话页面
2. 点击"格式说明"按钮
3. 预期: 弹出模态框显示Markdown格式说明

### 测试用例4: 兼容性测试

**测试步骤**:
1. 测试包含多种格式的复杂消息:
   ```
   ## 命盘分析

   ### 性格特点
   你的命盘显示【强烈的领导力】和〖创新思维〗。

   #### 事业建议
   《参考》: 适合从事管理或创业。

   **重点**: 需要注意*人际关系*的平衡。
   ```
2. 预期: 所有格式正确渲染,无冲突

### 测试用例5: 性能测试

**测试步骤**:
1. 发送包含大量强调标记的长文本
2. 观察渲染速度和流畅度
3. 预期: 无明显卡顿,渲染流畅

## 风险评估

**低风险**:
- 仅修改前端渲染逻辑,不涉及后端API
- 新增功能向后兼容,不影响现有【xxx】语法
- CSS样式修改独立,不影响其他组件
- 标题大小调整幅度小(2rpx),视觉影响可控

**潜在影响**:
- 新的强调语法需要在后端系统提示中说明,AI才会使用
- 标题字体变小后,部分用户可能需要适应
- 如果用户在输入中使用〖〗或《》,会被误识别为强调语法

**缓解措施**:
- 保持【xxx】作为主要强调语法,新语法为可选增强
- 标题大小可以根据用户反馈进一步微调
- 在用户输入中不解析强调语法(仅在AI回复中解析)

## 实施顺序

1. **修改 `chat.ts`** - 添加新的强调语法解析逻辑
2. **修改 `chat.wxss`** - 添加新样式,调整标题大小
3. **测试基础功能** - 验证新语法和标题大小
4. **(可选) 添加格式说明按钮** - 修改 `chat.wxml` 和 `chat.ts`
5. **更新后端系统提示** - 在数据库中添加Markdown格式说明
6. **全面测试** - 执行所有测试用例
7. **用户反馈收集** - 观察实际使用效果,根据反馈调整

## 后续优化建议

1. **更多强调样式**: 可以考虑添加背景色强调、下划线等
2. **代码块支持**: 添加 \`\`\`代码块\`\`\` 语法支持
3. **表格支持**: 添加简单的表格渲染
4. **链接支持**: 添加 [文本](URL) 链接语法
5. **图片支持**: 添加 ![描述](URL) 图片语法
6. **自定义主题**: 允许用户选择不同的颜色主题

## 总结

本次优化主要聚焦于:
1. **解释红字功能** - 详细说明了【xxx】语法的实现原理
2. **增强强调功能** - 新增〖xxx〗和《xxx》两种强调级别
3. **优化标题大小** - 将h1/h2/h3分别减小2rpx,视觉更柔和
4. **完善文档说明** - 添加格式说明按钮和系统提示更新

所有修改都遵循最小化原则,保持向后兼容,风险可控。
