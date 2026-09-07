# 八字风水平台 v1.0 发布与部署计划

## 一、Git Tag 发布

### 需要打 tag 的仓库
| 仓库 | 路径 | 状态 | 远程地址 |
|------|------|------|----------|
| fate (后端) | `E:\claude_projects\chat\fate` | 干净 | git@github.com:alexlueng000/fate.git |
| fate-frontend (前端) | `E:\claude_projects\chat\fate-frontend` | 干净 | git@github.com:alexlueng000/fate-frontend.git |
| fate_wechat (小程序) | `E:\claude_projects\chat\fate_wechat` | 暂不处理 | - |

### 执行命令
```bash
# 后端
cd E:\claude_projects\chat\fate
git tag -a v1.0.0 -m "Release v1.0.0 - 八字风水平台首个正式版本"
git push origin v1.0.0

# 前端
cd E:\claude_projects\chat\fate-frontend
git tag -a v1.0.0 -m "Release v1.0.0 - 八字风水平台首个正式版本"
git push origin v1.0.0
```

---

## 二、线上部署方案 (Docker + Nginx)

### 架构图
```
                    ┌─────────────────────────────────────┐
                    │           Nginx (443/80)            │
                    │  - SSL 终止                          │
                    │  - 反向代理                          │
                    │  - 负载均衡                          │
                    └─────────────┬───────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   api.fateinsight.site    yizhanmaster.site    fateinsight.site
            │                     │                     │
            ▼                     └──────────┬──────────┘
   ┌────────────────┐                        │
   │ fate-backend   │                        ▼
   │ (FastAPI:8000) │              ┌────────────────┐
   └────────────────┘              │ fate-frontend  │
            │                      │ (Next.js:3000) │
            ▼                      └────────────────┘
   ┌────────────────┐
   │ MySQL 8.4      │
   │ 43.139.4.252   │
   └────────────────┘
```

### 需要创建的文件

#### 1. 后端 Dockerfile (`fate/Dockerfile`)
- 多阶段构建优化镜像大小
- 使用 PyTorch CPU 版本（减小体积）
- 非 root 用户运行
- 健康检查端点

#### 2. 前端 Dockerfile (`fate-frontend/Dockerfile`)
- Next.js standalone 输出模式
- 多阶段构建
- 非 root 用户运行

#### 3. Docker Compose (`docker-compose.yml`)
- 编排 backend、frontend、nginx 三个服务
- 环境变量通过 .env 文件注入
- 服务健康检查和依赖关系

#### 4. Nginx 配置
- `nginx/nginx.conf` - 主配置
- `nginx/conf.d/api.fateinsight.site.conf` - API 域名
- `nginx/conf.d/yizhanmaster.site.conf` - 前端域名

#### 5. 环境变量 (`.env`)
```
DB_PASSWORD=xxx
JWT_SECRET=xxx (需要更换为强随机字符串)
DEEPSEEK_API_KEY=xxx
WX_APPID=xxx
WX_SECRET=xxx
```

### 部署步骤

1. **服务器准备**
   - 安装 Docker 和 Docker Compose
   - 创建项目目录 `/opt/fate-app`

2. **传输代码**
   - Git clone 或 scp 传输项目文件

3. **SSL 证书**
   - 使用 Certbot 获取 Let's Encrypt 证书
   - 配置自动续期

4. **配置环境变量**
   - 创建 `.env` 文件
   - 更换 JWT_SECRET 为强随机字符串

5. **修改前端配置**
   - `next.config.ts` 添加 `output: 'standalone'`

6. **构建和启动**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

7. **验证部署**
   - 测试 API: `curl https://api.fateinsight.site/api/healthz`
   - 测试前端: `curl https://yizhanmaster.site`

---

## 三、关键文件修改清单

| 操作 | 文件路径 |
|------|----------|
| 新建 | `fate/Dockerfile` |
| 新建 | `fate-frontend/Dockerfile` |
| 新建 | `docker-compose.yml` (项目根目录) |
| 新建 | `nginx/nginx.conf` |
| 新建 | `nginx/conf.d/api.fateinsight.site.conf` |
| 新建 | `nginx/conf.d/yizhanmaster.site.conf` |
| 新建 | `.env` (项目根目录) |
| 修改 | `fate-frontend/next.config.ts` (添加 output: 'standalone') |

---

## 四、验证方案

1. **本地测试**
   ```bash
   docker-compose up -d
   curl http://localhost:8000/api/healthz
   curl http://localhost:3000
   ```

2. **生产验证**
   - 访问 https://yizhanmaster.site 确认前端正常
   - 访问 https://api.fateinsight.site/api/healthz 确认后端正常
   - 测试八字计算功能
   - 测试 AI 对话流式响应

3. **日志检查**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   docker-compose logs -f nginx
   ```

---

## 五、配置文件详细内容

### 1. 后端 Dockerfile (`fate/Dockerfile`)

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 从 builder 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY --chown=appuser:appgroup . .

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/healthz')" || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 前端 Dockerfile (`fate-frontend/Dockerfile`)

```dockerfile
# ============================================
# Stage 1: Dependencies
# ============================================
FROM node:20-alpine AS deps

WORKDIR /app

# 复制 package 文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci --only=production

# ============================================
# Stage 2: Builder
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 设置环境变量
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# 构建应用
RUN npm run build

# ============================================
# Stage 3: Runner
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制构建产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
```

### 3. Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  # ============================================
  # 后端服务
  # ============================================
  backend:
    build:
      context: ./fate
      dockerfile: Dockerfile
    container_name: fate-backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:3306/fate
      - JWT_SECRET=${JWT_SECRET}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - AMAP_KEY=${AMAP_KEY}
    volumes:
      - ./fate/kb_index:/app/kb_index:ro
      - ./fate/kb_files:/app/kb_files:ro
    networks:
      - fate-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/healthz')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # ============================================
  # 前端服务
  # ============================================
  frontend:
    build:
      context: ./fate-frontend
      dockerfile: Dockerfile
    container_name: fate-frontend
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_BASE=https://api.fateinsight.site
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - fate-network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  # ============================================
  # Nginx 反向代理
  # ============================================
  nginx:
    image: nginx:alpine
    container_name: fate-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - fate-network

networks:
  fate-network:
    driver: bridge
```

### 4. Nginx 主配置 (`nginx/nginx.conf`)

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # 性能优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript
               application/xml application/xml+rss text/javascript application/x-javascript;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 上传大小限制
    client_max_body_size 10M;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
}
```

### 5. API 域名配置 (`nginx/conf.d/api.fateinsight.site.conf`)

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name api.fateinsight.site;
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name api.fateinsight.site;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/api.fateinsight.site/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/api.fateinsight.site/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # 反向代理到后端
    location / {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        chunked_transfer_encoding off;
    }

    # 健康检查端点
    location /api/healthz {
        proxy_pass http://backend:8000/api/healthz;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### 6. 前端域名配置 (`nginx/conf.d/yizhanmaster.site.conf`)

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name yizhanmaster.site fateinsight.site;
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置 - yizhanmaster.site
server {
    listen 443 ssl http2;
    server_name yizhanmaster.site;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/yizhanmaster.site/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/yizhanmaster.site/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # 反向代理到前端
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
    }

    # 静态资源缓存
    location /_next/static {
        proxy_pass http://frontend:3000/_next/static;
        proxy_cache_valid 60m;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
}

# HTTPS 配置 - fateinsight.site (重定向到主域名)
server {
    listen 443 ssl http2;
    server_name fateinsight.site;

    ssl_certificate /etc/nginx/ssl/fateinsight.site/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/fateinsight.site/privkey.pem;

    return 301 https://yizhanmaster.site$request_uri;
}
```

### 7. 环境变量模板 (`.env.example`)

```bash
# ============================================
# 数据库配置
# ============================================
DB_USER=fate_user
DB_PASSWORD=your_secure_password_here
DB_HOST=43.139.4.252

# ============================================
# JWT 配置
# ============================================
# 生成方式: openssl rand -hex 32
JWT_SECRET=your_32_byte_random_hex_string_here

# ============================================
# AI 服务
# ============================================
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# 高德地图 API
# ============================================
AMAP_KEY=your_amap_key_here

# ============================================
# 微信小程序 (可选)
# ============================================
WX_APPID=wxcfefbcb12af67c8f
WX_SECRET=your_wx_secret_here
```

---

## 六、前端配置修改

### 修改 `fate-frontend/next.config.ts`

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 启用 standalone 输出模式（Docker 部署必需）
  output: 'standalone',

  // 现有配置...
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_BASE
          ? `${process.env.NEXT_PUBLIC_API_BASE}/api/:path*`
          : 'https://api.fateinsight.site/api/:path*',
      },
    ];
  },
};

export default nextConfig;
```

---

## 七、部署命令速查

```bash
# 1. 克隆代码到服务器
cd /opt
git clone git@github.com:alexlueng000/fate.git
git clone git@github.com:alexlueng000/fate-frontend.git

# 2. 创建目录结构
mkdir -p /opt/fate-app/nginx/{conf.d,ssl,logs}

# 3. 复制配置文件
cp docker-compose.yml /opt/fate-app/
cp -r nginx/* /opt/fate-app/nginx/

# 4. 创建环境变量文件
cp .env.example /opt/fate-app/.env
vim /opt/fate-app/.env  # 编辑填入实际值

# 5. 获取 SSL 证书 (使用 Certbot)
certbot certonly --standalone -d api.fateinsight.site
certbot certonly --standalone -d yizhanmaster.site
certbot certonly --standalone -d fateinsight.site

# 复制证书到 nginx 目录
cp -rL /etc/letsencrypt/live/api.fateinsight.site /opt/fate-app/nginx/ssl/
cp -rL /etc/letsencrypt/live/yizhanmaster.site /opt/fate-app/nginx/ssl/
cp -rL /etc/letsencrypt/live/fateinsight.site /opt/fate-app/nginx/ssl/

# 6. 构建并启动
cd /opt/fate-app
docker-compose build --no-cache
docker-compose up -d

# 7. 查看日志
docker-compose logs -f

# 8. 重启服务
docker-compose restart backend
docker-compose restart frontend

# 9. 停止服务
docker-compose down

# 10. 更新部署
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

---

## 八、故障排查

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 502 Bad Gateway | 后端服务未启动 | `docker-compose logs backend` 查看日志 |
| 数据库连接失败 | 环境变量配置错误 | 检查 `.env` 中的数据库配置 |
| SSL 证书错误 | 证书路径不正确 | 检查 nginx ssl 目录下的证书文件 |
| SSE 流式响应中断 | Nginx 缓冲配置 | 确认 `proxy_buffering off` 已设置 |
| 前端 API 调用失败 | CORS 或代理配置 | 检查 `next.config.ts` 中的 rewrites |

### 日志位置

```bash
# Docker 容器日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# Nginx 访问日志
tail -f /opt/fate-app/nginx/logs/access.log

# Nginx 错误日志
tail -f /opt/fate-app/nginx/logs/error.log
```
