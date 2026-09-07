# 本地开发到远程测试服务器部署流程

## 概述

本文档描述从本地开发环境部署代码到远程测试服务器的标准流程。

## 前提条件

- 本地已配置 Git 并有远程仓库访问权限
- 远程测试服务器已配置好运行环境
- SSH 访问远程服务器的权限

---

## 1. 本地开发与提交

### 1.1 创建功能分支（首次）

```bash
# 后端
cd fate
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 前端
cd fate-frontend
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### 1.2 开发完成后提交代码

```bash
# 后端
cd fate
git add .
git commit -m "feat: 功能描述"
git push -u origin feature/your-feature-name

# 前端
cd fate-frontend
git add .
git commit -m "feat: 功能描述"
git push -u origin feature/your-feature-name
```

---

## 2. 远程测试服务器部署

SSH 登录到测试服务器后执行以下操作。

### 2.1 后端部署

```bash
# 进入后端目录
cd /opt/fate/fate

# 拉取最新代码
git fetch origin
git checkout feature/your-feature-name
git pull origin feature/your-feature-name

# 激活虚拟环境
source venv/bin/activate

# 安装新依赖（如有）
pip install -r requirements.txt

# 数据库迁移（如有新表或字段变更）
python init_db.py
# 或使用 alembic
# alembic upgrade head

# 重启后端服务
sudo systemctl restart fate-backend
# 或使用 pm2
# pm2 restart fate-backend
```

### 2.2 前端部署

```bash
# 进入前端目录
cd /opt/fate/fate-frontend

# 拉取最新代码
git fetch origin
git checkout feature/your-feature-name
git pull origin feature/your-feature-name

# 安装依赖（如有新增）
npm install

# 构建生产版本
npm run build

# 重启前端服务
sudo systemctl restart fate-frontend
# 或使用 pm2
# pm2 restart fate-frontend
```

### 2.3 验证部署

```bash
# 检查后端服务状态
curl http://localhost:8000/api/ping
# 期望: {"ok": true, "app": "Bazi AI Backend"}

# 检查前端服务状态
curl http://localhost:3000
# 期望: HTML 内容

# 查看服务日志（如有问题）
journalctl -u fate-backend -f
journalctl -u fate-frontend -f
```

---

## 3. 测试通过后合并到 develop

在本地执行：

```bash
# 后端
cd fate
git checkout develop
git pull origin develop
git merge feature/your-feature-name
git push origin develop

# 前端
cd fate-frontend
git checkout develop
git pull origin develop
git merge feature/your-feature-name
git push origin develop

# （可选）删除功能分支
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## 4. 快速部署脚本（可选）

可以在测试服务器上创建部署脚本简化操作。

### 创建脚本 `/opt/fate/deploy.sh`

```bash
#!/bin/bash
set -e

BRANCH=${1:-develop}
echo "=== 部署分支: $BRANCH ==="

# 后端
echo ">>> 部署后端..."
cd /opt/fate/fate
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fate-backend

# 前端
echo ">>> 部署前端..."
cd /opt/fate/fate-frontend
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
npm install
npm run build
sudo systemctl restart fate-frontend

echo "=== 部署完成 ==="
```

### 使用方式

```bash
# 部署 develop 分支
./deploy.sh develop

# 部署功能分支
./deploy.sh feature/password-reset
```

---

## 5. 常见问题

### 5.1 后端启动失败

```bash
# 查看详细错误日志
journalctl -u fate-backend -n 50

# 常见原因：
# - 依赖未安装：pip install -r requirements.txt
# - 数据库连接失败：检查 .env 中的 DATABASE_URL
# - 端口被占用：lsof -i :8000
```

### 5.2 前端构建失败

```bash
# 清理缓存后重新构建
rm -rf .next node_modules
npm install
npm run build
```

### 5.3 数据库表不存在

```bash
# 重新初始化数据库表
cd /opt/fate/fate
source venv/bin/activate
python init_db.py
```

---

## 6. 环境变量配置

首次部署新功能时，可能需要在 `.env` 文件中添加新的环境变量。

### 后端 (`fate/.env`)

```bash
# 示例：SMTP 邮件配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USERNAME=your_email@qq.com
SMTP_PASSWORD=your_smtp_password
SMTP_SENDER=your_email@qq.com
SMTP_USE_TLS=true
```

### 前端 (`fate-frontend/.env.local`)

```bash
# API 地址（通过 Nginx 代理）
NEXT_PUBLIC_API_BASE=http://your-server-ip
```
