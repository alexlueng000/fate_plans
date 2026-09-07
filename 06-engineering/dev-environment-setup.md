# 开发环境搭建计划

## 概述

为八字风水平台搭建独立的在线开发环境，供异地团队协作开发使用，同时保护生产环境稳定。

**范围**：后端 (fate/) + 前端 (fate-frontend/)
**不涉及**：微信小程序（用户明确不需要）

---

## 环境架构

```
用户浏览器
    ↓
  Nginx (80/443)
    ├── /api/*  → 后端 (localhost:8000)
    └── /*      → 前端 (localhost:3000)

生产环境                          开发环境
─────────────────────────────    ─────────────────────────────
Nginx (80/443)                   Nginx (80)
  ├── api.fateinsight.site         ├── <开发服务器IP>/api/*
  │     → 后端 FastAPI                   → 后端 FastAPI (:8000)
  │     → MySQL: fate                    → MySQL: fate_dev
  │
  └── yizhanmaster.site            └── <开发服务器IP>/*
        → 前端 Next.js                   → 前端 Next.js (:3000)
```

---

## Nginx 配置（重要）

### 为什么需要 Nginx？

前端的 API 请求是从**用户浏览器**发出的，如果前端配置 `localhost:8000`，浏览器会请求用户自己电脑的 8000 端口，而不是服务器。

使用 Nginx 作为反向代理可以：
1. 统一入口，前端请求 `/api/*` 由 Nginx 转发到后端
2. 支持 HTTPS（SSL 证书）
3. 负载均衡、缓存等高级功能

### 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx -y

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 创建 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/fate
```

写入以下内容：

```nginx
server {
    listen 80;
    server_name 81.71.4.86;  # 替换为你的服务器 IP 或域名

    # 前端 - Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API - FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE (Server-Sent Events) 支持 - 用于流式响应
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### 启用配置

```bash
# 创建软链接启用配置
sudo ln -s /etc/nginx/sites-available/fate /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置语法
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 前端重新构建

前端需要重新构建，API 地址改为通过 Nginx 访问：

```bash
cd /srv/fate/frontend

# 重新构建，API 地址使用服务器 IP（不带端口，走 Nginx 80 端口）
docker build --build-arg NEXT_PUBLIC_API_BASE=http://81.71.4.86 -t fate-frontend .

# 重启前端容器
docker stop fate-frontend && docker rm fate-frontend
docker run -d -p 3000:3000 --name fate-frontend fate-frontend
```

### 验证

```bash
# 测试 Nginx 是否正常转发
curl http://81.71.4.86/api/ping
# 期望: {"ok": true, "app": "Bazi AI Backend"}

# 测试前端
curl http://81.71.4.86/
# 期望: HTML 内容
```

### 配置 HTTPS（生产环境推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx -y

# 申请证书（需要先配置域名解析）
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 实施步骤

### 第一步：后端环境分离

#### 1.1 修改 `fate/app/config.py`

添加 `APP_ENV` 环境变量，修改默认数据库 URL 为本地（安全默认）：

```python
# 在 Settings 类中添加
app_env: str = "development"  # "development" | "production"

# 修改数据库默认值（第33行）
# 原: database_url: str = "mysql+pymysql://fate_app:Turkey414@43.139.4.252:3306/fate"
# 改为:
database_url: str = "mysql+pymysql://fate_app:Turkey414@127.0.0.1:3306/fate_dev"

# 添加辅助方法
def is_production(self) -> bool:
    return self.app_env == "production"
```

#### 1.2 创建 `fate/.env.example`

```bash
# 环境标识
APP_ENV=development  # development | production

# 数据库
DATABASE_URL=mysql+pymysql://fate_app:password@127.0.0.1:3306/fate_dev

# JWT (生产环境必须修改)
JWT_SECRET=change-me-in-production

# CORS
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 微信小程序
WX_APPID=your_appid
WX_SECRET=your_secret

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxx

# 微信支付
WECHAT_PAY_MODE=dev
```

#### 1.3 开发服务器 `.env` 配置

```bash
APP_ENV=development
DATABASE_URL=mysql+pymysql://fate_app:Turkey414@127.0.0.1:3306/fate_dev
JWT_SECRET=dev-jwt-secret-key
CORS_ALLOW_ORIGINS=*
# ... 其他配置
```

#### 1.4 生产服务器 `.env` 配置（确认现有配置）

```bash
APP_ENV=production
DATABASE_URL=mysql+pymysql://fate_app:Turkey414@43.139.4.252:3306/fate
JWT_SECRET=<生产密钥>
CORS_ALLOW_ORIGINS=https://yizhanmaster.site,https://api.fateinsight.site
# ... 其他配置
```

---

### 第二步：前端环境分离

#### 2.1 修改 `fate-frontend/next.config.ts`

将硬编码的 API URL 改为环境变量（第30行）：

```typescript
// 原:
destination: 'https://api.fateinsight.site/api/:path*',

// 改为:
destination: `${process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'}/api/:path*`,
```

#### 2.2 创建 `fate-frontend/.env.example`

```bash
# 后端 API 地址
# 开发: http://<开发服务器IP>:8000
# 生产: https://api.fateinsight.site
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

#### 2.3 开发服务器前端配置

创建 `fate-frontend/.env.local`：
```bash
NEXT_PUBLIC_API_BASE=http://<开发服务器IP>:8000
```

#### 2.4 生产服务器前端配置

创建 `fate-frontend/.env.local`：
```bash
NEXT_PUBLIC_API_BASE=https://api.fateinsight.site
```

---

### 第三步：开发服务器数据库配置

在开发服务器上运行 Docker MySQL：

```bash
docker run -d \
  --name mysql8-dev \
  -p 127.0.0.1:3306:3306 \
  -e MYSQL_ROOT_PASSWORD=devpassword \
  -e MYSQL_DATABASE=fate_dev \
  -e MYSQL_USER=fate_app \
  -e MYSQL_PASSWORD=Turkey414 \
  -e TZ=Asia/Shanghai \
  -v mysql8-dev-data:/var/lib/mysql \
  mysql:8.4 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_0900_ai_ci
```

初始化数据库表：
```bash
cd fate
python init_db.py
```

---

### 第四步：开发服务器部署

#### 4.1 后端部署

```bash
# 克隆代码
git clone <repo> /opt/fate

# 配置环境
cd /opt/fate/fate
cp .env.example .env
# 编辑 .env 设置开发环境配置

# 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4.2 前端部署

```bash
cd /opt/fate/fate-frontend

# 配置环境
echo "NEXT_PUBLIC_API_BASE=http://<开发服务器IP>:8000" > .env.local

# 安装依赖并构建
npm install
npm run build

# 启动服务
npm run start -- -p 3000
```

---

### 第五步：更新后端 Dockerfile

#### 5.1 当前问题

- 知识库索引需要在构建时打包，而非运行时构建
- 需要支持开发/生产两种启动模式

#### 5.2 修改 `fate/Dockerfile`

```dockerfile
# fate/Dockerfile
# Multi-stage build for FastAPI backend with ML dependencies

# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install PyTorch CPU version first (much smaller than GPU version)
RUN pip install --no-cache-dir \
    torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime - Final image
# ============================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# ========== 新增：构建知识库索引 ==========
# 在构建镜像时生成索引，而非运行时
RUN python kb_rag_mult.py ingest -i ./kb_files -o ./kb_index || echo "KB index build skipped (no files or error)"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ========== 新增：环境模式变量 ==========
# 默认生产模式，可通过 docker run -e APP_ENV=development 覆盖
ENV APP_ENV=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/healthz || exit 1

# ========== 修改：使用启动脚本支持多模式 ==========
COPY docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
```

#### 5.3 创建 `fate/docker-entrypoint.sh`

```bash
#!/bin/bash
set -e

# 根据 APP_ENV 选择启动模式
if [ "$APP_ENV" = "development" ]; then
    echo "Starting in DEVELOPMENT mode (hot reload enabled)..."
    exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting in PRODUCTION mode (multi-worker)..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
fi
```

#### 5.4 使用方式

```bash
# 构建镜像（会自动构建知识库索引）
docker build -t fate-backend .

# 生产环境运行（默认）
docker run -d -p 8000:8000 --env-file .env fate-backend

# 开发环境运行（热重载）
docker run -d -p 8000:8000 -e APP_ENV=development -v $(pwd):/app fate-backend
```

---

## 需要修改的文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `fate/app/config.py` | 修改 | 添加 APP_ENV，修改默认 DATABASE_URL |
| `fate/.env.example` | 新建 | 环境变量模板 |
| `fate/Dockerfile` | 修改 | 添加 KB 索引构建，支持开发/生产模式 |
| `fate/docker-entrypoint.sh` | 新建 | 启动脚本，根据环境选择启动模式 |
| `fate-frontend/next.config.ts` | 修改 | API URL 改为环境变量 |
| `fate-frontend/.env.example` | 新建 | 环境变量模板 |

---

## 验证方案

### 后端验证

```bash
# 在开发服务器上
curl http://<开发服务器IP>:8000/api/ping
# 期望: {"ok": true, "app": "Bazi AI Backend"}

curl http://<开发服务器IP>:8000/api/healthz
# 期望: {"status": "ok"}
```

### 前端验证

1. 访问 `http://<开发服务器IP>:3000`
2. 打开浏览器开发者工具 Network 面板
3. 确认 API 请求发送到开发服务器而非生产服务器
4. 测试登录/注册流程

### 数据库隔离验证

```bash
# 在开发服务器上
mysql -u fate_app -p -h 127.0.0.1 fate_dev -e "SHOW TABLES;"
# 确认使用的是 fate_dev 数据库
```

---

## 安全注意事项

1. **开发服务器防火墙**：仅开放 8000 和 3000 端口给团队成员 IP
2. **JWT 密钥**：开发和生产使用不同的密钥
3. **数据库**：开发数据库不包含真实用户数据
4. **CORS**：开发环境可以设置 `*`，生产环境必须限制域名

---

## 后续开发部署最佳实践

### Git 分支策略

```
main (生产分支)
  │
  ├── develop (开发分支，部署到开发服务器)
  │     │
  │     ├── feature/xxx (功能分支)
  │     ├── feature/yyy
  │     └── bugfix/zzz
  │
  └── hotfix/xxx (紧急修复，直接合并到 main)
```

**分支规则**：
- `main`: 生产环境代码，只接受来自 `develop` 或 `hotfix` 的合并
- `develop`: 开发环境代码，功能开发完成后合并到此分支
- `feature/*`: 新功能开发，从 `develop` 创建，完成后合并回 `develop`
- `hotfix/*`: 紧急修复，从 `main` 创建，修复后同时合并到 `main` 和 `develop`

---

### 日常开发流程

```
1. 从 develop 创建功能分支
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature

2. 开发并提交
   git add .
   git commit -m "feat: 添加新功能"

3. 推送并创建 PR
   git push origin feature/new-feature
   # 在 GitHub/GitLab 创建 PR 到 develop

4. 代码审查通过后合并到 develop
   # develop 分支自动部署到开发服务器

5. 测试通过后，从 develop 合并到 main
   # main 分支部署到生产服务器
```

---

### 数据库迁移策略

#### 使用 Alembic 管理迁移

```bash
# 1. 修改模型后，生成迁移脚本
cd fate
alembic revision --autogenerate -m "add user avatar field"

# 2. 检查生成的迁移脚本
# 文件位于 migrations/versions/xxx_add_user_avatar_field.py

# 3. 在开发环境测试迁移
alembic upgrade head

# 4. 确认无误后提交迁移脚本
git add migrations/
git commit -m "migration: add user avatar field"

# 5. 生产环境部署时执行迁移
alembic upgrade head
```

#### 迁移注意事项

- **先备份**：生产环境迁移前必须备份数据库
- **可回滚**：确保每个迁移都有对应的 downgrade 方法
- **小步迭代**：避免一次性大规模修改表结构
- **非破坏性**：优先使用添加列而非删除列

---

### 进程管理（推荐使用 systemd 或 pm2）

#### 方案一：systemd（推荐）

创建 `/etc/systemd/system/fate-backend.service`：
```ini
[Unit]
Description=Fate Backend API
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fate/fate
Environment="PATH=/opt/fate/fate/venv/bin"
ExecStart=/opt/fate/fate/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/fate-frontend.service`：
```ini
[Unit]
Description=Fate Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fate/fate-frontend
ExecStart=/usr/bin/npm run start -- -p 3000
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable fate-backend fate-frontend
sudo systemctl start fate-backend fate-frontend
```

#### 方案二：pm2

```bash
# 安装 pm2
npm install -g pm2

# 后端
cd /opt/fate/fate
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name fate-backend

# 前端
cd /opt/fate/fate-frontend
pm2 start npm --name fate-frontend -- run start -- -p 3000

# 保存配置
pm2 save
pm2 startup
```

---

### 日志管理

#### 后端日志

```python
# 在 main.py 或 config.py 中配置
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/fate/backend.log'),
        logging.StreamHandler()
    ]
)
```

#### 日志轮转

创建 `/etc/logrotate.d/fate`：
```
/var/log/fate/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

#### 查看日志

```bash
# systemd 日志
journalctl -u fate-backend -f
journalctl -u fate-frontend -f

# 文件日志
tail -f /var/log/fate/backend.log
```

---

### 回滚策略

#### 代码回滚

```bash
# 1. 查看提交历史
git log --oneline -10

# 2. 回滚到指定版本
git checkout <commit-hash>

# 3. 或者回滚最近一次合并
git revert -m 1 HEAD

# 4. 重启服务
sudo systemctl restart fate-backend fate-frontend
```

#### 数据库回滚

```bash
# 回滚最近一次迁移
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>

# 查看迁移历史
alembic history
```

#### 紧急回滚清单

1. [ ] 停止服务
2. [ ] 回滚代码 `git checkout <last-stable-commit>`
3. [ ] 回滚数据库（如需要）`alembic downgrade -1`
4. [ ] 重启服务
5. [ ] 验证服务正常
6. [ ] 通知团队

---

### 监控建议

#### 基础监控

```bash
# 服务状态检查脚本 /opt/fate/scripts/health_check.sh
#!/bin/bash

# 检查后端
if ! curl -s http://localhost:8000/api/ping | grep -q "ok"; then
    echo "Backend is down!"
    # 发送告警（邮件/钉钉/微信）
fi

# 检查前端
if ! curl -s http://localhost:3000 | grep -q "html"; then
    echo "Frontend is down!"
fi

# 检查数据库
if ! mysqladmin ping -h 127.0.0.1 -u fate_app -pTurkey414 2>/dev/null; then
    echo "Database is down!"
fi
```

添加到 crontab：
```bash
*/5 * * * * /opt/fate/scripts/health_check.sh >> /var/log/fate/health_check.log 2>&1
```

#### 推荐监控工具

- **Uptime Kuma**: 轻量级自托管监控
- **Prometheus + Grafana**: 完整监控方案
- **Sentry**: 错误追踪和性能监控

---

### CI/CD 建议（可选）

#### GitHub Actions 示例

创建 `.github/workflows/deploy-dev.yml`：
```yaml
name: Deploy to Development

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to dev server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DEV_SERVER_IP }}
          username: ${{ secrets.DEV_SERVER_USER }}
          key: ${{ secrets.DEV_SERVER_SSH_KEY }}
          script: |
            cd /opt/fate
            git pull origin develop
            cd fate && source venv/bin/activate && pip install -r requirements.txt
            sudo systemctl restart fate-backend
            cd ../fate-frontend && npm install && npm run build
            sudo systemctl restart fate-frontend
```

---

### 环境变量管理建议

1. **不要提交 `.env` 文件**：确保 `.gitignore` 包含 `.env*`（除了 `.env.example`）
2. **使用 `.env.example` 作为模板**：新成员可以复制并修改
3. **敏感信息**：考虑使用密钥管理服务（如 HashiCorp Vault）
4. **环境变量文档**：在 README 或 CLAUDE.md 中说明每个变量的用途
