# Bazi 平台 React Native APP 实施方案

## Context

`fateinsight.site` 已有完整的后端(FastAPI)、Web 前端(Next.js)和微信小程序,现需要新增 iOS + Android 双端原生 APP,目标是覆盖 Web 全部功能,通过原生 SDK 实现微信登录/支付,并兼顾 App Store 合规要求。

选择 React Native 是为了在「复用现有 TS 业务逻辑」与「接近原生体验」之间取得平衡:Web 端 `app/lib/` 下的 api、auth、chat/sse、bazi 计算、liuyao、design-tokens 已经是框架无关的,可以直接抽出共享。同时 React Native 能支撑微信原生 SDK、Apple 登录、IAP 等必需的原生模块。

**关键约束:**
- iOS 走合规路线:加 Sign in with Apple + IAP 双支付,Android 继续用微信支付
- 前端只剩 ~5% Next.js 强耦合代码(`next/image`、`next/font`、`generateStaticParams`),其余可复用
- 后端缺口:Apple 登录、IAP 验证、手机+短信、原生微信登录(与小程序 jscode 不同)、推送 token、CORS 放行原生 scheme

---

## 总体路线 & 时间盘

**现实预估 13–15 周**(6 大阶段,部分并行):

| 阶段 | 周次 | 内容 |
|---|---|---|
| A. 基建 | W1–W2 | RN 工程初始化、monorepo 抽 shared 包、导航/主题/存储 |
| B. 后端补齐 | W2–W4(并行) | 手机+短信、Apple 登录、原生微信登录、IAP 验证、推送 token、CORS |
| C. 核心功能(Tier 1) | W3–W6 | 登录/注册/重置、`/panel`、`/paipan`、`/chat`、`/account` |
| D. 次要功能(Tier 2) | W6–W9 | `/liuyao`、`/xinji`、`/history`、`/report`、`/profile/*`、`/pricing` |
| E. 原生集成 | W8–W11(覆盖 C/D) | 微信 OpenSDK、APNs/FCM、闪屏图标、深链 |
| F. 上架准备 | W11–W15 | TestFlight、App Store、Google Play + 国内安卓商店、隐私合规 |

长尾页面(`/about` `/faq` `/terms` `/privacy` `/contact` `/feedback` `/knowledge/[slug]`)v1 用 WebView 嵌入,后续视需求再原生化。
管理后台(`/admin/*`)v1 不做。

---

## 工程结构(Monorepo)

把现有目录改造为 pnpm workspace:

```
chat/
  packages/shared/        新增 - 抽自 fate-frontend/app/lib/
  fate-frontend/          保留 - 改为 import @fate/shared
  fate-app/               新增 - RN CLI bare workflow(非 Expo Managed)
  fate/                   不动
```

`packages/shared/` 直接搬迁的文件(都是框架无关):
- `fate-frontend/app/lib/api.ts` → 网络层
- `fate-frontend/app/lib/chat/sse.ts` → SSE 流式解析
- `fate-frontend/app/lib/chat/types.ts` → 消息类型
- `fate-frontend/app/lib/auth.tsx` → 拆掉 JSX 层,保留 hook 逻辑
- `fate-frontend/app/lib/bazi/*`、`liuyao/*`、`hexagram.ts`、`birthData.ts`、`design-tokens.ts`、`disclaimer.ts`

需要小改造:把 `localStorage` 抽成 `Storage` 接口,Web 注入 localStorage 实现,RN 注入 `react-native-mmkv` 实现。

---

## 阶段 A:RN 工程基建

**关键技术选型:**

| 项 | 选择 | 原因 |
|---|---|---|
| 脚手架 | RN CLI(bare),0.74+,New Architecture | 微信 OpenSDK 必须原生模块,Expo Managed 不行 |
| 导航 | React Navigation v7 | 生态最成熟 |
| 状态 | Zustand | 体量轻、API 接近现有 Context 用法 |
| 存储 | react-native-mmkv | 替代 localStorage,同步 API,10× AsyncStorage |
| 主题 | StyleSheet + theme object | 复用 `design-tokens.ts`,无额外依赖 |
| 流式 | WebSocket 主路径 + react-native-sse 兜底 | `/api/chat/ws/chat` 已就绪,小程序已验证 |
| 图标 | lucide-react-native | Web 用的 lucide-react,API 一致 |
| 图表/SVG | react-native-svg | 复用 `components/charts/`、`WuXing.tsx` 逻辑 |
| Markdown | react-native-markdown-display | 替代 `components/Markdown.tsx` |
| 日期时间 | @react-native-community/datetimepicker | 替代 `Calender.tsx`、`DatePicker.tsx`、`TimePicker.tsx` |

**导航结构:**
- `RootNavigator` = `AuthStack` ∪ `MainTabs` ∪ `ModalStack`
- `MainTabs`: 首页(`/panel`)、AI 对话(`/chat`)、工具(paipan/liuyao/xinji 三合一)、我的(`/account`)
- `ModalStack`: `/report`、`/history`、`/pricing`、`/knowledge/:slug`、`/profile/edit`
- `WebView` 屏:`/about`、`/contact`、`/faq`、`/terms`、`/privacy`、`/feedback`

**RN 项目目录:**
```
fate-app/src/
  api/          (re-export @fate/shared/api)
  components/   (Button, Card, Markdown, ChartSvg, QuotaBar, ...)
  screens/
    auth/       (Login, Register, PhoneCode, AppleSignIn, ForgotPwd, ResetPwd)
    main/       (Panel, Chat, Paipan, Liuyao, Xinji, History, Account)
    modal/      (Report, Pricing, Knowledge, ProfileEdit)
    web/        (Terms, Privacy, Faq, About, Contact, Feedback)
  navigation/
  theme/        (复用 shared tokens,RN 扩展)
  storage/      (mmkv 适配 Storage 接口)
  streaming/    (ws.ts, sse.ts)
  native/       (wechat.ts, apple.ts, iap.ts, push.ts)
  hooks/        (useAuth, useQuota, useStreamingChat)
```

---

## 阶段 B:后端补齐(并行)

**新增/修改的关键文件:**

| 文件 | 修改内容 |
|---|---|
| `fate/app/routers/users.py` | `POST /api/auth/phone/send-code`、`POST /api/auth/phone/verify`、`POST /api/auth/wechat/native-login`(区别于现有 mp jscode)、`POST /api/auth/apple/login` |
| `fate/app/routers/payments.py` | `POST /api/payments/iap/verify`(Apple receipt 验证),与 `webhooks/wechatpay` 平行 |
| `fate/app/routers/push.py` | 新增。`POST /api/push-tokens`(device_id, platform, token) |
| `fate/app/services/sms.py` | 新增。封装阿里云/腾讯云短信。频控:1/min/手机、5/day/IP,Redis 计数 |
| `fate/app/services/wechat_open.py` | 新增。开放平台 access_token + refresh_token,与小程序 jscode 流程独立 |
| `fate/app/services/apple_signin.py` | 新增。验证 identity_token(JWKS 拉取 + 缓存) |
| `fate/app/services/iap_validator.py` | 新增。调用 Apple `/verifyReceipt`,沙盒/生产路由 |
| `fate/app/models/` | 新增 `PhoneCode`、`PushToken`、`IapReceipt` 三张表 |
| `fate/app/main.py`(CORS 配置处) | 加 `capacitor://`、`fate://` 等 scheme;RN fetch 实际不带 Origin,主要是 Universal Links host 校验 |
| `fate/app/config.py` | 加 `ALIYUN_SMS_*`、`WECHAT_OPEN_APPID/SECRET`、`APPLE_TEAM_ID`、`APPLE_KEY_ID`、`APPLE_PRIVATE_KEY`、`IAP_SHARED_SECRET` |

**复用确认:** JWT 签发逻辑、quota 系统、订单/产品模型、SSE/WebSocket 流式不动,所有新登录方式最终都签发同一个 JWT 走同一套鉴权。

---

## 阶段 C/D:Web 功能对齐(按优先级)

**Tier 1 核心(W3–W6):**
- 登录:邮箱/密码、手机+短信、微信(原生 SDK)、Apple(iOS)
- 注册 + 邀请码、忘记密码、重置密码
- `/panel`:首页/仪表盘
- `/paipan`:八字排盘表单 + 结果(SVG 重画 `WuXing.tsx`)
- `/chat`:流式对话 + 重新生成 + 简化 + 快捷问 + 配额提示
- `/account`:个人信息、配额、退出

**Tier 2 次要(W6–W9):**
- `/liuyao`:六爻占卜(摇卦 UI 在触屏上反而比 Web 顺手)
- `/xinji`:心机/情绪
- `/history`:排盘历史(本地缓存 + 服务器同步)
- `/report`:解读报告
- `/profile/*`:档案管理、默认八字
- `/pricing`、`/try`、`/demo`:套餐和试用

**Tier 3 长尾(W8–W9,WebView):**
直接 `WebView` 加载 Web 端对应路径,加 token 注入与回退按钮即可。

---

## 阶段 E:原生集成

- **微信 OpenSDK**(`react-native-wechat-lib`):
  - 必须在 `open.weixin.qq.com` 重新注册「移动应用」(与小程序 AppID 不同)
  - iOS 配 Universal Links + URL Scheme
  - Android 配签名 SHA1/MD5、应用包名
  - Bundle ID / package name 建议 `com.fate.bazi` 早定下来
- **Apple Sign-In**:Xcode capability 勾选 + `@invertase/react-native-apple-authentication`
- **IAP**:`react-native-iap`,前端发起购买 → 后端 receipt 验证 → 加 quota
- **推送**:
  - iOS:APNs 走 `@react-native-firebase/messaging`
  - Android(国际版):FCM
  - Android(国内):个推/极光,v1.1 再补,v1 内置「前台 WebSocket 通知」兜底
- **闪屏/图标**:`react-native-bootsplash`,主色 `#b83227`,底色 `#efe9dd`
- **深链**:`fate://` scheme + Universal Links(`https://app.fateinsight.site/*`)

---

## 阶段 F:上架准备

- **iOS**:Apple Developer 账号、Provisioning、TestFlight 外测(≥10 人 1 周)、隐私 nutrition labels、ICP 备案(国区上架必需)
- **Android**:keystore + Play App Signing
  - 国际:Google Play
  - 国内:应用宝、华为、小米、OPPO、vivo(每家约 1 周审核,先发应用宝 + 华为)
- **合规(China)**:首次启动隐私政策弹窗(MIIT 强制)、SDK 合规清单、个人信息保护清单、AI 算法备案(可能适用)

ICP 备案/算法备案有 4–8 周窗口期,**W1 立即并行启动**。

---

## 仍需确认的次要决策

| 决策 | 默认 | 备选 |
|---|---|---|
| 国内 Android 推送 | v1 内置 WebSocket 前台通知,后台推送 v1.1 接个推 | v1 直接接个推 |
| 长尾页面方式 | WebView | 全部原生重写 |
| Monorepo 工具 | pnpm workspace | Nx / Turborepo |

这几项不阻塞启动,W1–W2 期间再敲定即可。

---

## 风险登记

| 风险 | 等级 | 缓解 |
|---|---|---|
| App Store 4.8(无 Apple 登录) | ✅ 已规避 | 已纳入 Phase B |
| App Store 3.1.1(数字服务必须 IAP) | ✅ 已规避 | iOS 走 IAP,Android 走微信支付 |
| 微信 OpenSDK 签名/Universal Links 配错 | 中 | 物理机测,流程文档化;别在模拟器排查 |
| 国内安卓商店审核分散 | 中 | 应用宝 + 华为先行,其余分批 |
| ICP/算法备案延期 | 中 | W1 即启动,与开发并行 |
| SSE/WS 移动网络抖动 | 中 | 指数退避重连;断点续传从 last `message_id` |
| iOS 后台流式中断 | 低 | 后端兜底完成,推送通知用户回看 |

---

## 验证方案

- **单测**:shared 包共用 Web 端已有 Jest 配置,直接跑
- **组件**:`@testing-library/react-native` 覆盖关键屏幕
- **E2E**:Detox iOS 模拟器 + Android emulator,跑通登录 → 排盘 → 流式对话 → 支付/IAP 沙盒主链路
- **微信登录/支付**:必须真机,微信开放平台沙盒 + 微信支付测试商户号
- **Apple Sign-In + IAP**:TestFlight 包 + Sandbox 测试账号
- **推送**:Firebase 测试控制台触发 FCM/APNs
- **真机矩阵**:iPhone 13/15、Pixel 6、华为(无 GMS)、低端 Redmi
- **上线前**:TestFlight 外测 + Google Play Internal Testing 各跑 1 周

---

## 关键复用清单(避免重写)

抽到 `packages/shared/` 直接复用:
- `fate-frontend/app/lib/api.ts`、`api.d.ts`
- `fate-frontend/app/lib/chat/sse.ts`、`chat/types.ts`
- `fate-frontend/app/lib/auth.tsx`(去 JSX,保留 hooks 逻辑)
- `fate-frontend/app/lib/bazi/*`、`liuyao/*`
- `fate-frontend/app/lib/hexagram.ts`、`birthData.ts`、`design-tokens.ts`、`disclaimer.ts`

后端不动直接调:
- JWT 签发 / 鉴权
- `POST /api/bazi/calc_paipan`
- `POST /api/chat/start`、`/api/chat`、`/api/chat/regenerate`、`/api/chat/simplify`
- `WS /api/chat/ws/chat`
- `GET /api/quota/me`、`/api/me`
- `POST /api/profile/*`、`/api/orders/*`、`/api/products/*`

设计资产(从小程序借):
- 主色 `#b83227`、底色 `#efe9dd`、文字 `#888888`/`#2c2c2c`
- 五行色:木 `#5D8A4A`、火 `#D4534A`、土 `#A67C52`、金 `#B8860B`、水 `#4A7BA7`
- Tab 图标可直接复用 `fate_wechat/miniprogram/assets/tab-*.png`
