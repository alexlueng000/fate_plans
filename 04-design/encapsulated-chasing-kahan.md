# 优化首页和 Panel 页日期时间选择器

## 问题分析

### 当前状态

| 页面 | 日期选择器 | 时间选择器 | 样式 |
|------|-----------|-----------|------|
| 首页 (`page.tsx`) | 原生 `<input type="date">` | 原生 `<input type="time">` | 灰色背景 + 主色调边框 |
| Panel (`panel/page.tsx`) | `PrettyDateField` (带清空按钮) | `IOSWheelTime` (滚轮选择器) | 奶油色背景 + 金色边框 |

### 主要问题
1. **体验不一致**: Panel 页面的 iOS 风格滚轮时间选择器体验更好，首页使用原生控件
2. **样式不统一**: 两个页面的颜色、边框、图标大小都不同
3. **Android 体验差**: 原生 HTML5 日期/时间选择器在 Android 上问题严重：
   - 不同厂商/版本的选择器样式差异大
   - 日期/时间选择操作繁琐（需要多次点击）
   - 部分机型弹出键盘而非选择器
4. **移动端体验**: 原生控件在触摸设备上不够友好

---

## 实现方案

### 策略：创建统一的 iOS 风格滚轮选择器

1. **使用 frontend-design skill**: 先设计组件的视觉样式
2. **时间选择器**: 复用现有的 `IOSWheelTime` 组件，添加主题支持
3. **日期选择器**: 新建 `IOSWheelDate` 组件，采用相同的滚轮交互模式

---

## 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/components/form/dateTimeThemes.ts` | 新建 | 主题配置 |
| `app/components/DatePicker.tsx` | 新建 | iOS 风格滚轮日期选择器 |
| `app/components/TimePicker.tsx` | 修改 | 添加 `theme` 属性 |
| `app/components/Calender.tsx` | 修改 | 添加 `theme` 属性，内部使用新日期选择器 |
| `app/page.tsx` | 修改 | 替换原生输入为自定义组件 |

---

## 详细实现步骤

### 步骤 0: 使用 frontend-design skill 设计组件样式

在实现组件之前，先使用 `/frontend-design` skill 设计日期和时间选择器的视觉样式：

**设计要求**：
- iOS 风格滚轮选择器
- 支持两套主题（landing 页灰色调、panel 页奶油色调）
- 移动端友好的触摸交互
- 中线选中框视觉反馈
- 弹层样式（边框、按钮、背景）

**输出**：
- 完整的组件样式设计
- Tailwind CSS 类名配置
- 主题变量定义

### 步骤 1: 创建主题配置文件

**文件**: `app/components/form/dateTimeThemes.ts`

```typescript
export type DateTimeTheme = 'landing' | 'panel';

export const dateTimeThemes = {
  landing: {
    // 触发器样式
    trigger: 'bg-[var(--color-bg-deep)] border-2 border-transparent focus:border-[var(--color-primary)] focus:bg-white',
    triggerPadding: 'pl-12 pr-4 py-3.5',
    // 弹层样式
    popup: 'border-[var(--color-border)] bg-white',
    popupBorder: 'border-[var(--color-border)]',
    popupButton: 'bg-[var(--color-primary)] text-white hover:opacity-90',
    popupButtonSecondary: 'border-[var(--color-border)] bg-white text-neutral-700 hover:bg-neutral-50',
    // 选中高亮
    selectedText: 'text-[var(--color-primary)] font-semibold',
    // 图标
    iconColor: 'text-[var(--color-text-hint)]',
    iconSize: 'w-5 h-5',
  },
  panel: {
    trigger: 'bg-[#fff7ed] border border-[#f0d9a6] focus:ring-2 focus:ring-red-400',
    triggerPadding: 'pl-9 pr-9 py-2',
    popup: 'border-[#f0d9a6] bg-white',
    popupBorder: 'border-[#f0d9a6]',
    popupButton: 'bg-[#a83232] text-[#fff7e8] hover:bg-[#8c2b2b]',
    popupButtonSecondary: 'border-[#f0d9a6] bg-white text-neutral-700 hover:bg-[#fff7ed]',
    selectedText: 'text-[#a83232] font-semibold',
    iconColor: 'text-red-600/70',
    iconSize: 'w-4 h-4',
  },
};
```

### 步骤 2: 创建 iOS 风格日期选择器

**文件**: `app/components/DatePicker.tsx`

参考 `IOSWheelTime` 的实现，创建三列滚轮选择器：
- **年份列**: 1900 - 当前年份
- **月份列**: 1 - 12
- **日期列**: 根据年月动态计算 (1-28/29/30/31)

核心功能：
- 滚轮滚动选择，支持惯性滚动和自动吸附
- 中线选中框视觉反馈
- 点击外部/ESC 关闭
- 清空和确认按钮
- 支持主题配置

```typescript
type IOSWheelDateProps = {
  value: string;                    // 'YYYY-MM-DD' | ''
  onChange: (v: string) => void;
  placeholder?: string;             // '年 / 月 / 日'
  disabled?: boolean;
  min?: string;                     // 最小日期
  max?: string;                     // 最大日期 (默认今天)
  attachToBody?: boolean;
  theme?: DateTimeTheme;
};
```

### 步骤 3: 修改 TimePicker.tsx

添加 `theme` 属性，根据主题动态应用样式：

```typescript
import { DateTimeTheme, dateTimeThemes } from './form/dateTimeThemes';

type IOSWheelTimeProps = {
  // ... 现有属性
  theme?: DateTimeTheme;  // 新增
};

export function IOSWheelTime({ ..., theme = 'panel' }: IOSWheelTimeProps) {
  const themeConfig = dateTimeThemes[theme];
  // 使用 themeConfig 替换硬编码的样式
}
```

主要修改点：
- 触发器按钮样式 (第 204 行): `themeConfig.trigger`
- 弹层边框颜色 (第 124 行): `themeConfig.popupBorder`
- 确认按钮样式 (第 133 行): `themeConfig.popupButton`
- 清空按钮样式 (第 132 行): `themeConfig.popupButtonSecondary`
- 选中项高亮 (第 159, 182 行): `themeConfig.selectedText`

### 步骤 4: 修改 Calender.tsx (PrettyDateField)

更新组件使用新的 `IOSWheelDate`：

```typescript
import { IOSWheelDate } from './DatePicker';
import { DateTimeTheme } from './form/dateTimeThemes';

export function PrettyDateField({
  // ... 现有属性
  theme = 'panel',
}: {
  // ... 现有类型
  theme?: DateTimeTheme;
}) {
  return (
    <IOSWheelDate
      value={value}
      onChange={onChange}
      max={max}
      theme={theme}
      attachToBody
    />
  );
}
```

### 步骤 5: 修改首页 page.tsx

替换原生输入控件 (第 202-221 行)：

```tsx
import { PrettyDateField } from '@/app/components/Calender';
import { IOSWheelTime } from '@/app/components/TimePicker';

// 替换日期输入
<div className="relative">
  <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-hint)] z-10 pointer-events-none" />
  <PrettyDateField
    value={birthDate}
    onChange={setBirthDate}
    theme="landing"
  />
</div>

// 替换时间输入
<div className="relative">
  <Clock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-hint)] z-10 pointer-events-none" />
  <IOSWheelTime
    value={birthTime}
    onChange={setBirthTime}
    theme="landing"
    attachToBody
  />
</div>
```

---

## 验证方案

1. **开发环境测试**
   ```bash
   cd fate-frontend
   npm run dev
   ```

2. **功能验证**
   - 访问首页 `http://localhost:3000`，测试日期/时间选择
   - 访问 Panel 页 `http://localhost:3000/panel`，确认原有功能正常
   - 测试日期选择器的年月日联动（如 2 月天数变化）

3. **移动端测试**
   - Chrome DevTools 模拟 Android 设备
   - 测试滚轮的触摸滚动和惯性效果
   - 验证弹层定位在不同屏幕尺寸下正确

4. **样式验证**
   - 首页：灰色背景、主色调边框、大图标
   - Panel：奶油色背景、金色边框、小图标

5. **构建验证**
   ```bash
   npm run build
   ```

---

## 预期效果

- 首页和 Panel 页都使用 iOS 风格滚轮选择器（日期 + 时间）
- 两个页面保持各自的视觉风格
- **Android 体验大幅提升**：纯 Web 实现，所有设备表现一致
- 移动端触摸体验统一且友好
- 代码复用，减少维护成本

---

## 关于 Android 兼容性

自定义滚轮选择器的优势：
- **纯 Web 实现**：不依赖浏览器原生控件，所有平台表现一致
- **触摸优化**：支持惯性滚动和自动吸附，触摸体验流畅
- **视觉反馈**：中线选中框清晰指示当前选择
- **操作简单**：滚动选择 + 点击确认，比原生控件更直观
- **样式可控**：完全自定义外观，与应用风格统一

---

## 日期选择器实现细节

### 年月日联动逻辑

```typescript
// 根据年月计算当月天数
function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

// 当年或月变化时，自动调整日期
useEffect(() => {
  const maxDay = getDaysInMonth(year, month);
  if (day > maxDay) {
    setDay(maxDay);
  }
}, [year, month]);
```

### 年份范围

- 默认范围: 1900 - 当前年份
- 八字应用场景: 用户选择出生日期，通常在过去
- 可通过 `min`/`max` 属性自定义范围

### 滚轮参数

```typescript
const ROW_H = 36;      // 每行高度
const VISIBLE = 5;     // 显示 5 行（中间为选中）
const VIEW_H = ROW_H * VISIBLE;
```
