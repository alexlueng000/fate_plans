# 海外国际化实施方案（待确认）

## 范围与阶段

统一主Web与后端代码、独立部署配置；不复制项目、不接Stripe、不修改命理算法。本轮先交付审计与方案，按AGENTS.md重大变更前确认的要求，确认后实施。

1. 确认Git基线，在后端和主Web建立 feature/overseas-i18n。推荐以当前stage实现为基线，经确认后采用；另一选项是先把stage合入develop再从develop创建。不要直接从落后的develop开发，也不擅自合并生产分支。Web已有panel修改先做diff记录，冲突时用独立worktree，不stash/reset用户代码。
2. 建立locale解析、地区配置及两套语言资源，先做首页/认证/排盘垂直流程。
3. 覆盖六爻、开场、续聊、报告、历史、用户中心及所有可达展示与错误文案。
4. 加入前后端支付禁用、海外出生支持校验、回归测试，再准备独立海外部署；本任务不部署国内服务器。

## 前端方案

优先next-intl：官方支持App Router、Server/Client Components、cookie决定语言且无需语言路径前缀，适合现有Next15架构。来源：https://next-intl.dev/docs/getting-started/app-router 。具体依赖版本须安装前验证peer dependencies并锁定，当前仅完成架构评估。

保留现有路径、rewrites、UI与API调用语义。新增request配置、Provider及messages/zh-CN.json和zh-TW.json；zh-HK/en仅注册预留，不显示为可用语言。语言优先级：有效用户偏好 > 部署默认；国内默认zh-CN，海外默认zh-TW。服务端渲染与客户端一致，缓存不得跨语言复用。

Provider不能以locale为key重建整个页面。切换时更新词典/cookie并保留表单组件实例；需服务端刷新时先验证草稿恢复、当前路由/query和会话ID不丢失。复用已有profileDraft逻辑，不覆盖用户输入。Metadata、html lang、canonical、OG、sitemap与真实部署域名同步；仅为实际可访问的语言URL生成hreflang。

台湾措辞人工校对：登录→登入、注册→註冊、验证码→驗證碼、账号→帳號、信息→資訊、历史记录→歷史紀錄、加载中→載入中。品牌核心表达保持语义，术语建立词汇表。使用ICU参数，不拼接句子；日期/数字按locale格式化，但出生时区不能取浏览器语言或自动推断。

## 后端方案

统一白名单locale解析：显式请求locale > Accept-Language（处理q权重及别名）> zh-CN。现有客户端缺省行为、JSON key、枚举与HTTP状态不变；未知语言回落zh-CN，zh-HK/en未启用时不能声称已支持。

在响应展示层映射术语与错误；不对整个JSON或内部对象做OpenCC。请求校验错误、鉴权、额度不足、SSE错误也需本地化。原始用户内容与历史原文保留。

沿用DB基础System Prompt，组合可信的locale输出约束，同时覆盖User Prompt中的开场/报告模板；八字与六爻每轮生成都明确台湾繁体语言要求。会话store持久化locale并向后兼容旧会话；语言变化重建语言约束，不能沿用旧pinned简体指令。开场/报告缓存与幂等请求需区分输出语言，同时不重复扣费。OpenCC仅可作为自然语言输出的辅助，先验证流式分块、术语及引用，不更改RAG检索。

## 地区与权限

服务器地区配置为权限事实来源；客户端只接收安全公共配置。包含region/defaultLocale/currency/siteUrl/apiBase/loginMethods/paymentChannels/features。海外paymentChannels为空且paymentsEnabled=false，前端隐藏所有购买入口、服务端阻止创建国内支付；不能凭locale或可伪造header决定支付权限。现有国内订单回调的验签与幂等保持不变，海外不持有国内商户凭据。

海外先启用已有邮箱能力，短信/微信默认关闭；是否对海外开放已有邮箱注册受邀请机制约束，不能删除原授权规则。付费关闭不等于免费无限使用，额度不足仍拒绝服务。

## 受影响文件清单（计划，非已修改）

| 绝对路径 | 改动 |
|---|---|
| E:/claude_projects/chat/fate-frontend/package.json及锁文件 | next-intl依赖 |
| E:/claude_projects/chat/fate-frontend/next.config.ts | 包裹intl插件，保留代理 |
| E:/claude_projects/chat/fate-frontend/i18n/、messages/ | 新建配置和语言资源 |
| E:/claude_projects/chat/fate-frontend/app/layout.tsx、ClientLayout.tsx | Provider、lang、metadata |
| E:/claude_projects/chat/fate-frontend/app 下各page.tsx、layout.tsx | 首页、八字、六爻、chat、panel、认证、历史、账户、报告等全部用户可达文案 |
| E:/claude_projects/chat/fate-frontend/app/components/ | 导航、表单、日期时间、支付/额度弹窗、landing、分享及错误展示 |
| E:/claude_projects/chat/fate-frontend/app/lib/api.ts、auth.tsx、birthData.ts、chat/ | 请求语言透传、错误与状态保持 |
| E:/claude_projects/chat/fate-frontend/app/lib/bazi/、hexagram.ts | 仅展示标签；计算标识不变 |
| E:/claude_projects/chat/fate-frontend/app/sitemap.ts、robots.ts | 部署域名和SEO |
| E:/claude_projects/chat/fate/app/i18n/ | 新建locale解析、词典、输出约束 |
| E:/claude_projects/chat/fate/app/config.py | 地区配置及启动校验 |
| E:/claude_projects/chat/fate/app/routers/ | bazi/liuyao/chat/游客/用户/支付/配置入口的语言及地区限制 |
| E:/claude_projects/chat/fate/app/schemas/ | 向后兼容可选locale |
| E:/claude_projects/chat/fate/app/chat/service.py、utils.py、store.py | prompt、会话语言、历史恢复 |
| E:/claude_projects/chat/fate/app/liuyao/prompts.py、chat_service.py | 开场与续聊语言 |
| E:/claude_projects/chat/fate/app/services/bazi_opening_request.py、liuyao_opening_request.py | 检查语言缓存及扣费幂等 |
| E:/claude_projects/chat/fate/app/services/payments.py | 服务端地区策略 |
| E:/claude_projects/chat/fate/app/test/ | API默认兼容、计算一致性、语言与支付隔离测试 |

fate_personal、fate_wechat、fate-mobile-expo本期不改。bazi_engine和RAG保持计算/检索逻辑不变。实施时进一步列出实际逐文件diff。

## 验收矩阵

1. 国内原URL、默认简体、认证及额度流程回归，比较改前基线。
2. 小程序原请求不带locale回放，核对状态、key、枚举、登录与SSE事件。
3. zh-TW完整走输入→排盘→开场；仅用已验证出生时区。
4. 六爻固定起卦参数→排盘→解读，游客/登录两条路径。
5. 至少三轮繁体对话、断流重试、历史恢复及混合简体提问，人工检查台湾措辞。
6. 未提交八字/六爻/认证表单切换语言，值、草稿、路由参数、会话保持。
7. 同一代码分别使用国内/海外配置启动，核对页面、API、域名、cookie和缓存。
8. 海外隐藏入口及直接调用支付API均阻止；mock国内支付服务断言调用次数为零；额度不足不能绕过。
9. 固定生日、时区、经度及起卦随机种子，跨locale比较所有核心字段与数值；RAG检索输入与结果保持一致。
10. Web执行build、独立tsc和lint，后端相关回归通过；记录命令、退出码、环境及失败基线。

时间专项样例：台北/香港/上海历史规则、纽约DST缺失与重复时间、伦敦DST、加德满都45分钟偏移、南半球DST；节气前后一分钟、23:00/00:00、闰日、农历闰月、经度导致跨日。预期值取独立确认的历算样例，不能用被测代码自证。不支持的城市/无效IANA/缺经度应明确拒绝或提示，不能错误回退。

## 后续英文

复用相同key、ICU和地区配置；另建命理英文术语表及人工审校Prompt，验证长字符串布局和RAG输出理解。启用前完成en资源全覆盖，不使用空词典冒充支持；不因语言扩展重建检索索引或改算法。
