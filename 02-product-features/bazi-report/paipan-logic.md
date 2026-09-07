# 排盘逻辑文档

## 概述

排盘（Paipan）是八字命理系统的核心功能，根据用户的出生信息（日期、时间、地点）计算出八字命盘（四柱八字）和大运信息。本文档详细说明了系统的排盘计算流程。

---

## 整体流程

```
用户输入出生信息
    ↓
前端表单验证
    ↓
调用 /api/bazi/calc_paipan
    ↓
后端处理流程：
  1. 地名解析（获取经纬度）
  2. 真太阳时计算（可选）
  3. 公历/农历转换
  4. 四柱八字计算
  5. 大运计算
    ↓
返回命盘数据
    ↓
前端展示 + AI 解读
```

---

## 前端输入

### 用户输入字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `gender` | string | 性别："男" 或 "女" | "男" |
| `calendar` | string | 历法类型："gregorian"（公历）或 "lunar"（农历） | "gregorian" |
| `birth_date` | string | 出生日期（YYYY-MM-DD） | "1990-05-20" |
| `birth_time` | string | 出生时间（HH:MM，24小时制） | "14:30" |
| `birthplace` | string | 出生地点（城市名称） | "广东阳春" |
| `use_true_solar` | boolean | 是否启用真太阳时（默认 true） | true |

### 前端调用示例

```typescript
const body = {
  gender: "男",
  calendar: "gregorian",
  birth_date: "1990-05-20",
  birth_time: "14:30",
  birthplace: "广东阳春",
  birthplace_provided: true,
  use_true_solar: true
};

const response = await fetch(api('/bazi/calc_paipan'), {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
});

const data = await response.json();
const paipan = data.mingpan;
```

---

## 后端处理流程

### 1. 地名解析（Geocoding）

**文件位置**: `fate/app/utils/geo_amap.py`

**功能**: 将城市名称转换为经纬度坐标

**流程**:
1. 检查缓存：如果城市已解析过，直接返回缓存结果
2. 调用高德地图 API：`https://restapi.amap.com/v3/geocode/geo`
3. 坐标系转换：将高德返回的 GCJ-02 坐标转换为 WGS-84 坐标
4. 缓存结果：避免重复调用外部 API

**坐标系说明**:
- **GCJ-02**（火星坐标系）：中国国家测绘局制定的加密坐标系，高德地图使用
- **WGS-84**（地球坐标系）：国际标准坐标系，用于真太阳时计算

**转换公式**:
```python
def _gcj02_to_wgs84(gcj_lat, gcj_lng):
    # 使用迭代算法进行近似反算
    # 详见 geo_amap.py 中的实现
    return wgs_lat, wgs_lng
```

**示例**:
```python
geocode_city("广东阳春")
# 返回: {"city": "广东阳春", "lat": 22.17, "lng": 111.79}
```

---

### 2. 真太阳时计算

**文件位置**: `fate/app/routers/bazi.py` - `calc_true_solar()`

**原理**: 由于地球自转和经度差异，不同地点的太阳时不同。真太阳时是根据太阳实际位置计算的当地时间。

**计算公式**:
```
真太阳时 = 北京时间 + (当地经度 - 120°) × 4分钟
```

**说明**:
- 中国统一使用东八区时间（北京时间），标准子午线为 **120°E**
- 每相差 **1度经度** = **4分钟** 时差
- 东经大于 120° → 真太阳时比北京时间早
- 东经小于 120° → 真太阳时比北京时间晚

**示例**:
```python
# 广东阳春：经度 111.79°E
# 北京时间：1990-05-20 14:30:00
# 经度差：111.79 - 120 = -8.21°
# 时差：-8.21 × 4 = -32.84 分钟
# 真太阳时：14:30:00 - 32.84分钟 = 13:57:10
```

**代码实现**:
```python
def calc_true_solar(body: SolarIn):
    dt = datetime.strptime(body.birth_date, "%Y-%m-%d %H:%M:%S")
    ref_longitude = 120.0  # 中国标准子午线
    delta_minutes = (body.longitude - ref_longitude) * 4
    dt_true = dt + timedelta(minutes=delta_minutes)
    return {"true_solar_time": dt_true.strftime("%Y-%m-%d %H:%M:%S")}
```

---

### 3. 公历/农历转换

**依赖库**: `lunar-python`

**流程**:

#### 公历输入（gregorian）
```python
# 1. 创建 Solar 对象（公历）
solar = Solar.fromYmdHms(year, month, day, hour, minute, second)

# 2. 转换为 Lunar 对象（农历）
lunar = solar.getLunar()
```

#### 农历输入（lunar）
```python
# 直接创建 Lunar 对象
lunar = Lunar.fromYmdHms(year, month, day, hour, minute, second)
```

**注意事项**:
- 农历输入时，日期已经是农历，无需转换
- 公历输入时，需要先转换为农历，再进行八字计算

---

### 4. 四柱八字计算

**关键概念**:
- **四柱**：年柱、月柱、日柱、时柱
- **八字**：每柱由天干和地支组成，共 8 个字
- **年界**：以立春为界（不是正月初一）
- **月界**：以节气为界（不是农历月初一）

**重要区别**:

| 类型 | 年界 | 月界 | 用途 |
|------|------|------|------|
| 农历干支 | 正月初一 | 农历月初一 | 日历标注 |
| 八字干支 | 立春 | 节气 | 命理排盘 |

**代码实现**:
```python
# 必须使用 EightChar 类，而不是 Lunar 类
eight_char = lunar.getEightChar()

# 获取四柱干支
four_pillars = {
    "year":  _split_ganzhi_to_list(eight_char.getYear()),   # 年柱
    "month": _split_ganzhi_to_list(eight_char.getMonth()),  # 月柱
    "day":   _split_ganzhi_to_list(eight_char.getDay()),    # 日柱
    "hour":  _split_ganzhi_to_list(eight_char.getTime())    # 时柱
}
```

**干支拆分**:
```python
def _split_ganzhi_to_list(gz: str) -> List[str]:
    """
    将干支字符串拆分为 [天干, 地支]
    例如: "癸酉" -> ["癸", "酉"]
    """
    s = str(gz).strip().replace(" ", "")
    return [s[0], s[1]] if len(s) == 2 else []
```

**示例输出**:
```json
{
  "year": ["庚", "午"],
  "month": ["辛", "巳"],
  "day": ["癸", "酉"],
  "hour": ["己", "未"]
}
```

---

### 5. 大运计算

**概念**: 大运是命理学中的重要概念，表示人生不同阶段的运势周期，每步大运持续 10 年。

**计算依据**:
- **性别**: 男命和女命的大运顺序不同
- **年柱阴阳**: 根据出生年的天干阴阳决定顺逆

**代码实现**:
```python
# 性别编码：男=1，女=0
gender_code = 1 if body.gender == "男" else 0

# 创建大运对象
yun = Yun(eight_char, gender_code)

# 获取大运列表
dayun_list = []
for du in yun.getDaYun():
    pillar_list = _split_ganzhi_to_list(du.getGanZhi())
    dayun_list.append({
        "age": du.getStartAge(),        # 起运年龄
        "start_year": du.getStartYear(), # 起运年份
        "pillar": pillar_list            # 大运干支
    })
```

**示例输出**:
```json
[
  {"age": 3, "start_year": 1993, "pillar": ["壬", "午"]},
  {"age": 13, "start_year": 2003, "pillar": ["癸", "未"]},
  {"age": 23, "start_year": 2013, "pillar": ["甲", "申"]},
  {"age": 33, "start_year": 2023, "pillar": ["乙", "酉"]},
  ...
]
```

---

## 返回数据结构

### 完整响应格式

```json
{
  "mingpan": {
    "gender": "男",
    "four_pillars": {
      "year": ["庚", "午"],
      "month": ["辛", "巳"],
      "day": ["癸", "酉"],
      "hour": ["己", "未"]
    },
    "dayun": [
      {
        "age": 3,
        "start_year": 1993,
        "pillar": ["壬", "午"]
      },
      {
        "age": 13,
        "start_year": 2003,
        "pillar": ["癸", "未"]
      }
    ]
  }
}
```

### 字段说明

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `mingpan.gender` | string | 性别 |
| `mingpan.four_pillars.year` | [string, string] | 年柱 [天干, 地支] |
| `mingpan.four_pillars.month` | [string, string] | 月柱 [天干, 地支] |
| `mingpan.four_pillars.day` | [string, string] | 日柱 [天干, 地支] |
| `mingpan.four_pillars.hour` | [string, string] | 时柱 [天干, 地支] |
| `mingpan.dayun` | array | 大运列表 |
| `mingpan.dayun[].age` | number | 起运年龄 |
| `mingpan.dayun[].start_year` | number | 起运年份 |
| `mingpan.dayun[].pillar` | [string, string] | 大运干支 [天干, 地支] |

---

## 错误处理

### 常见错误场景

1. **地名解析失败**
   - 原因：城市名称不存在或高德 API 异常
   - 处理：回退到本地时间（不使用真太阳时）

2. **日期格式错误**
   - 原因：前端传入的日期格式不符合要求
   - 返回：`{"error": "ValueError: ..."}`

3. **农历日期无效**
   - 原因：输入的农历日期不存在（如闰月错误）
   - 返回：`{"error": "..."}`

### 错误响应格式

```json
{
  "error": "ValueError: time data '2024-13-01' does not match format '%Y-%m-%d'"
}
```

---

## 前端展示

### 命盘展示组件

**文件位置**: `fate-frontend/app/lib/paipan.ts`

**功能**:
- 展示四柱八字（年月日时）
- 展示大运列表
- 五行颜色标注
- 十神标注（可选）

### AI 解读流程

1. 前端获取命盘数据后，调用 `/api/chat/start`
2. 后端将命盘数据注入到系统提示词中
3. AI 基于命盘进行解读，通过 SSE 流式返回
4. 前端实时显示 AI 解读内容

---

## 技术栈

### 后端依赖

| 库 | 版本 | 用途 |
|----|------|------|
| `lunar-python` | - | 农历转换、八字计算 |
| `requests` | - | 调用高德地图 API |
| `FastAPI` | 0.110.0 | Web 框架 |

### 前端依赖

| 库 | 版本 | 用途 |
|----|------|------|
| `Next.js` | 15.5.0 | React 框架 |
| `TypeScript` | 5 | 类型系统 |

---

## 性能优化

### 1. 地名缓存

```python
_geo_cache_city: dict[str, tuple[float, float]] = {}
```

- 内存缓存已解析的城市经纬度
- 避免重复调用高德 API
- 缓存生命周期：应用运行期间

### 2. API 重试机制

```python
def geocode_city(city: str, retries: int = 2, timeout: float = 5.0):
    for i in range(retries + 1):
        try:
            # 调用高德 API
        except requests.RequestException:
            if i == retries:
                return {"error": "网络异常"}
            time.sleep(1.5 * (i + 1))  # 指数退避
```

---

## 配置项

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AMAP_KEY` | 高德地图 API Key | 硬编码在代码中 |

### 常量配置

| 常量 | 值 | 说明 |
|------|-----|------|
| `ref_longitude` | 120.0 | 中国标准子午线（东经120°） |
| `AMAP_GEOCODE_URL` | `https://restapi.amap.com/v3/geocode/geo` | 高德地图地理编码 API |

---

## 测试用例

### 测试数据

```json
{
  "gender": "男",
  "calendar": "gregorian",
  "birth_date": "1990-05-20",
  "birth_time": "14:30",
  "birthplace": "广东阳春",
  "use_true_solar": true
}
```

### 预期结果

- 四柱八字：庚午年、辛巳月、癸酉日、己未时
- 大运起运年龄：3 岁
- 真太阳时修正：约 -33 分钟

---

## 未来优化方向

1. **离线地名库**：减少对外部 API 的依赖
2. **数据库缓存**：持久化地名解析结果
3. **批量排盘**：支持一次性计算多个命盘
4. **更精确的真太阳时**：考虑均时差（Equation of Time）
5. **支持更多历法**：藏历、回历等

---

## 参考资料

- [lunar-python 文档](https://github.com/6tail/lunar-python)
- [高德地图 API 文档](https://lbs.amap.com/api/webservice/guide/api/georegeo)
- [真太阳时计算原理](https://zh.wikipedia.org/wiki/%E7%9C%9F%E5%A4%AA%E9%98%B3%E6%97%B6)
- [GCJ-02 坐标系转换](https://github.com/wandergis/coordtransform)

---

**文档版本**: 1.0
**最后更新**: 2026-03-03
**维护者**: 开发团队
