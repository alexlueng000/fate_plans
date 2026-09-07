# 八字AI平台完整日志系统规划

## 一、当前问题诊断

### 1.1 后端（fate/）问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 混用 print() 和 logging | 高 | 日志不一致，无法统一管理 |
| 无统一日志配置 | 高 | 无法控制日志级别和输出 |
| 异常静默失败 | 严重 | 无法定位生产问题 |
| 无日志持久化 | 严重 | 重启后日志丢失 |
| 性能统计未持久化 | 中 | 无法分析系统性能趋势 |

**问题文件清单**：
- `app/chat/service.py` - 9处 print()
- `app/routers/chat.py` - 2处 print()
- `app/routers/bazi.py` - 3处 print()
- `app/deps.py` - 1处 print() + 静默异常
- `app/chat/utils.py` - 1处 print()

### 1.2 前端（fate-frontend/）问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 无错误上报机制 | 高 | 用户端错误无法追踪 |
| 无 API 调用日志 | 中 | 无法分析接口性能 |
| 仅 console.log 调试 | 低 | 生产环境无意义 |

### 1.3 微信小程序（fate_wechat/）问题

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 未使用微信日志 API | 高 | 无法利用平台能力 |
| 无错误上报 | 高 | 小程序崩溃无法追踪 |
| 大量 console 调试 | 低 | 生产环境无意义 |

---

## 二、日志系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        日志收集层                                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   fate (后端)   │  fate-frontend  │      fate_wechat            │
│   Python        │   Next.js       │      微信小程序              │
│   structlog     │   自定义Logger  │      wx.getLogManager       │
└────────┬────────┴────────┬────────┴────────────┬────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        日志传输层                                │
│   后端：文件 + 控制台                                            │
│   前端：API 上报到后端                                           │
│   小程序：wx.reportMonitor + API 上报                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        日志存储层                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │  文件存储   │  │   MySQL     │  │  (可选)     │            │
│   │  logs/*.log │  │  app_logs   │  │  ELK/Loki   │            │
│   └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 日志分类

| 日志类型 | 用途 | 存储位置 | 保留时间 |
|----------|------|----------|----------|
| 访问日志 | 请求追踪 | 文件 + DB | 30天 |
| 错误日志 | 问题排查 | 文件 + DB | 90天 |
| 业务日志 | 业务分析 | DB | 180天 |
| 性能日志 | 性能监控 | DB | 30天 |
| 审计日志 | 安全合规 | DB | 1年 |

---

## 三、后端日志系统实现

### 3.1 技术选型

**推荐方案**：`structlog` + `Python logging`

**理由**：
- 结构化日志，便于分析
- 与 Python logging 兼容
- 支持 JSON 输出
- 性能优秀

### 3.2 目录结构

```
fate/
├── app/
│   ├── core/
│   │   └── logging.py      # 日志配置（新增）
│   ├── middleware/
│   │   └── logging.py      # 请求日志中间件（新增）
│   └── ...
├── logs/                    # 日志文件目录（新增）
│   ├── app.log             # 应用日志
│   ├── error.log           # 错误日志
│   ├── access.log          # 访问日志
│   └── performance.log     # 性能日志
└── ...
```

### 3.3 核心代码实现

#### 3.3.1 日志配置 `app/core/logging.py`

```python
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import structlog
from datetime import datetime

# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
JSON_FORMAT = True  # 生产环境使用 JSON 格式

def setup_logging(log_level: str = "INFO"):
    """初始化日志系统"""

    # 1. 配置标准 logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除已有 handlers
    root_logger.handlers.clear()

    # 2. 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console_handler)

    # 3. 文件 Handler（按大小轮转，最大 10MB，保留 5 个）
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(file_handler)

    # 4. 错误日志 Handler（单独文件）
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(error_handler)

    # 5. 配置 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if JSON_FORMAT
                else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()

def get_logger(name: str = None):
    """获取 logger 实例"""
    return structlog.get_logger(name)
```

#### 3.3.2 请求日志中间件 `app/middleware/logging.py`

```python
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger("access")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 生成请求 ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 记录开始时间
        start_time = time.time()

        # 请求信息
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "")[:100],
        }

        try:
            response = await call_next(request)

            # 计算耗时
            duration_ms = (time.time() - start_time) * 1000

            log_data.update({
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            })

            # 根据状态码选择日志级别
            if response.status_code >= 500:
                logger.error("request_completed", **log_data)
            elif response.status_code >= 400:
                logger.warning("request_completed", **log_data)
            else:
                logger.info("request_completed", **log_data)

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_data.update({
                "status_code": 500,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__,
            })
            logger.exception("request_failed", **log_data)
            raise
```

#### 3.3.3 业务日志示例

```python
# 在 app/chat/service.py 中使用
from app.core.logging import get_logger

logger = get_logger("chat")

async def start_chat(...):
    logger.info("chat_started",
        conversation_id=cid,
        user_id=user_id,
        gender=gender
    )

    try:
        # 业务逻辑
        ...
        logger.info("chat_completed",
            conversation_id=cid,
            duration_ms=duration,
            tokens_used=tokens
        )
    except Exception as e:
        logger.exception("chat_failed",
            conversation_id=cid,
            error=str(e)
        )
        raise
```

### 3.4 性能日志

```python
# app/core/performance.py
from app.core.logging import get_logger
from contextlib import contextmanager
import time

perf_logger = get_logger("performance")

@contextmanager
def log_performance(operation: str, **extra):
    """性能日志上下文管理器"""
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        perf_logger.info(
            "performance",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **extra
        )

# 使用示例
with log_performance("rag_search", query=query):
    results = rag.search(query)
```

### 3.5 main.py 集成

```python
from fastapi import FastAPI
from app.core.logging import setup_logging
from app.middleware.logging import RequestLoggingMiddleware

# 初始化日志
logger = setup_logging(log_level="INFO")

app = FastAPI()

# 添加日志中间件
app.add_middleware(RequestLoggingMiddleware)

@app.on_event("startup")
async def startup():
    logger.info("application_started", version="1.0.0")

@app.on_event("shutdown")
async def shutdown():
    logger.info("application_stopped")
```

---

## 四、前端日志系统实现

### 4.1 日志服务 `app/lib/logger.ts`

```typescript
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

class Logger {
  private queue: LogEntry[] = [];
  private flushInterval: number = 5000; // 5秒批量上报
  private maxQueueSize: number = 50;

  constructor() {
    // 定时上报
    if (typeof window !== 'undefined') {
      setInterval(() => this.flush(), this.flushInterval);
      // 页面卸载前上报
      window.addEventListener('beforeunload', () => this.flush());
    }
  }

  private log(level: LogLevel, message: string, context?: Record<string, unknown>) {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
    };

    // 开发环境输出到控制台
    if (process.env.NODE_ENV === 'development') {
      console[level](message, context);
    }

    // 生产环境加入队列
    if (level === 'warn' || level === 'error') {
      this.queue.push(entry);
      if (this.queue.length >= this.maxQueueSize) {
        this.flush();
      }
    }
  }

  debug(message: string, context?: Record<string, unknown>) {
    this.log('debug', message, context);
  }

  info(message: string, context?: Record<string, unknown>) {
    this.log('info', message, context);
  }

  warn(message: string, context?: Record<string, unknown>) {
    this.log('warn', message, context);
  }

  error(message: string, error?: Error, context?: Record<string, unknown>) {
    const entry: LogEntry = {
      level: 'error',
      message,
      timestamp: new Date().toISOString(),
      context,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : undefined,
    };

    if (process.env.NODE_ENV === 'development') {
      console.error(message, error, context);
    }

    this.queue.push(entry);
    if (this.queue.length >= this.maxQueueSize) {
      this.flush();
    }
  }

  private async flush() {
    if (this.queue.length === 0) return;

    const logs = [...this.queue];
    this.queue = [];

    try {
      await fetch('/api/logs/client', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs }),
      });
    } catch (e) {
      // 上报失败，放回队列
      this.queue.unshift(...logs);
    }
  }
}

export const logger = new Logger();
```

### 4.2 全局错误捕获

```typescript
// app/lib/error-boundary.tsx
'use client';

import { Component, ReactNode } from 'react';
import { logger } from './logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('react_error', error, {
      componentStack: errorInfo.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <div>出错了，请刷新页面</div>;
    }
    return this.props.children;
  }
}
```

---

## 五、微信小程序日志实现

### 5.1 日志管理器 `miniprogram/utils/logger.ts`

```typescript
const logManager = wx.getLogManager({ level: 0 });
const realtimeLogManager = wx.getRealtimeLogManager();

interface LogContext {
  page?: string;
  action?: string;
  [key: string]: unknown;
}

class MiniProgramLogger {
  private context: LogContext = {};

  setContext(ctx: LogContext) {
    this.context = { ...this.context, ...ctx };
  }

  debug(message: string, data?: Record<string, unknown>) {
    const logData = { ...this.context, ...data };
    logManager.debug(message, logData);
  }

  info(message: string, data?: Record<string, unknown>) {
    const logData = { ...this.context, ...data };
    logManager.info(message, logData);
    realtimeLogManager?.info(message, logData);
  }

  warn(message: string, data?: Record<string, unknown>) {
    const logData = { ...this.context, ...data };
    logManager.warn(message, logData);
    realtimeLogManager?.warn(message, logData);
  }

  error(message: string, error?: Error, data?: Record<string, unknown>) {
    const logData = {
      ...this.context,
      ...data,
      errorName: error?.name,
      errorMessage: error?.message,
      errorStack: error?.stack,
    };
    logManager.warn(message, logData); // logManager 没有 error 级别
    realtimeLogManager?.error(message, logData);

    // 上报到后端
    this.reportToServer('error', message, logData);
  }

  // 性能监控
  reportPerformance(name: string, value: number) {
    wx.reportPerformance(name as any, value);
  }

  private async reportToServer(
    level: string,
    message: string,
    data: Record<string, unknown>
  ) {
    try {
      await wx.request({
        url: `${getApp().globalData.apiBase}/api/logs/miniprogram`,
        method: 'POST',
        data: {
          level,
          message,
          data,
          timestamp: new Date().toISOString(),
          systemInfo: wx.getSystemInfoSync(),
        },
      });
    } catch (e) {
      // 静默失败
    }
  }
}

export const logger = new MiniProgramLogger();
```

---

## 六、后端日志接收 API

### 6.1 日志接收路由 `app/routers/logs.py`

```python
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.logging import get_logger

router = APIRouter(prefix="/api/logs", tags=["logs"])
client_logger = get_logger("client")
mp_logger = get_logger("miniprogram")

class ClientLogEntry(BaseModel):
    level: str
    message: str
    timestamp: str
    context: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class ClientLogsRequest(BaseModel):
    logs: List[ClientLogEntry]

@router.post("/client")
async def receive_client_logs(request: Request, body: ClientLogsRequest):
    """接收前端日志"""
    client_ip = request.client.host if request.client else "unknown"

    for log in body.logs:
        log_method = getattr(client_logger, log.level, client_logger.info)
        log_method(
            log.message,
            client_ip=client_ip,
            timestamp=log.timestamp,
            **(log.context or {}),
            error=log.error
        )

    return {"status": "ok", "received": len(body.logs)}

@router.post("/miniprogram")
async def receive_mp_logs(request: Request, body: Dict[str, Any]):
    """接收小程序日志"""
    mp_logger.log(
        body.get("level", "info"),
        body.get("message", ""),
        **body.get("data", {}),
        system_info=body.get("systemInfo")
    )
    return {"status": "ok"}
```

---

## 七、数据库日志表设计

### 7.1 日志表 SQL

```sql
-- 应用日志表
CREATE TABLE app_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    logger_name VARCHAR(100),
    message TEXT,
    request_id VARCHAR(50),
    user_id INT,
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (level),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id),
    INDEX idx_request_id (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 性能日志表
CREATE TABLE performance_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    operation VARCHAR(100) NOT NULL,
    duration_ms DECIMAL(10,2) NOT NULL,
    request_id VARCHAR(50),
    user_id INT,
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_operation (operation),
    INDEX idx_created_at (created_at),
    INDEX idx_duration (duration_ms)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 客户端错误日志表
CREATE TABLE client_error_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source ENUM('web', 'miniprogram') NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT,
    error_name VARCHAR(100),
    error_message TEXT,
    error_stack TEXT,
    client_ip VARCHAR(50),
    user_agent VARCHAR(500),
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_level (level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 八、确定的实施计划（仅后端）

### 技术选型确认
- **日志库**：structlog + Python logging
- **存储方式**：文件存储（按大小轮转）
- **实施范围**：仅后端（fate/）

### 实施步骤

#### 步骤1：创建日志配置模块
**新增文件**：`fate/app/core/logging.py`
- 配置 structlog
- 配置文件 Handler（app.log, error.log）
- 配置控制台 Handler

#### 步骤2：创建请求日志中间件
**新增文件**：`fate/app/middleware/logging.py`
- 记录每个请求的 method, path, duration, status_code
- 生成 request_id 用于链路追踪

#### 步骤3：集成到 main.py
**修改文件**：`fate/main.py`
- 初始化日志系统
- 添加日志中间件

#### 步骤4：替换 print 为 logger
**修改文件**：
- `fate/app/chat/service.py` - 9处 print
- `fate/app/routers/chat.py` - 2处 print
- `fate/app/routers/bazi.py` - 3处 print
- `fate/app/deps.py` - 1处 print + 修复静默异常
- `fate/app/chat/utils.py` - 1处 print

#### 步骤5：添加依赖
**修改文件**：`fate/requirements.txt`
- 添加 `structlog>=24.0.0`

### 验证方式
1. 启动服务：`uvicorn main:app --reload`
2. 检查 `fate/logs/` 目录生成 `app.log` 和 `error.log`
3. 发送请求，检查访问日志记录
4. 触发错误，检查错误日志记录

### 后续扩展（暂不实施）
- 前端错误上报
- 小程序日志
- 数据库持久化
- ELK/Loki 集成

---

## 九、配置项

### 9.1 环境变量

```bash
# fate/.env
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json             # json, text
LOG_DIR=./logs              # 日志目录
LOG_MAX_SIZE=10485760       # 单文件最大 10MB
LOG_BACKUP_COUNT=5          # 保留文件数
LOG_TO_DB=false             # 是否写入数据库
```

### 9.2 日志级别说明

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 开发调试 | 变量值、SQL 语句 |
| INFO | 正常业务 | 用户登录、对话开始 |
| WARNING | 潜在问题 | 重试、降级 |
| ERROR | 错误异常 | 请求失败、异常捕获 |

---

## 十、总结

### 核心改进
1. **统一日志框架**：使用 structlog 替代 print
2. **结构化日志**：JSON 格式便于分析
3. **日志分级**：按级别分文件存储
4. **请求追踪**：request_id 贯穿全链路
5. **错误上报**：前端/小程序错误集中收集

### 预期效果
- 生产问题可追溯
- 性能瓶颈可分析
- 用户行为可统计
- 系统健康可监控
