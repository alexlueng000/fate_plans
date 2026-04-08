# 八字排盘卡片UI改造计划

## Context（背景）

用户希望改造 `/panel` 页面中的八字排盘展示界面，使其更加美观和专业。用户提供了两张设计参考图：

1. **第一张图**：简洁的卡片式设计，四个柱子（年月日时）横向排列，每个柱子是独立的圆角卡片，显示天干地支和五行标签，日柱有黄色高亮，底部显示大运列表
2. **第二张图**：详细的表格视图，包含更多专业信息（藏干、副星、星运、自坐、空亡、纳音、神煞等）

用户需求：
- 只改造 `/panel` 页面的排盘展示
- 同时提供简洁卡片视图和详细表格视图
- 用户可以在两种视图之间切换

## Implementation Plan（实现方案）

### 第一阶段：改造简洁卡片视图

#### 1. 修改 SimplifiedPaipanCard 组件

**文件**: `E:\claude_projects\chat\fate-frontend\app\components\chat\SimplifiedPaipanCard.tsx`

**主要改动**：

1. **更新柱子样式配置**
   - 年柱和月柱使用浅绿色背景（`bg-emerald-50/40`）
   - 日柱使用浅黄色背景（`bg-amber-50`）并添加金色阴影和边框高亮
   - 时柱使用浅灰色背景（`bg-gray-50`）
   - 所有卡片使用更大的圆角（`rounded-xl`）和更粗的边框（`border-2`）

2. **优化五行标签样式**
   - 增大字体（`text-[10px]`）
   - 使用更圆润的形状（`rounded-full`）
   - 调整内边距（`px-2 py-0.5`）
   - 增加上边距（`mt-1.5`）

3. **调整卡片布局**
   - 天干和地支字体增大（`text-2xl sm:text-3xl`）
   - 增加卡片内边距（`px-2 py-3`）
   - 优化分隔线样式（虚线，更淡的颜色）
   - 日主标记移到卡片下方

4. **优化大运列表**
   - 增大卡片尺寸（`min-w-[60px] sm:min-w-[70px]`）
   - 使用更大圆角（`rounded-xl`）和更粗边框（`border-2`）
   - 当前大运添加缩放效果（`scale-105`）
   - 添加悬停效果

5. **添加交互动画**
   - 卡片悬停时显示更大阴影（`hover:shadow-lg`）
   - 所有过渡使用 `transition-all duration-200`

#### 2. 更新全局样式

**文件**: `E:\claude_projects\chat\fate-frontend\app\globals.css`

**改动**：
- 调整 `.wuxing-*` 类的背景透明度和边框颜色
- 使用更柔和的颜色（`rgba` 格式，透明度 0.08-0.12）

### 第二阶段：创建详细表格视图

#### 3. 创建 DetailedPaipanTable 组件

**文件**: `E:\claude_projects\chat\fate-frontend\app\components\chat\DetailedPaipanTable.tsx`（新建）

**功能**：
- 显示完整的八字排盘表格
- 包含以下信息行：
  - 日期（农历、阳历）
  - 年柱、月柱、日柱、时柱
  - 主星（偏财、七杀、元男等）
  - 天干（带五行标签和图标）
  - 地支（带五行标签和图标）
  - 藏干（辛金、乙木、己土等）
  - 副星（食神、七杀、比肩等）
  - 星运（长生、病、墓等）
  - 自坐（病、临官、墓等）
  - 空亡（戌亥、子丑、午未等）
  - 纳音（剑锋金、大溪水、霹雳火等）
  - 神煞（文昌贵人、天乙贵人、福星贵人等）

**设计要点**：
- 使用表格布局（`<table>` 或 CSS Grid）
- 天干地支使用五行颜色标注
- 重要信息（如日柱）使用高亮
- 响应式设计，小屏幕可横向滚动

**数据来源**：
需要扩展后端 API `/api/bazi/calc_paipan` 返回以下额外信息：

1. **藏干**（地支藏干）
   - 每个地支包含的天干
   - 例如：子藏癸，丑藏己癸辛，寅藏甲丙戊等
   - 使用 `lunar-python` 的 `DiZhi.getHideGan()` 方法

2. **十神**（主星/副星）
   - 以日干为主，计算其他三柱的十神关系
   - 十神：比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印
   - 使用 `EightChar` 的 `getShiShenGan()` 和 `getShiShenZhi()` 方法

3. **十二长生**（星运）
   - 日干在各地支的长生状态
   - 十二长生：长生、沐浴、冠带、临官、帝旺、衰、病、死、墓、绝、胎、养
   - 使用 `EightChar` 的相关方法

4. **自坐**
   - 日柱天干在日柱地支的十二长生状态

5. **空亡**
   - 根据日柱计算空亡的地支
   - 使用 `EightChar.getXunKong()` 方法

6. **纳音**（六十甲子纳音）
   - 年柱、月柱、日柱、时柱的纳音五行
   - 例如：剑锋金、大溪水、霹雳火等
   - 使用 `LunarUtil.NAYIN` 映射表

7. **神煞**
   - 天乙贵人、文昌贵人、福星贵人、将星、太极贵人、六秀日、月德合、华盖等
   - 使用 `EightChar.getShenSha()` 方法

### 第三阶段：添加视图切换功能

#### 4. 修改 /panel 页面

**文件**: `E:\claude_projects\chat\fate-frontend\app\panel\page.tsx`

**改动**：

1. **添加视图切换状态**
   ```typescript
   const [viewMode, setViewMode] = useState<'card' | 'table'>('card');
   ```

2. **添加切换按钮**
   - 在排盘卡片顶部添加两个按钮：「简洁视图」和「详细视图」
   - 使用图标（如卡片图标和表格图标）
   - 当前视图高亮显示

3. **条件渲染组件**
   ```typescript
   {viewMode === 'card' ? (
     <SimplifiedPaipanCard paipan={paipan} />
   ) : (
     <DetailedPaipanTable paipan={paipan} />
   )}
   ```

4. **保存用户偏好**
   - 将视图模式保存到 `localStorage`
   - 下次打开页面时恢复用户选择

### 第四阶段：数据获取方案（二选一）

#### 方案A：后端计算（简单但增加后端负担）

**文件**: `E:\claude_projects\chat\fate\app\routers\bazi.py`

**改动**：

在 `calc_paipan` 函数中添加以下计算：

```python
# 在现有的 four_pillars 和 dayun 计算之后添加：

# 5) 藏干（地支藏干）
cang_gan = {
    "year": eight_char.getYearZhi().getHideGan(),
    "month": eight_char.getMonthZhi().getHideGan(),
    "day": eight_char.getDayZhi().getHideGan(),
    "hour": eight_char.getTimeZhi().getHideGan(),
}

# 6) 十神（主星）
shi_shen_gan = {
    "year": eight_char.getYearShiShenGan(),
    "month": eight_char.getMonthShiShenGan(),
    "day": eight_char.getDayShiShenGan(),
    "hour": eight_char.getTimeShiShenGan(),
}

shi_shen_zhi = {
    "year": eight_char.getYearShiShenZhi()[0] if eight_char.getYearShiShenZhi() else "",
    "month": eight_char.getMonthShiShenZhi()[0] if eight_char.getMonthShiShenZhi() else "",
    "day": eight_char.getDayShiShenZhi()[0] if eight_char.getDayShiShenZhi() else "",
    "hour": eight_char.getTimeShiShenZhi()[0] if eight_char.getTimeShiShenZhi() else "",
}

# 7) 十二长生（星运）
chang_sheng = {
    "year": eight_char.getYearZhi().getChangSheng(eight_char.getDayGan()),
    "month": eight_char.getMonthZhi().getChangSheng(eight_char.getDayGan()),
    "day": eight_char.getDayZhi().getChangSheng(eight_char.getDayGan()),
    "hour": eight_char.getTimeZhi().getChangSheng(eight_char.getDayGan()),
}

# 8) 空亡
xun_kong = eight_char.getXunKong()

# 9) 纳音
from lunar_python import LunarUtil
na_yin = {
    "year": LunarUtil.NAYIN.get(eight_char.getYear(), ""),
    "month": LunarUtil.NAYIN.get(eight_char.getMonth(), ""),
    "day": LunarUtil.NAYIN.get(eight_char.getDay(), ""),
    "hour": LunarUtil.NAYIN.get(eight_char.getTime(), ""),
}

# 10) 神煞
shen_sha = {
    "year": eight_char.getYearShenSha(),
    "month": eight_char.getMonthShenSha(),
    "day": eight_char.getDayShenSha(),
    "hour": eight_char.getTimeShenSha(),
}
```

**返回结构更新**：
```python
return {
    "mingpan": {
        "gender": body.gender,
        "four_pillars": four_pillars,
        "dayun": dayun_list,
        "solar_date": birthday_adjusted,
        # 新增字段
        "cang_gan": cang_gan,
        "shi_shen_gan": shi_shen_gan,
        "shi_shen_zhi": shi_shen_zhi,
        "chang_sheng": chang_sheng,
        "xun_kong": xun_kong,
        "na_yin": na_yin,
        "shen_sha": shen_sha,
    }
}
```

**前端类型更新**：

**文件**: `E:\claude_projects\chat\fate-frontend\app\api\index.ts`

在 `CalcPaipanResp` 接口中添加新增字段（见上述代码）。

**优点**：
- 前端实现简单，直接使用后端返回的数据
- 计算逻辑集中在后端，便于维护

**缺点**：
- 增加后端计算负担
- 网络传输数据量较大
- 后端需要维护复杂的计算逻辑

---

#### 方案B：前端查表计算（推荐）

**核心思路**：后端只返回基础的四柱数据，前端通过查询表计算其他信息。

**后端改动**：无需修改，保持现有接口返回的数据结构。

**前端新增文件**：

1. **地支藏干查询表**

**文件**: `E:\claude_projects\chat\fate-frontend\app\lib\bazi\canggan.ts`（新建）

```typescript
// 地支藏干对照表
export const DIZHI_CANGGAN: Record<string, string[]> = {
  子: ['癸'],
  丑: ['己', '癸', '辛'],
  寅: ['甲', '丙', '戊'],
  卯: ['乙'],
  辰: ['戊', '乙', '癸'],
  巳: ['丙', '庚', '戊'],
  午: ['丁', '己'],
  未: ['己', '丁', '乙'],
  申: ['庚', '壬', '戊'],
  酉: ['辛'],
  戌: ['戊', '辛', '丁'],
  亥: ['壬', '甲'],
};

export function getCangGan(zhi: string): string[] {
  return DIZHI_CANGGAN[zhi] || [];
}
```

2. **天干十神查询表**

**文件**: `E:\claude_projects\chat\fate-frontend\app\lib\bazi\shishen.ts`（新建）

```typescript
// 十神对照表（以日干为基准）
export const SHISHEN_MAP: Record<string, Record<string, string>> = {
  甲: { 甲: '比肩', 乙: '劫财', 丙: '食神', 丁: '伤官', 戊: '偏财', 己: '正财', 庚: '偏官', 辛: '正官', 壬: '偏印', 癸: '正印' },
  乙: { 乙: '比肩', 甲: '劫财', 丁: '食神', 丙: '伤官', 己: '偏财', 戊: '正财', 辛: '偏官', 庚: '正官', 癸: '偏印', 壬: '正印' },
  丙: { 丙: '比肩', 丁: '劫财', 戊: '食神', 己: '伤官', 庚: '偏财', 辛: '正财', 壬: '偏官', 癸: '正官', 甲: '偏印', 乙: '正印' },
  丁: { 丁: '比肩', 丙: '劫财', 己: '食神', 戊: '伤官', 辛: '偏财', 庚: '正财', 癸: '偏官', 壬: '正官', 乙: '偏印', 甲: '正印' },
  戊: { 戊: '比肩', 己: '劫财', 庚: '食神', 辛: '伤官', 壬: '偏财', 癸: '正财', 甲: '偏官', 乙: '正官', 丙: '偏印', 丁: '正印' },
  己: { 己: '比肩', 戊: '劫财', 辛: '食神', 庚: '伤官', 癸: '偏财', 壬: '正财', 乙: '偏官', 甲: '正官', 丁: '偏印', 丙: '正印' },
  庚: { 庚: '比肩', 辛: '劫财', 壬: '食神', 癸: '伤官', 甲: '偏财', 乙: '正财', 丙: '偏官', 丁: '正官', 戊: '偏印', 己: '正印' },
  辛: { 辛: '比肩', 庚: '劫财', 癸: '食神', 壬: '伤官', 乙: '偏财', 甲: '正财', 丁: '偏官', 丙: '正官', 己: '偏印', 戊: '正印' },
  壬: { 壬: '比肩', 癸: '劫财', 甲: '食神', 乙: '伤官', 丙: '偏财', 丁: '正财', 戊: '偏官', 己: '正官', 庚: '偏印', 辛: '正印' },
  癸: { 癸: '比肩', 壬: '劫财', 乙: '食神', 甲: '伤官', 丁: '偏财', 丙: '正财', 己: '偏官', 戊: '正官', 辛: '偏印', 庚: '正印' },
};

export function getShiShen(dayGan: string, targetGan: string): string {
  return SHISHEN_MAP[dayGan]?.[targetGan] || '';
}
```

3. **十二长生查询表**

**文件**: `E:\claude_projects\chat\fate-frontend\app\lib\bazi\changsheng.ts`（新建）

```typescript
// 十二长生对照表（阳干顺行，阴干逆行）
const YANG_GAN_CHANGSHENG: Record<string, Record<string, string>> = {
  甲: { 亥: '长生', 子: '沐浴', 丑: '冠带', 寅: '临官', 卯: '帝旺', 辰: '衰', 巳: '病', 午: '死', 未: '墓', 申: '绝', 酉: '胎', 戌: '养' },
  丙: { 寅: '长生', 卯: '沐浴', 辰: '冠带', 巳: '临官', 午: '帝旺', 未: '衰', 申: '病', 酉: '死', 戌: '墓', 亥: '绝', 子: '胎', 丑: '养' },
  戊: { 寅: '长生', 卯: '沐浴', 辰: '冠带', 巳: '临官', 午: '帝旺', 未: '衰', 申: '病', 酉: '死', 戌: '墓', 亥: '绝', 子: '胎', 丑: '养' },
  庚: { 巳: '长生', 午: '沐浴', 未: '冠带', 申: '临官', 酉: '帝旺', 戌: '衰', 亥: '病', 子: '死', 丑: '墓', 寅: '绝', 卯: '胎', 辰: '养' },
  壬: { 申: '长生', 酉: '沐浴', 戌: '冠带', 亥: '临官', 子: '帝旺', 丑: '衰', 寅: '病', 卯: '死', 辰: '墓', 巳: '绝', 午: '胎', 未: '养' },
};

const YIN_GAN_CHANGSHENG: Record<string, Record<string, string>> = {
  乙: { 午: '长生', 巳: '沐浴', 辰: '冠带', 卯: '临官', 寅: '帝旺', 丑: '衰', 子: '病', 亥: '死', 戌: '墓', 酉: '绝', 申: '胎', 未: '养' },
  丁: { 酉: '长生', 申: '沐浴', 未: '冠带', 午: '临官', 巳: '帝旺', 辰: '衰', 卯: '病', 寅: '死', 丑: '墓', 子: '绝', 亥: '胎', 戌: '养' },
  己: { 酉: '长生', 申: '沐浴', 未: '冠带', 午: '临官', 巳: '帝旺', 辰: '衰', 卯: '病', 寅: '死', 丑: '墓', 子: '绝', 亥: '胎', 戌: '养' },
  辛: { 子: '长生', 亥: '沐浴', 戌: '冠带', 酉: '临官', 申: '帝旺', 未: '衰', 午: '病', 巳: '死', 辰: '墓', 卯: '绝', 寅: '胎', 丑: '养' },
  癸: { 卯: '长生', 寅: '沐浴', 丑: '冠带', 子: '临官', 亥: '帝旺', 戌: '衰', 酉: '病', 申: '死', 未: '墓', 午: '绝', 巳: '胎', 辰: '养' },
};

export function getChangSheng(gan: string, zhi: string): string {
  return YANG_GAN_CHANGSHENG[gan]?.[zhi] || YIN_GAN_CHANGSHENG[gan]?.[zhi] || '';
}
```

4. **纳音查询表**

**文件**: `E:\claude_projects\chat\fate-frontend\app\lib\bazi\nayin.ts`（新建）

```typescript
// 六十甲子纳音表
export const NAYIN_MAP: Record<string, string> = {
  甲子: '海中金', 乙丑: '海中金',
  丙寅: '炉中火', 丁卯: '炉中火',
  戊辰: '大林木', 己巳: '大林木',
  庚午: '路旁土', 辛未: '路旁土',
  壬申: '剑锋金', 癸酉: '剑锋金',
  甲戌: '山头火', 乙亥: '山头火',
  丙子: '涧下水', 丁丑: '涧下水',
  戊寅: '城头土', 己卯: '城头土',
  庚辰: '白蜡金', 辛巳: '白蜡金',
  壬午: '杨柳木', 癸未: '杨柳木',
  甲申: '泉中水', 乙酉: '泉中水',
  丙戌: '屋上土', 丁亥: '屋上土',
  戊子: '霹雳火', 己丑: '霹雳火',
  庚寅: '松柏木', 辛卯: '松柏木',
  壬辰: '长流水', 癸巳: '长流水',
  甲午: '砂中金', 乙未: '砂中金',
  丙申: '山下火', 丁酉: '山下火',
  戊戌: '平地木', 己亥: '平地木',
  庚子: '壁上土', 辛丑: '壁上土',
  壬寅: '金箔金', 癸卯: '金箔金',
  甲辰: '覆灯火', 乙巳: '覆灯火',
  丙午: '天河水', 丁未: '天河水',
  戊申: '大驿土', 己酉: '大驿土',
  庚戌: '钗钏金', 辛亥: '钗钏金',
  壬子: '桑柘木', 癸丑: '桑柘木',
  甲寅: '大溪水', 乙卯: '大溪水',
  丙辰: '沙中土', 丁巳: '沙中土',
  戊午: '天上火', 己未: '天上火',
  庚申: '石榴木', 辛酉: '石榴木',
  壬戌: '大海水', 癸亥: '大海水',
};

export function getNaYin(gan: string, zhi: string): string {
  return NAYIN_MAP[gan + zhi] || '';
}
```

5. **空亡计算**

**文件**: `E:\claude_projects\chat\fate-frontend\app\lib\bazi\xunkong.ts`（新建）

```typescript
// 空亡计算（根据日柱）
const XUNKONG_MAP: Record<string, string> = {
  甲子: '戌亥', 甲戌: '申酉', 甲申: '午未', 甲午: '辰巳', 甲辰: '寅卯', 甲寅: '子丑',
  乙丑: '戌亥', 乙亥: '申酉', 乙酉: '午未', 乙未: '辰巳', 乙巳: '寅卯', 乙卯: '子丑',
  丙寅: '戌亥', 丙子: '申酉', 丙戌: '午未', 丙申: '辰巳', 丙午: '寅卯', 丙辰: '子丑',
  丁卯: '戌亥', 丁丑: '申酉', 丁亥: '午未', 丁酉: '辰巳', 丁未: '寅卯', 丁巳: '子丑',
  戊辰: '戌亥', 戊寅: '申酉', 戊子: '午未', 戊戌: '辰巳', 戊申: '寅卯', 戊午: '子丑',
  己巳: '戌亥', 己卯: '申酉', 己丑: '午未', 己亥: '辰巳', 己酉: '寅卯', 己未: '子丑',
  庚午: '戌亥', 庚辰: '申酉', 庚寅: '午未', 庚子: '辰巳', 庚戌: '寅卯', 庚申: '子丑',
  辛未: '戌亥', 辛巳: '申酉', 辛卯: '午未', 辛丑: '辰巳', 辛亥: '寅卯', 辛酉: '子丑',
  壬申: '戌亥', 壬午: '申酉', 壬辰: '午未', 壬寅: '辰巳', 壬子: '寅卯', 壬戌: '子丑',
  癸酉: '戌亥', 癸未: '申酉', 癸巳: '午未', 癸卯: '辰巳', 癸丑: '寅卯', 癸亥: '子丑',
};

export function getXunKong(dayGan: string, dayZhi: string): string {
  return XUNKONG_MAP[dayGan + dayZhi] || '';
}
```

6. **综合计算工具**

**文件**: `E:\claude_projects\chat\fate-frontend\app\lib\bazi\calculator.ts`（新建）

```typescript
import { getCangGan } from './canggan';
import { getShiShen } from './shishen';
import { getChangSheng } from './changsheng';
import { getNaYin } from './nayin';
import { getXunKong } from './xunkong';
import type { Paipan } from '@/app/lib/chat/types';

export interface DetailedPaipan extends Paipan {
  cang_gan: {
    year: string[];
    month: string[];
    day: string[];
    hour: string[];
  };
  shi_shen_gan: {
    year: string;
    month: string;
    day: string;
    hour: string;
  };
  shi_shen_zhi: {
    year: string;
    month: string;
    day: string;
    hour: string;
  };
  chang_sheng: {
    year: string;
    month: string;
    day: string;
    hour: string;
  };
  xun_kong: string;
  na_yin: {
    year: string;
    month: string;
    day: string;
    hour: string;
  };
}

export function calculateDetailedPaipan(paipan: Paipan): DetailedPaipan {
  const { four_pillars } = paipan;
  const dayGan = four_pillars.day[0];
  const dayZhi = four_pillars.day[1];

  return {
    ...paipan,
    // 藏干
    cang_gan: {
      year: getCangGan(four_pillars.year[1]),
      month: getCangGan(four_pillars.month[1]),
      day: getCangGan(four_pillars.day[1]),
      hour: getCangGan(four_pillars.hour[1]),
    },
    // 十神（天干）
    shi_shen_gan: {
      year: getShiShen(dayGan, four_pillars.year[0]),
      month: getShiShen(dayGan, four_pillars.month[0]),
      day: getShiShen(dayGan, four_pillars.day[0]),
      hour: getShiShen(dayGan, four_pillars.hour[0]),
    },
    // 十神（地支藏干主气）
    shi_shen_zhi: {
      year: getShiShen(dayGan, getCangGan(four_pillars.year[1])[0] || ''),
      month: getShiShen(dayGan, getCangGan(four_pillars.month[1])[0] || ''),
      day: getShiShen(dayGan, getCangGan(four_pillars.day[1])[0] || ''),
      hour: getShiShen(dayGan, getCangGan(four_pillars.hour[1])[0] || ''),
    },
    // 十二长生
    chang_sheng: {
      year: getChangSheng(dayGan, four_pillars.year[1]),
      month: getChangSheng(dayGan, four_pillars.month[1]),
      day: getChangSheng(dayGan, four_pillars.day[1]),
      hour: getChangSheng(dayGan, four_pillars.hour[1]),
    },
    // 空亡
    xun_kong: getXunKong(dayGan, dayZhi),
    // 纳音
    na_yin: {
      year: getNaYin(four_pillars.year[0], four_pillars.year[1]),
      month: getNaYin(four_pillars.month[0], four_pillars.month[1]),
      day: getNaYin(four_pillars.day[0], four_pillars.day[1]),
      hour: getNaYin(four_pillars.hour[0], four_pillars.hour[1]),
    },
  };
}
```

**使用方式**：

在 `DetailedPaipanTable` 组件中：

```typescript
import { calculateDetailedPaipan } from '@/app/lib/bazi/calculator';

export function DetailedPaipanTable({ paipan }: { paipan: Paipan }) {
  const detailedPaipan = calculateDetailedPaipan(paipan);
  
  // 使用 detailedPaipan 中的数据渲染表格
  // ...
}
```

**优点**：
- 后端无需修改，保持简洁
- 减少网络传输数据量
- 前端可以灵活计算和展示
- 查询表是固定的，不会变化

**缺点**：
- 前端代码量增加
- 需要维护多个查询表
- 如果算法有误，需要更新前端代码

---

### 方案对比

| 特性 | 方案A（后端计算） | 方案B（前端查表）|
|------|------------------|------------------|
| 后端改动 | 需要大量修改 | 无需修改 |
| 前端改动 | 较少 | 较多（新增查询表）|
| 网络传输 | 数据量大 | 数据量小 |
| 计算负担 | 后端承担 | 前端承担 |
| 维护成本 | 后端集中维护 | 前端分散维护 |
| 推荐指数 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**推荐使用方案B**，因为：
1. 查询表是固定的，不会变化
2. 减少后端计算负担和网络传输
3. 前端可以更灵活地展示和计算
4. 用户已经提供了关键的查询表

## Critical Files（关键文件）

### 需要修改的文件

1. `fate-frontend/app/components/chat/SimplifiedPaipanCard.tsx`
   - 改造简洁卡片视图

2. `fate-frontend/app/globals.css`
   - 更新五行样式类

3. `fate-frontend/app/panel/page.tsx`
   - 添加视图切换功能

4. `fate/app/routers/bazi.py`
   - 扩展 API 返回更多数据

5. `fate-frontend/app/api/index.ts`
   - 更新类型定义

### 需要创建的文件

6. `fate-frontend/app/components/chat/DetailedPaipanTable.tsx`
   - 新建详细表格视图组件

## Verification（验证方案）

### 视觉验证

1. **简洁卡片视图**
   - [ ] 四个柱子卡片样式符合设计图
   - [ ] 日柱黄色高亮明显
   - [ ] 五行标签颜色准确、样式精致
   - [ ] 大运列表美观，当前大运高亮
   - [ ] 整体配色协调

2. **详细表格视图**
   - [ ] 表格布局清晰，信息完整
   - [ ] 天干地支五行颜色正确
   - [ ] 所有行信息显示准确
   - [ ] 响应式布局正常

3. **视图切换**
   - [ ] 切换按钮位置合理，样式美观
   - [ ] 切换动画流畅
   - [ ] 用户偏好正确保存和恢复

### 功能验证

1. **数据准确性**
   - [ ] 四柱数据显示正确
   - [ ] 五行映射准确
   - [ ] 大运列表完整
   - [ ] 详细表格信息准确

2. **交互验证**
   - [ ] 卡片悬停效果流畅
   - [ ] 大运列表可横向滚动
   - [ ] 视图切换响应迅速
   - [ ] 触摸设备上操作顺畅

3. **响应式验证**
   - [ ] 桌面端（>1024px）：布局宽敞
   - [ ] 平板端（768-1024px）：布局适配
   - [ ] 手机端（<768px）：字体和间距合适
   - [ ] 极小屏幕（<360px）：不崩溃

### 浏览器兼容性

- [ ] Chrome/Edge（Chromium）
- [ ] Firefox
- [ ] Safari（iOS/macOS）
- [ ] 移动浏览器

## Implementation Notes（实现注意事项）

### 样式一致性

- 优先使用 `design-tokens.ts` 中定义的颜色
- 使用 CSS 变量（`var(--color-*)`）而非硬编码颜色
- 保持与现有设计系统的一致性

### 性能优化

- 避免不必要的重渲染
- 使用 `React.memo` 包裹纯展示组件
- 复杂动画使用 CSS 而非 JS

### 可访问性

- 添加适当的 ARIA 标签
- 确保键盘导航可用
- 颜色对比度符合 WCAG 标准

### 代码质量

- 遵循现有的 TypeScript 规范
- 使用 ESLint 检查代码
- 添加必要的注释

## Future Enhancements（未来扩展）

1. **动画效果**
   - 卡片进入动画
   - 视图切换过渡动画
   - 五行标签脉动效果

2. **交互增强**
   - 点击柱子显示详细解释
   - 大运卡片点击展开流年
   - 五行标签悬停显示含义

3. **主题支持**
   - 暗色模式适配
   - 自定义配色方案

4. **导出功能**
   - 导出排盘为图片
   - 分享到社交媒体
