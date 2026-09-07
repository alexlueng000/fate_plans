# Fate Frontend 重构设计方案

## 产品定位
- **传统文化知识的解释者** - 强调教育性、知识传播
- **基于概率模型的趋势分析工具** - 强调科学性、数据分析

## 设计方向
- 视觉风格：文化+科技融合
- 核心功能：上方数据仪表盘 + 下方智能对话
- 范围：全部页面重设计
- **免登录体验**：用户无需注册登录即可免费体验一次完整解读

---

## 一、设计系统

### 1.1 配色方案

```css
/* 主色系 - 传统朱红 */
--primary-500: #c93b3a;
--primary-600: #a82820;

/* 辅助色 - 金色 */
--gold-400: #C4A574;
--gold-500: #A67C52;

/* 科技蓝 - 数据可视化 */
--tech-500: #3b82f6;
--tech-600: #2563eb;

/* 五行色系 */
--wuxing-wood: #10b981;
--wuxing-fire: #ef4444;
--wuxing-earth: #f59e0b;
--wuxing-metal: #eab308;
--wuxing-water: #0ea5e9;

/* 背景色 */
--surface-primary: #f7f3ed;
--surface-secondary: #fffbf7;
--surface-elevated: #ffffff;
```

### 1.2 字体系统
- 正文：Inter + Noto Sans SC
- 标题：Noto Serif SC（传统感）
- 代码：JetBrains Mono

---

## 二、页面设计

### 2.1 首页 Landing Page (`/`) - 含免登录体验入口

**核心功能：免登录体验**
- 首页直接嵌入排盘表单，用户无需登录即可输入出生信息
- 点击"开始解读"后直接进入体验页面 `/try`
- 体验完成后引导注册（保存记录、继续对话）

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  Hero Section                                │
│  标题: "解读命理智慧，洞察人生趋势"            │
│  副标题: 传统文化知识 × 概率模型分析           │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  快速体验表单（无需登录）                 │ │
│  │  性别: [男/女]                           │ │
│  │  出生日期: [____年__月__日]              │ │
│  │  出生时间: [__:__]                       │ │
│  │  [立即免费解读]                          │ │
│  └────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│  双定位展示区                                │
│  [知识解释者] | [趋势分析工具]               │
├─────────────────────────────────────────────┤
│  数据能力展示 - 动态图表演示                  │
├─────────────────────────────────────────────┤
│  使用流程 - 3步引导                          │
├─────────────────────────────────────────────┤
│  FAQ + CTA                                   │
└─────────────────────────────────────────────┘
```

**关键文件：** `app/page.tsx`

### 2.2 免登录体验页 (`/try`) - 新增

**功能说明：**
- 无需登录即可使用的完整体验页面
- 展示命盘数据仪表盘 + AI解读
- 限制：只能进行一次初始解读，不能追问
- 体验结束后显示注册引导弹窗

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  顶部提示条: "您正在体验免费版，注册解锁更多" │
├─────────────────────────────────────────────┤
│  数据仪表盘（与Panel相同）                   │
│  四柱命盘 | 五行雷达图 | 大运时间轴           │
├─────────────────────────────────────────────┤
│  AI解读内容（只读，流式展示）                │
├─────────────────────────────────────────────┤
│  底部CTA                                     │
│  [注册账号，保存记录] [继续提问（需登录）]    │
└─────────────────────────────────────────────┘
```

**关键文件：** `app/try/page.tsx` (新建)

### 2.3 核心工作台 Panel (`/panel`)

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  数据仪表盘区域                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │排盘表单   │ │四柱命盘   │ │五行雷达图 │    │
│  └──────────┘ └──────────┘ └──────────┘    │
│  ┌──────────────────────────────────────┐  │
│  │  大运流年趋势图（可交互时间轴）         │  │
│  └──────────────────────────────────────┘  │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐              │
│  │日主│ │用神│ │格局│ │评分│ 指标卡片      │
│  └────┘ └────┘ └────┘ └────┘              │
├─────────────────────────────────────────────┤
│  智能对话区域                                │
│  ┌──────────────────────────────────────┐  │
│  │  知识卡片（术语解释、文化背景）         │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │  消息列表                              │  │
│  └──────────────────────────────────────┘  │
│  [性格] [事业] [财运] [感情] [健康] 快捷按钮 │
│  [输入框] [发送] [重新解读] [清空]          │
└─────────────────────────────────────────────┘
```

**关键文件：** `app/panel/page.tsx`

### 2.4 登录/注册页
- 简洁专业风格
- 渐变背景 + 微妙八卦纹理
- 品牌一致性

**关键文件：** `app/(auth)/login/LoginClient.tsx`, `app/(auth)/register/page.tsx`

### 2.5 账户页 (`/account`)
- 用户信息卡片
- 账户设置
- 历史记录

### 2.6 管理后台 (`/admin/*`)
- 侧边导航布局
- 功能性优先

---

## 三、新增组件

### 3.1 数据可视化组件
| 组件 | 路径 | 功能 |
|------|------|------|
| WuxingRadar | `app/components/charts/WuxingRadar.tsx` | 五行分布雷达图 |
| DayunTimeline | `app/components/charts/DayunTimeline.tsx` | 大运流年时间轴 |
| TrendChart | `app/components/charts/TrendChart.tsx` | 趋势分析折线图 |
| MetricCard | `app/components/charts/MetricCard.tsx` | 指标卡片 |

### 3.2 文化元素组件
| 组件 | 路径 | 功能 |
|------|------|------|
| AnimatedBagua | `app/components/cultural/AnimatedBagua.tsx` | 八卦动画 |
| PillarCard | `app/components/cultural/PillarCard.tsx` | 四柱卡片（增强版） |
| WuxingIcon | `app/components/cultural/WuxingIcon.tsx` | 五行图标 |

### 3.3 仪表盘组件
| 组件 | 路径 | 功能 |
|------|------|------|
| Dashboard | `app/components/dashboard/Dashboard.tsx` | 仪表盘容器 |
| PaipanForm | `app/components/dashboard/PaipanForm.tsx` | 排盘表单（可折叠） |
| PaipanVisualizer | `app/components/dashboard/PaipanVisualizer.tsx` | 命盘可视化 |

### 3.4 聊天增强组件
| 组件 | 路径 | 功能 |
|------|------|------|
| KnowledgePanel | `app/components/chat/KnowledgePanel.tsx` | 知识卡片面板 |
| KnowledgeCard | `app/components/chat/KnowledgeCard.tsx` | 单个知识卡片 |
| EnhancedMessage | `app/components/chat/EnhancedMessage.tsx` | 增强消息气泡 |

### 3.5 通用UI组件
| 组件 | 路径 |
|------|------|
| Button | `app/components/ui/Button.tsx` |
| Card | `app/components/ui/Card.tsx` |
| Input | `app/components/ui/Input.tsx` |
| Modal | `app/components/ui/Modal.tsx` |
| Tabs | `app/components/ui/Tabs.tsx` |
| Tooltip | `app/components/ui/Tooltip.tsx` |
| Skeleton | `app/components/ui/Skeleton.tsx` |

---

## 四、数据可视化方案

### 技术选型
使用 **Recharts** - 轻量级，React 集成良好

### 图表类型
1. **五行雷达图** - 展示五行分布比例
2. **大运时间轴** - 可交互，悬停显示详情
3. **趋势折线图** - 事业/财运/感情/健康多维度

---

## 五、实施步骤

### Step 1: 设计系统基础
- [x] 创建 `app/lib/design-tokens.ts` 设计token文件
- [x] 更新 `app/globals.css` 全局样式
- [x] 安装 recharts 依赖

### Step 2: 通用UI组件
- [x] 创建 `app/components/ui/` 目录
- [x] 实现 Button, Card, Input, Modal, Tabs, Tooltip, Skeleton 组件

### Step 3: 数据可视化组件
- [x] 创建 `app/components/charts/` 目录
- [x] 实现 WuxingRadar 五行雷达图
- [x] 实现 DayunTimeline 大运时间轴
- [x] 实现 MetricCard 指标卡片

### Step 4: 文化元素组件
- [x] 创建 `app/components/cultural/` 目录
- [x] 实现 AnimatedBagua 八卦动画
- [x] 实现 PillarCard 四柱卡片
- [x] 实现 WuxingIcon 五行图标

### Step 5: 核心页面重构 - Panel
- [x] 重构 `app/panel/page.tsx` 为仪表盘+聊天布局
- [x] 创建 Dashboard 容器组件
- [x] 集成数据可视化组件
- [x] 实现 KnowledgePanel 知识卡片

### Step 6: 首页重设计（含免登录入口）
- [x] 重构 `app/page.tsx`
- [x] 实现 Hero Section 带快速体验表单
- [x] 实现双定位展示区
- [x] 实现数据能力展示区

### Step 7: 免登录体验页
- [x] 创建 `app/try/page.tsx`
- [x] 复用仪表盘组件展示命盘
- [x] 实现只读AI解读流式展示
- [x] 实现注册引导弹窗

### Step 8: 登录/注册页
- [x] 重构 `app/(auth)/login/LoginClient.tsx`
- [x] 重构 `app/(auth)/register/page.tsx`

### Step 9: 账户页和管理后台
- [x] 重构 `app/account/page.tsx`
- [x] 重构 `app/(auth)/admin/` 管理后台

---

## 六、关键文件清单

| 文件 | 操作 |
|------|------|
| `app/lib/design-tokens.ts` | 新建 |
| `app/globals.css` | 修改 |
| `app/page.tsx` | 重构 |
| `app/try/page.tsx` | 新建（免登录体验页） |
| `app/panel/page.tsx` | 重构 |
| `app/(auth)/login/LoginClient.tsx` | 重构 |
| `app/(auth)/register/page.tsx` | 重构 |
| `app/account/page.tsx` | 重构 |
| `app/components/ui/*` | 新建 |
| `app/components/charts/*` | 新建 |
| `app/components/cultural/*` | 新建 |
| `app/components/dashboard/*` | 新建 |
| `app/components/chat/KnowledgePanel.tsx` | 新建 |

---

## 七、验证方案

### 开发验证
```bash
cd fate-frontend
npm run dev
# 访问 http://localhost:3000 验证各页面
```

### 检查清单
- [ ] 首页正确展示双定位信息和快速体验表单
- [ ] 免登录体验页 `/try` 正常工作
- [ ] Panel 页面仪表盘+聊天布局正常
- [ ] 五行雷达图正确渲染
- [ ] 大运时间轴可交互
- [ ] 知识卡片正常展示
- [ ] 登录/注册流程正常
- [ ] 响应式布局在移动端正常
- [ ] 所有页面风格统一
