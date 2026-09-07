# 手机号注册登录功能实施计划

## Context

当前系统已支持邮箱+密码登录和微信小程序登录，但缺少手机号登录方式。手机号登录是国内用户最常用的认证方式，可以降低注册门槛，提升用户转化率。

**用户需求**：实现手机号验证码登录/注册功能

**技术选型**（已确认）：
- 短信服务商：腾讯云短信
- 认证模式：纯验证码登录（无需密码）
- 验证码有效期：5分钟
- 实施范围：MVP核心功能（登录/注册，不含账号绑定）

**现有基础设施**：
- User 模型已有 `phone` 字段（唯一约束）
- 已有 `get_by_phone()` 服务函数
- 已有完整的邮箱验证码系统（`password_reset_codes` 表 + `password_reset.py` 服务）可作为模板
- JWT 认证和 Argon2id 密码哈希已配置
- **Redis 已集成**（`redis>=5.0.0`，用于会话存储）

---

## Implementation Plan

### 1. Redis 验证码存储方案

**优势**：
- 性能更好（内存操作 vs 数据库查询）
- 自动过期（利用 Redis TTL，无需定时清理）
- 原子操作（INCR 实现失败次数计数）
- 简化实现（无需数据库表和迁移）

**Redis Key 设计**：

```
# 验证码存储（5分钟 TTL）
phone:code:{phone}:{purpose} = {code}

# 失败次数计数（5分钟 TTL）
phone:attempts:{phone}:{purpose} = {count}

# 频率限制（60秒 TTL）
phone:ratelimit:{phone} = {timestamp}

# IP 频率限制（60秒 TTL）
phone:ratelimit:ip:{ip} = {count}

# 每日发送次数（24小时 TTL）
phone:daily:{phone}:{date} = {count}
```

**数据结构示例**：
```
phone:code:13800138000:login = "123456"  (TTL: 300秒)
phone:attempts:13800138000:login = "2"   (TTL: 300秒)
phone:ratelimit:13800138000 = "1737360000"  (TTL: 60秒)
phone:ratelimit:ip:192.168.1.1 = "2"  (TTL: 60秒)
phone:daily:13800138000:20260520 = "3"  (TTL: 86400秒)
```

**无需数据库表**：使用 Redis 完全替代 `phone_verification_codes` 表，简化实现

---

### 2. 后端服务层

#### 2.1 腾讯云短信服务

**文件**：`fate/app/services/sms.py`

实现异步短信发送服务：

```python
class TencentSMSService:
    """腾讯云短信服务"""
    
    async def send_verification_code(
        self, 
        phone: str, 
        code: str
    ) -> Tuple[bool, str]:
        """
        发送验证码短信
        
        Returns:
            (success, message/error)
        """
```

**依赖**：
- SDK: `tencentcloud-sdk-python` (sms 模块)
- 配置: `TENCENT_SMS_SECRET_ID`, `TENCENT_SMS_SECRET_KEY`, `TENCENT_SMS_APP_ID`, `TENCENT_SMS_SIGN`, `TENCENT_SMS_TEMPLATE_ID`

**短信模板示例**：
```
【易凡文化】您的验证码是：{1}，{2}分钟内有效。如非本人操作，请忽略此短信。
```

#### 2.2 Redis 客户端封装

**文件**：`fate/app/core/redis_client.py`（或复用 `app/chat/store.py` 中的 `_get_redis()`）

```python
from redis import Redis
import os

def get_redis() -> Redis:
    """获取 Redis 客户端（单例模式）"""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=True)
```

#### 2.3 手机验证码服务（基于 Redis）

**文件**：`fate/app/services/phone_verification.py`

使用 Redis 替代数据库存储，核心函数：

**核心函数**：

```python
def generate_code() -> str:
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

def can_send_code(redis: Redis, phone: str, ip_address: str) -> Tuple[bool, Optional[str]]:
    """
    检查是否可以发送验证码
    
    检查项：
    1. 手机号频率限制（60秒内只能发送1次）
    2. IP 频率限制（60秒内最多3次）
    3. 每日限制（单手机号每天最多10次）
    
    Returns:
        (can_send, error_message)
    """
    # 1. 检查手机号频率限制
    rate_key = f"phone:ratelimit:{phone}"
    if redis.exists(rate_key):
        ttl = redis.ttl(rate_key)
        return False, f"请求过于频繁，请 {ttl} 秒后重试"
    
    # 2. 检查 IP 频率限制
    ip_key = f"phone:ratelimit:ip:{ip_address}"
    ip_count = redis.get(ip_key)
    if ip_count and int(ip_count) >= 3:
        return False, "该 IP 请求过于频繁，请稍后重试"
    
    # 3. 检查每日限制
    today = datetime.now().strftime("%Y%m%d")
    daily_key = f"phone:daily:{phone}:{today}"
    daily_count = redis.get(daily_key)
    if daily_count and int(daily_count) >= 10:
        return False, "今日请求次数已达上限（10次），请明天再试"
    
    return True, None

def save_verification_code(
    redis: Redis,
    phone: str,
    code: str,
    ip_address: str,
    purpose: str = "login",
    expire_seconds: int = 300
) -> None:
    """
    保存验证码到 Redis
    
    同时更新频率限制计数器
    """
    # 保存验证码（5分钟过期）
    code_key = f"phone:code:{phone}:{purpose}"
    redis.setex(code_key, expire_seconds, code)
    
    # 初始化失败次数为0
    attempts_key = f"phone:attempts:{phone}:{purpose}"
    redis.setex(attempts_key, expire_seconds, 0)
    
    # 设置手机号频率限制（60秒）
    rate_key = f"phone:ratelimit:{phone}"
    redis.setex(rate_key, 60, int(time.time()))
    
    # 增加 IP 计数（60秒）
    ip_key = f"phone:ratelimit:ip:{ip_address}"
    redis.incr(ip_key)
    redis.expire(ip_key, 60)
    
    # 增加每日计数（24小时）
    today = datetime.now().strftime("%Y%m%d")
    daily_key = f"phone:daily:{phone}:{today}"
    redis.incr(daily_key)
    redis.expire(daily_key, 86400)

def verify_code(
    redis: Redis,
    phone: str,
    code: str,
    purpose: str = "login"
) -> Tuple[bool, str]:
    """
    验证验证码
    
    Returns:
        (success, message)
    """
    code_key = f"phone:code:{phone}:{purpose}"
    attempts_key = f"phone:attempts:{phone}:{purpose}"
    
    # 检查验证码是否存在
    stored_code = redis.get(code_key)
    if not stored_code:
        return False, "验证码已过期或不存在，请重新获取"
    
    # 检查失败次数
    attempts = int(redis.get(attempts_key) or 0)
    if attempts >= 5:
        # 删除验证码，防止继续尝试
        redis.delete(code_key)
        redis.delete(attempts_key)
        return False, "验证码已失效，请重新获取"
    
    # 验证验证码
    if stored_code != code:
        # 增加失败次数
        redis.incr(attempts_key)
        remaining = 5 - (attempts + 1)
        if remaining > 0:
            return False, f"验证码错误，还剩 {remaining} 次尝试机会"
        else:
            redis.delete(code_key)
            redis.delete(attempts_key)
            return False, "验证码已失效，请重新获取"
    
    # 验证成功，删除验证码（防止重复使用）
    redis.delete(code_key)
    redis.delete(attempts_key)
    return True, "验证成功"
```

**安全策略**：
- 验证码有效期：5分钟（300秒 TTL）
- 失败次数限制：5次（Redis INCR 计数）
- 手机号频率限制：60秒（Redis TTL）
- IP 频率限制：60秒内最多3次
- 每日限制：10次/天（24小时 TTL）

#### 2.4 用户服务扩展

**文件**：`fate/app/services/users.py`

添加新函数：

```python
def get_or_create_by_phone(
    db: Session,
    phone: str,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> User:
    """
    根据手机号获取或创建用户（幂等操作）
    
    类似 get_or_create_by_openid 的实现模式
    """
```

**逻辑**：
- 如果手机号已存在 → 返回现有用户
- 如果不存在 → 创建新用户（`source='phone'`）

---

### 3. 后端 API 层

#### 3.1 Redis 配置

**文件**：`fate/app/config.py`

确认 Redis 配置已存在：

```python
# Redis
redis_url: str = "redis://localhost:6379/0"
```

**文件**：`fate/.env.example`

```bash
# Redis
REDIS_URL=redis://localhost:6379/0
```

#### 3.2 配置管理

**文件**：`fate/app/config.py`

添加腾讯云短信配置：

```python
# SMS Service (Tencent Cloud)
sms_provider: str = "tencent"
tencent_sms_secret_id: Optional[str] = None
tencent_sms_secret_key: Optional[str] = None
tencent_sms_app_id: Optional[str] = None
tencent_sms_sign: str = "易凡文化"
tencent_sms_template_id: Optional[str] = None

# SMS Rate Limiting
sms_rate_limit_seconds: int = 60
sms_daily_limit: int = 10
sms_code_expire_minutes: int = 5
```

**文件**：`fate/.env.example`

添加环境变量示例：

```bash
# Tencent Cloud SMS
TENCENT_SMS_SECRET_ID=your_secret_id
TENCENT_SMS_SECRET_KEY=your_secret_key
TENCENT_SMS_APP_ID=your_app_id
TENCENT_SMS_SIGN=易凡文化
TENCENT_SMS_TEMPLATE_ID=your_template_id
```

#### 3.3 API 端点

**文件**：`fate/app/routers/users.py`

添加两个新端点：

**端点1：发送验证码**

```python
@router.post("/auth/phone/send-code")
async def send_phone_verification_code(
    payload: PhoneSendCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    发送手机验证码
    
    Request:
        {
          "phone": "13800138000",
          "purpose": "login"  # 可选，默认 login
        }
    
    Response 200:
        {
          "success": true,
          "message": "验证码已发送",
          "expires_in": 300,
          "rate_limit_reset": 60
        }
    
    Response 429:
        {"detail": "请求过于频繁，请 45 秒后重试"}
    """
```

**实现逻辑**：
1. 验证手机号格式（国内11位，1开头）
2. 获取 Redis 客户端
3. 检查频率限制（`can_send_code(redis, phone, ip)`）
4. 生成验证码（`generate_code()`）
5. 保存到 Redis（`save_verification_code(redis, phone, code, ip)`）
6. 发送短信（`TencentSMSService.send_verification_code(phone, code)`）
7. 返回成功响应

**端点2：验证码登录/注册**

```python
@router.post("/auth/phone/login")
async def login_with_phone(
    payload: PhoneLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    手机号验证码登录/注册
    
    Request:
        {
          "phone": "13800138000",
          "code": "123456",
          "nickname": "用户昵称",  # 可选，仅首次注册时使用
          "avatar_url": "https://..."  # 可选
        }
    
    Response 200:
        {
          "access_token": "eyJ...",
          "token_type": "bearer",
          "user": {
            "id": 123,
            "phone": "13800138000",
            "nickname": "用户昵称",
            "email": null,
            "is_admin": false,
            "source": "phone"
          },
          "is_new_user": true
        }
    """
```

**实现逻辑**：
1. 获取 Redis 客户端
2. 验证验证码（`verify_code(redis, phone, code)`）
3. 如果验证成功 → 查询或创建用户（`get_or_create_by_phone(db, phone, nickname)`）
4. 更新最后登录时间和IP（`touch_last_login(db, user, ip)`）
5. 生成 JWT token（`create_access_token(user.id)`）
6. 返回 token 和用户信息

#### 3.4 Pydantic Schemas

**文件**：`fate/app/schemas/auth.py`（或新建 `phone_auth.py`）

```python
class PhoneSendCodeRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    purpose: str = Field(default="login", pattern="^(login|bind|verify)$")

class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    code: str = Field(..., min_length=6, max_length=6)
    nickname: Optional[str] = Field(None, max_length=64)
    avatar_url: Optional[str] = Field(None, max_length=256)
```

---

### 4. 前端实现

#### 4.1 手机号登录页面

**文件**：`fate-frontend/app/(auth)/login/LoginClient.tsx`

修改现有登录页面，添加 Tab 切换：

```tsx
<Tabs defaultValue="email">
  <TabsList>
    <TabsTrigger value="email">邮箱登录</TabsTrigger>
    <TabsTrigger value="phone">手机登录</TabsTrigger>
  </TabsList>
  
  <TabsContent value="email">
    {/* 现有邮箱登录表单 */}
  </TabsContent>
  
  <TabsContent value="phone">
    <PhoneLoginForm />
  </TabsContent>
</Tabs>
```

#### 4.2 手机登录表单组件

**文件**：`fate-frontend/app/components/PhoneLoginForm.tsx`

实现手机号登录表单：

**UI 元素**：
- 手机号输入框（11位数字，自动格式化）
- 验证码输入框（6位数字）
- "获取验证码"按钮（带60秒倒计时）
- "登录"按钮

**交互逻辑**：
1. 用户输入手机号 → 启用"获取验证码"按钮
2. 点击"获取验证码" → 调用 `/api/auth/phone/send-code`
3. 发送成功 → 按钮禁用，显示倒计时（60秒）
4. 用户输入验证码 → 启用"登录"按钮
5. 点击"登录" → 调用 `/api/auth/phone/login`
6. 登录成功 → 保存 token，跳转到 `/panel` 或 `/profile/create`

#### 4.3 API 客户端

**文件**：`fate-frontend/app/lib/auth.tsx`

添加新函数：

```typescript
export async function sendPhoneCode(phone: string): Promise<void> {
  const resp = await fetch(api('/auth/phone/send-code'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, purpose: 'login' }),
  });
  if (!resp.ok) throw new Error(await resp.text());
}

export async function loginPhone(payload: {
  phone: string;
  code: string;
  nickname?: string;
}): Promise<LoginResponse> {
  const resp = await fetch(api('/auth/phone/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}
```

#### 4.4 工具函数

**文件**：`fate-frontend/app/lib/phone.ts`

```typescript
/**
 * 验证中国大陆手机号（11位，1开头）
 */
export function validateChinaPhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone);
}

/**
 * 格式化手机号显示（138 0013 8000）
 */
export function formatPhone(phone: string): string {
  return phone.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3');
}
```

---

### 5. 依赖管理

#### 5.1 后端依赖

**文件**：`fate/requirements.txt`

添加：

```
# Tencent Cloud SMS SDK
tencentcloud-sdk-python>=3.0.1000
```

**已有依赖**（无需添加）：
- `redis>=5.0.0` ✅

安装命令：
```bash
pip install tencentcloud-sdk-python
```

#### 5.2 前端依赖

无需新增依赖，使用现有的 React 19 + Tailwind CSS。

---

### 6. Redis 部署

**开发环境**：

```bash
# 使用 Docker 运行 Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# 验证连接
redis-cli ping
# 预期输出: PONG
```

**生产环境**：
- 使用云服务商的 Redis（阿里云、腾讯云）
- 配置 `REDIS_URL` 环境变量

**无需数据库迁移**：使用 Redis 存储验证码，无需创建数据库表

---

### 7. 验证计划

#### 7.1 单元测试

**文件**：`fate/app/test/test_phone_verification.py`

测试用例（使用 fakeredis 模拟 Redis）：
- 验证码生成（6位数字）
- 频率限制（60秒内重复发送）
- IP 频率限制（60秒内最多3次）
- 每日限制（10次/天）
- 验证码验证（正确/错误/过期）
- 失败次数限制（5次后失效）
- Redis TTL 自动过期

#### 7.2 集成测试

**测试流程**：

1. **发送验证码**：
   ```bash
   curl -X POST http://localhost:8000/api/auth/phone/send-code \
     -H "Content-Type: application/json" \
     -d '{"phone": "13800138000"}'
   ```
   预期：返回 200，短信发送成功

2. **验证码登录（新用户）**：
   ```bash
   curl -X POST http://localhost:8000/api/auth/phone/login \
     -H "Content-Type: application/json" \
     -d '{"phone": "13800138000", "code": "123456", "nickname": "测试用户"}'
   ```
   预期：返回 200，包含 `access_token` 和 `is_new_user: true`

3. **验证码登录（老用户）**：
   ```bash
   # 使用相同手机号再次登录
   ```
   预期：返回 200，`is_new_user: false`

4. **频率限制测试**：
   ```bash
   # 60秒内重复发送
   ```
   预期：返回 429，提示"请求过于频繁"

5. **错误验证码测试**：
   ```bash
   # 使用错误的验证码
   ```
   预期：返回 400，提示"验证码错误，还剩 X 次尝试机会"

#### 7.3 前端测试

**测试场景**：

1. **正常登录流程**：
   - 输入手机号 → 获取验证码 → 输入验证码 → 登录成功
   - 验证 token 保存到 localStorage
   - 验证跳转到正确页面

2. **倒计时功能**：
   - 点击"获取验证码"后按钮禁用
   - 显示60秒倒计时
   - 倒计时结束后按钮重新启用

3. **错误处理**：
   - 手机号格式错误 → 显示错误提示
   - 验证码错误 → 显示错误提示
   - 网络错误 → 显示友好提示

4. **UI 响应式**：
   - 桌面端和移动端显示正常
   - Tab 切换流畅

#### 7.4 真实短信测试

**前置条件**：
1. 在腾讯云控制台创建短信应用
2. 申请短信签名（"易凡文化"）
3. 申请短信模板（验证码类型）
4. 配置 `.env` 文件

**测试步骤**：
1. 使用真实手机号发送验证码
2. 检查短信是否收到
3. 验证短信内容格式正确
4. 使用收到的验证码完成登录

---

## Critical Files

**后端（新建）**：
- `fate/app/services/phone_verification.py` - 验证码业务逻辑（基于 Redis）
- `fate/app/services/sms.py` - 腾讯云短信服务
- `fate/app/core/redis_client.py` - Redis 客户端封装（可选，可复用现有）

**后端（修改）**：
- `fate/app/routers/users.py` - 添加 `/auth/phone/send-code` 和 `/auth/phone/login` 端点
- `fate/app/services/users.py` - 添加 `get_or_create_by_phone()` 方法
- `fate/app/config.py` - 添加腾讯云短信配置（Redis 配置已存在）
- `fate/.env.example` - 添加短信服务环境变量
- `fate/requirements.txt` - 添加 `tencentcloud-sdk-python`

**前端（新建）**：
- `fate-frontend/app/components/PhoneLoginForm.tsx` - 手机登录表单组件
- `fate-frontend/app/lib/phone.ts` - 手机号验证工具

**前端（修改）**：
- `fate-frontend/app/(auth)/login/LoginClient.tsx` - 添加手机登录 Tab
- `fate-frontend/app/lib/auth.tsx` - 添加 `sendPhoneCode()` 和 `loginPhone()` 方法

**无需数据库迁移**：使用 Redis 存储验证码，无需创建数据库表

---

## Implementation Order

1. **Redis 环境准备**（15分钟）
   - 启动 Redis 服务（Docker 或本地）
   - 验证 Redis 连接
   - 确认 `REDIS_URL` 配置

2. **后端服务层**（2小时）
   - 实现 `sms.py`（腾讯云短信服务）
   - 实现 `phone_verification.py`（基于 Redis 的验证码逻辑）
   - 扩展 `users.py`（添加 `get_or_create_by_phone`）

3. **后端 API 层**（1.5小时）
   - 添加短信配置到 `config.py` 和 `.env.example`
   - 实现 `/auth/phone/send-code` 端点
   - 实现 `/auth/phone/login` 端点
   - 创建 Pydantic schemas

4. **前端实现**（2小时）
   - 创建 `PhoneLoginForm` 组件
   - 修改 `LoginClient.tsx` 添加 Tab 切换
   - 实现 API 客户端函数
   - 添加手机号验证工具

5. **测试验证**（1.5小时）
   - 单元测试（验证码生成、Redis 操作）
   - 集成测试（完整登录流程）
   - 前端测试（UI 交互）
   - 真实短信测试

**预计总时长**：7小时（比数据库方案节省1小时）

---

## Security Considerations

1. **频率限制**：
   - 单手机号：60秒内只能发送1次
   - 单IP：60秒内最多发送3次（需在 `send-code` 端点中实现）
   - 每日限制：单手机号每天最多10次

2. **验证码安全**：
   - 6位数字，5分钟有效期
   - 最多5次验证失败
   - 验证成功后立即标记为已使用

3. **手机号验证**：
   - 仅支持国内11位手机号（1开头）
   - 格式验证：`/^1[3-9]\d{9}$/`

4. **IP 记录**：
   - 每次发送验证码记录 IP 地址
   - 便于后续风控和异常行为分析

5. **短信内容**：
   - 必须包含签名【易凡文化】
   - 明确有效期（5分钟）
   - 提示非本人操作的处理方式
   - 不包含任何链接

---

## Cost Estimation

**腾讯云短信成本**：
- 验证码短信：0.045元/条
- 预估日活1000人，每人平均1.5次登录：1000 × 1.5 × 0.045 = 67.5元/天
- **月成本**：约2000元

**优化建议**：
- 引导用户使用微信登录（免费）
- 已登录用户使用 JWT 长期有效（7天），减少重复登录
- 实施严格的频率限制，防止恶意消耗

---

## Notes

- 本计划仅实现 MVP 核心功能（登录/注册），不包含账号绑定功能
- 后续可扩展：已有用户绑定手机号、小程序端支持、国际号码支持
- **使用 Redis 替代数据库存储验证码**，优势：
  - 性能更好（内存操作）
  - 自动过期（TTL 机制）
  - 实现更简单（无需数据库迁移）
  - 原子操作（INCR 计数器）
- 前端使用 Tab 切换而非独立页面，保持用户体验一致性
- Redis 已在项目中集成（`redis>=5.0.0`），无需额外安装
