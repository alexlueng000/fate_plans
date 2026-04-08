# "猜你想问"功能设计方案

**日期**: 2026-04-03  
**状态**: 待实施  
**预计工时**: 1.5-2 天

## 一、功能概述

在用户与 AI 对话过程中，每次 AI 回复后自动显示 4 个个性化的推荐问题，引导用户深入对话，提升用户体验和参与度。

### 核心特性
- **显示时机**: 每次 AI 回复后都显示
- **生成方式**: AI 动态生成（基于当前对话内容）
- **问题数量**: 4 个
- **交互方式**: 点击直接发送

---

## 二、功能价值评估

### 用户价值
1. **降低思考门槛** - 用户不知道该问什么时，推荐问题可以引导对话深入
2. **提升参与度** - 每次 AI 回复后都有新的话题建议，保持对话连续性
3. **发现隐藏功能** - 通过推荐问题，用户可以了解系统能回答哪些类型的问题
4. **提高满意度** - 个性化的问题推荐让用户感觉被理解，提升体验

### 商业价值
1. **增加会话轮次** - 平均每次对话可能增加 2-3 轮，提升用户粘性
2. **降低流失率** - 用户不会因为"不知道问什么"而离开
3. **数据收集** - 可以统计哪些推荐问题被点击最多，优化产品方向
4. **差异化竞争** - 相比传统算命网站，这是一个明显的体验优势

### 技术成本
- 无需额外 API 调用（在主回复中附带）
- 需要修改 system prompt（约 100-200 字）
- 前端开发工作量约 1-2 天
- 后端改动极小（仅修改 prompt）

### 风险评估
- **低风险**: 不影响核心功能，可以随时关闭
- **AI 质量**: 生成的问题质量需要监控和优化
- **性能影响**: 无明显性能影响（不增加 API 调用）

---

## 三、技术架构设计

### 整体流程
```
用户提问 → AI 生成回复 + 推荐问题 → 前端解析 → 展示推荐按钮 → 用户点击 → 直接发送
```

### System Prompt 修改

在现有的 system prompt 末尾添加以下指令：

```
在每次回复的最后，请生成 4 个用户可能感兴趣的后续问题。
使用以下格式（必须严格遵守）：

---SUGGESTED_QUESTIONS---
1. 问题文本1
2. 问题文本2
3. 问题文本3
4. 问题文本4
---END_SUGGESTED_QUESTIONS---

要求：
- 问题要基于当前对话内容，具有针对性
- 问题长度控制在 15-30 字
- 涵盖不同维度（事业、感情、健康、财运等）
- 使用疑问句形式
```

### 数据格式示例

```
AI 正常回复内容...

根据您的八字，今年财运较旺...

---SUGGESTED_QUESTIONS---
1. 今年适合投资理财吗？
2. 我的事业运势如何？
3. 什么时候会遇到贵人？
4. 如何化解流年不利？
---END_SUGGESTED_QUESTIONS---
```

---

## 四、前端实现方案

### 1. 解析工具

**文件**: `fate-frontend/app/lib/chat/parser.ts`（新建）

```typescript
export interface SuggestedQuestions {
  questions: string[];
  cleanedContent: string; // 移除标记后的内容
}

export function parseSuggestedQuestions(content: string): SuggestedQuestions {
  const regex = /---SUGGESTED_QUESTIONS---([\s\S]*?)---END_SUGGESTED_QUESTIONS---/;
  const match = content.match(regex);
  
  if (!match) {
    return { questions: [], cleanedContent: content };
  }
  
  const questionsText = match[1].trim();
  const questions = questionsText
    .split('\n')
    .map(line => line.replace(/^\d+\.\s*/, '').trim())
    .filter(q => q.length > 0);
  
  const cleanedContent = content.replace(regex, '').trim();
  
  return { questions, cleanedContent };
}
```

### 2. UI 组件

**文件**: `fate-frontend/app/components/chat/SuggestedQuestions.tsx`（新建）

```typescript
'use client';

interface SuggestedQuestionsProps {
  questions: string[];
  onQuestionClick: (question: string) => void;
  loading?: boolean;
}

export function SuggestedQuestions({ 
  questions, 
  onQuestionClick,
  loading = false 
}: SuggestedQuestionsProps) {
  if (questions.length === 0) return null;
  
  return (
    <div className="mt-4 space-y-2">
      <div className="text-xs text-[var(--color-text-muted)] font-medium">
        猜你想问
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {questions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => onQuestionClick(q)}
            disabled={loading}
            className="text-left px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-elevated)] hover:border-[var(--color-primary)]/40 hover:bg-[var(--color-primary)]/5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
```

### 3. 消息类型扩展

**文件**: `fate-frontend/app/lib/chat/types.ts`

```typescript
export type Msg = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  streaming?: boolean;
  meta?: { kind: string };
  suggestedQuestions?: string[]; // 新增字段
};
```

---

## 五、集成到现有页面

### 修改聊天页面逻辑

**文件**: `fate-frontend/app/chat/page.tsx` 和 `fate-frontend/app/panel/page.tsx`

#### 1. 导入解析工具

```typescript
import { parseSuggestedQuestions } from '@/app/lib/chat/parser';
```

#### 2. 在 SSE 流式接收完成后解析

找到处理 AI 回复完成的代码（通常在 `[DONE]` 事件处理中），添加解析逻辑：

```typescript
// 在接收到完整回复后
const { questions, cleanedContent } = parseSuggestedQuestions(fullText);

setMsgs(prev => {
  const updated = [...prev];
  if (aiIndexRef.current !== null && updated[aiIndexRef.current]) {
    updated[aiIndexRef.current] = {
      ...updated[aiIndexRef.current],
      content: cleanedContent,
      suggestedQuestions: questions,
      streaming: false,
    };
  }
  return updated;
});
```

#### 3. 添加点击处理函数

```typescript
const handleQuestionClick = async (question: string) => {
  if (loading) return;
  
  // 直接发送问题（复用现有的发送逻辑）
  setInput(question);
  
  // 添加用户消息
  setMsgs(prev => [...prev, { role: 'user', content: question }]);
  
  // 触发 AI 回复（复用现有逻辑）
  // ... 调用 handleSend 或相关函数
};
```

### 修改 MessageList 组件

**文件**: `fate-frontend/app/components/chat/MessageList.tsx`

#### 1. 导入组件

```typescript
import { SuggestedQuestions } from './SuggestedQuestions';
```

#### 2. 在渲染消息时添加推荐问题

找到渲染 assistant 消息的地方，添加：

```typescript
{msg.role === 'assistant' && !msg.streaming && msg.suggestedQuestions && (
  <SuggestedQuestions
    questions={msg.suggestedQuestions}
    onQuestionClick={onQuestionClick}
    loading={loading}
  />
)}
```

#### 3. 传递 props

确保 MessageList 组件接收 `onQuestionClick` 和 `loading` props：

```typescript
interface MessageListProps {
  // ... 现有 props
  onQuestionClick: (question: string) => void;
  loading: boolean;
}
```

---

## 六、错误处理与边界情况

### 1. AI 未生成推荐问题

```typescript
// 解析函数已处理：返回空数组
// 组件会自动隐藏（questions.length === 0）

// 可选：添加降级方案（首次回复时）
const FALLBACK_QUESTIONS = [
  '我的事业运势如何？',
  '今年财运怎么样？',
  '感情方面有什么建议？',
  '如何提升运势？',
];
```

### 2. 格式错误的容错

```typescript
export function parseSuggestedQuestions(content: string): SuggestedQuestions {
  // 支持多种格式变体
  const patterns = [
    /---SUGGESTED_QUESTIONS---([\s\S]*?)---END_SUGGESTED_QUESTIONS---/,
    /【推荐问题】([\s\S]*?)【结束】/,
    /\[建议问题\]([\s\S]*?)\[\/建议问题\]/,
  ];
  
  for (const pattern of patterns) {
    const match = content.match(pattern);
    if (match) {
      // 解析逻辑...
      const questionsText = match[1].trim();
      const questions = questionsText
        .split('\n')
        .map(line => line.replace(/^\d+\.\s*/, '').trim())
        .filter(q => q.length > 0 && q.length <= 50); // 过滤异常长度
      
      const cleanedContent = content.replace(pattern, '').trim();
      return { questions, cleanedContent };
    }
  }
  
  return { questions: [], cleanedContent: content };
}
```

### 3. 防止重复点击

```typescript
const [sendingQuestion, setSendingQuestion] = useState(false);

const handleQuestionClick = async (question: string) => {
  if (sendingQuestion || loading) return;
  
  setSendingQuestion(true);
  try {
    await handleSend(question);
  } finally {
    setSendingQuestion(false);
  }
};
```

### 4. 流式输出时的处理

- 只有当 `streaming: false` 时才渲染 SuggestedQuestions 组件
- 避免用户在 AI 还在输出时就点击推荐问题
- 在组件中添加 `!msg.streaming` 判断

---

## 七、测试方案

### 1. 单元测试

**文件**: `fate-frontend/app/lib/chat/parser.test.ts`（新建）

```typescript
import { parseSuggestedQuestions } from './parser';

describe('parseSuggestedQuestions', () => {
  it('应该正确解析标准格式', () => {
    const content = `回复内容
---SUGGESTED_QUESTIONS---
1. 问题1
2. 问题2
3. 问题3
4. 问题4
---END_SUGGESTED_QUESTIONS---`;
    
    const result = parseSuggestedQuestions(content);
    expect(result.questions).toEqual(['问题1', '问题2', '问题3', '问题4']);
    expect(result.cleanedContent).toBe('回复内容');
  });
  
  it('应该处理没有推荐问题的情况', () => {
    const content = '普通回复内容';
    const result = parseSuggestedQuestions(content);
    expect(result.questions).toEqual([]);
    expect(result.cleanedContent).toBe('普通回复内容');
  });
  
  it('应该过滤空行和异常格式', () => {
    const content = `回复内容
---SUGGESTED_QUESTIONS---
1. 问题1

2. 问题2
问题3
---END_SUGGESTED_QUESTIONS---`;
    
    const result = parseSuggestedQuestions(content);
    expect(result.questions.length).toBeGreaterThan(0);
  });
});
```

### 2. 集成测试场景

- ✅ 完整对话流程：提问 → AI 回复 → 显示推荐 → 点击 → 发送
- ✅ 流式输出时推荐问题的显示时机
- ✅ 多轮对话中推荐问题的更新
- ✅ 推荐问题为空时的隐藏
- ✅ 快速连续点击的防抖处理

### 3. 用户测试

- **A/B 测试**: 50% 用户看到推荐问题，50% 不看到
- **监控指标**:
  - 会话轮次变化
  - 推荐问题点击率
  - 用户停留时间
  - 用户满意度评分

---

## 八、实施步骤

### 第一阶段：后端准备（1-2 小时）

1. **修改 system prompt**
   - 文件: `fate/app/routers/chat.py` 或数据库中的 `app_config` 表
   - 在现有 prompt 末尾添加推荐问题生成指令
   - 测试 AI 是否能稳定生成符合格式的推荐问题

2. **验证生成质量**
   - 进行 10-20 次测试对话
   - 检查推荐问题的相关性和质量
   - 调整 prompt 直到满意

### 第二阶段：前端开发（1 天）

1. **创建基础工具**（30 分钟）
   - 创建 `parser.ts` 解析工具
   - 编写单元测试

2. **创建 UI 组件**（1 小时）
   - 创建 `SuggestedQuestions.tsx` 组件
   - 添加样式和动画效果
   - 测试响应式布局

3. **集成到聊天页面**（2-3 小时）
   - 修改消息类型定义
   - 修改 `chat/page.tsx`
   - 修改 `panel/page.tsx`
   - 修改 `MessageList.tsx`
   - 添加点击处理逻辑

4. **错误处理**（1 小时）
   - 添加降级方案
   - 添加格式容错
   - 添加防重复点击

### 第三阶段：测试优化（半天）

1. **功能测试**
   - 测试各种对话场景
   - 测试边界情况
   - 测试移动端体验

2. **修复问题**
   - 修复发现的 bug
   - 优化交互体验
   - 调整样式细节

3. **性能测试**
   - 测试解析性能
   - 测试渲染性能
   - 优化必要的地方

### 第四阶段：上线监控（持续）

1. **灰度发布**
   - 10% 用户 → 观察 1-2 天
   - 50% 用户 → 观察 2-3 天
   - 100% 用户 → 全量上线

2. **数据监控**
   - 推荐问题点击率
   - 会话轮次变化
   - 用户停留时间
   - 错误日志

3. **持续优化**
   - 收集用户反馈
   - 优化 prompt 质量
   - 调整推荐策略

---

## 九、预期效果

### 核心指标
- **会话轮次**: 提升 30-50%
- **用户停留时间**: 增加 20-30%
- **推荐问题点击率**: 15-25%
- **用户满意度**: 提升 10-15%

### 成功标准
- ✅ 推荐问题生成成功率 > 95%
- ✅ 推荐问题点击率 > 15%
- ✅ 无明显性能影响
- ✅ 用户反馈正面

---

## 十、关键文件清单

### 需要创建的文件
1. `fate-frontend/app/lib/chat/parser.ts` - 解析工具
2. `fate-frontend/app/lib/chat/parser.test.ts` - 单元测试
3. `fate-frontend/app/components/chat/SuggestedQuestions.tsx` - UI 组件

### 需要修改的文件
1. `fate-frontend/app/lib/chat/types.ts` - 添加 suggestedQuestions 字段
2. `fate-frontend/app/chat/page.tsx` - 集成解析和点击逻辑
3. `fate-frontend/app/panel/page.tsx` - 集成解析和点击逻辑
4. `fate-frontend/app/components/chat/MessageList.tsx` - 渲染推荐问题
5. `fate/app/routers/chat.py` 或数据库 - 修改 system prompt

---

## 十一、风险与应对

### 风险1：AI 生成质量不稳定
**应对**: 
- 添加降级方案（预设问题）
- 持续优化 prompt
- 监控生成质量并及时调整

### 风险2：用户不点击推荐问题
**应对**:
- 优化问题质量和相关性
- 调整 UI 设计，提高吸引力
- A/B 测试不同的展示方式

### 风险3：增加用户认知负担
**应对**:
- 保持简洁的 UI 设计
- 限制问题数量（4 个）
- 可以添加"收起"功能

---

## 十二、后续优化方向

1. **智能排序**: 根据用户历史行为，调整推荐问题的顺序
2. **个性化**: 基于用户画像生成更个性化的问题
3. **多样性**: 确保推荐问题涵盖不同维度
4. **学习优化**: 根据点击数据优化问题生成策略
5. **多语言支持**: 如果需要支持其他语言

---

**文档版本**: v1.0  
**最后更新**: 2026-04-03
