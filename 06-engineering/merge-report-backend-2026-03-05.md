# 后端 develop → main 合并差异报告

**生成时间**: 2026-03-05
**分支**: develop → main
**提交数量**: 18 个提交
**文件变更**: 20 个文件，+1330 行，-31 行

---

## 📊 变更统计

### 新增文件 (6个)
- `app/models/message_rating.py` - 消息评价模型
- `app/models/quota.py` - 用户配额模型
- `app/models/usage_log.py` - 使用日志模型
- `app/routers/message_rating.py` - 消息评价 API
- `app/routers/user_stats.py` - 用户统计 API
- `app/schemas/message_rating.py` - 消息评价 Schema

### 修改文件 (12个)
- `.gitignore` - 忽略规则更新
- `app/chat/service.py` - 聊天服务增强（+149行）
- `app/config.py` - 配置更新
- `app/deps.py` - 依赖注入更新
- `app/models/__init__.py` - 模型导入更新
- `app/models/user.py` - 用户模型扩展
- `app/routers/admin_stats.py` - 管理统计增强（+212行）
- `app/routers/chat.py` - 聊天路由更新
- `app/routers/users.py` - 用户路由扩展
- `app/services/quota.py` - 配额服务（+213行）
- `kb_rag_mult.py` - RAG 知识库更新
- `main.py` - 主应用更新

### 新增知识库文档 (2个)
- 八字命理文档（去图片版）
- 八宫卦取卦逻辑文档

---

## 🎯 主要功能变更

### 1. 消息评价功能 ⭐
**提交**: `9a365fb - add message rating feature`

**新增内容**:
- 消息点赞/点踩功能
- 点踩原因选择（预设 + 自定义）
- 命盘数据保存（用于分析）
- 管理员查看评价列表 API

**涉及文件**:
- `app/models/message_rating.py` - 数据模型
- `app/routers/message_rating.py` - API 路由
- `app/schemas/message_rating.py` - 请求/响应 Schema
- `app/chat/service.py` - 消息保存时返回 message_id

**数据库变更**:
- 新增 `message_ratings` 表
- 字段: id, message_id, user_id, rating_type, reason, paipan_data, created_at
- 索引: message_id, user_id, (message_id, user_id) unique

---

### 2. 用户配额管理 ⭐
**提交**: `b762d56 - add user quota management`

**新增内容**:
- 用户配额系统（对话次数、消息次数限制）
- 使用日志记录
- 配额检查和扣减服务
- 管理员配额管理 API

**涉及文件**:
- `app/models/quota.py` - 配额模型
- `app/models/usage_log.py` - 使用日志模型
- `app/services/quota.py` - 配额服务逻辑
- `app/models/user.py` - 用户模型扩展（添加配额关系）

**数据库变更**:
- 新增 `user_quotas` 表
- 新增 `usage_logs` 表

---

### 3. 知识库增强 ⭐
**提交**: `70ddc25 - add knowledge base`

**新增内容**:
- 新增八字命理知识库文档
- 新增八宫卦取卦逻辑文档
- RAG 知识库功能优化

**涉及文件**:
- `kb_rag_mult.py` - RAG 处理逻辑更新
- 新增知识库文档（.docx 格式）

---

### 4. 统计功能增强 ⭐
**提交**: `1765616 - add logs`, 更新 `admin_stats.py`

**新增内容**:
- 管理员统计数据增强（+212行）
- 用户统计 API（新增 `user_stats.py`）
- 日志记录功能

**涉及文件**:
- `app/routers/admin_stats.py` - 管理统计扩展
- `app/routers/user_stats.py` - 用户统计 API

---

### 5. 默认命盘功能
**提交**: `06994ea - add default mingpan`

**新增内容**:
- 用户默认命盘保存
- 快速排盘功能

**涉及文件**:
- `app/routers/users.py` - 用户路由扩展

---

### 6. Bug 修复
**提交**:
- `8d4448c - fix bug` (15小时前)
- `120ec86 - fix bugs` (18小时前)
- `97a4b30 - fix bug` (4周前)
- `c64719d - fix knowledge base` (4周前)

---

## 🔧 配置和依赖变更

### 配置文件
- `app/config.py` - 配置项更新
- `.gitignore` - 忽略规则调整

### 主应用
- `main.py` - 路由注册更新（新增 message_rating, user_stats）

### 依赖注入
- `app/deps.py` - 依赖函数更新

---

## 📝 提交历史（最近 → 最早）

```
8d4448c - fix bug (15 hours ago)
141d463 - update (17 hours ago)
120ec86 - fix bugs (18 hours ago)
8048b4d - update (2 days ago)
0864f56 - Merge branch 'develop' (3 days ago)
9a365fb - add message rating feature (3 days ago) ⭐
8077230 - Merge branch 'develop' (3 weeks ago)
70ddc25 - add knowledge base (3 weeks ago) ⭐
1765616 - add logs (4 weeks ago)
debe345 - update (4 weeks ago)
9a00fc1 - update (4 weeks ago)
97a4b30 - fix bug (4 weeks ago)
1c87487 - update (4 weeks ago)
dc79238 - update (4 weeks ago)
b762d56 - add user quota management (4 weeks ago) ⭐
c64719d - fix knowledge base (4 weeks ago)
26d02bb - update (4 weeks ago)
06994ea - add default mingpan (4 weeks ago)
```

---

## ⚠️ 合并前检查清单

### 数据库迁移
- [ ] 确认 `message_ratings` 表已创建
- [ ] 确认 `user_quotas` 表已创建
- [ ] 确认 `usage_logs` 表已创建
- [ ] 执行数据库迁移 SQL（如有）

### 环境变量
- [ ] 检查 `.env` 文件是否需要新增配置项
- [ ] 确认配额相关配置

### 依赖包
- [ ] 检查 `requirements.txt` 是否有更新
- [ ] 确认所有依赖已安装

### 测试
- [ ] 消息评价功能测试
- [ ] 配额系统测试
- [ ] 知识库功能测试
- [ ] 统计 API 测试

### 备份
- [ ] 备份生产数据库
- [ ] 备份当前 main 分支代码

---

## 🚀 合并建议

### 合并步骤

1. **切换到 main 分支**
```bash
git checkout main
git pull origin main
```

2. **合并 develop 分支**
```bash
git merge develop
```

3. **解决冲突（如有）**
```bash
# 查看冲突文件
git status

# 解决冲突后
git add .
git commit -m "Merge develop into main"
```

4. **推送到远程**
```bash
git push origin main
```

### 部署步骤

1. **备份数据库**
```bash
mysqldump -u fate_app -p fate > backup_fate_$(date +%Y%m%d_%H%M%S).sql
```

2. **执行数据库迁移**
```bash
# 如果有 Alembic 迁移
alembic upgrade head

# 或手动执行 SQL
mysql -u fate_app -p fate < migrations/xxx.sql
```

3. **重启服务**
```bash
# 停止服务
systemctl stop fate-api

# 拉取最新代码
git pull origin main

# 安装依赖（如有更新）
pip install -r requirements.txt

# 启动服务
systemctl start fate-api
```

4. **验证功能**
- 访问 API 健康检查端点
- 测试消息评价功能
- 测试配额系统
- 检查日志是否正常

---

## 📌 注意事项

1. **数据库变更**：本次合并包含多个新表，务必先在测试环境验证
2. **配额系统**：新增的配额功能可能影响现有用户，需要初始化配额数据
3. **知识库文档**：新增的 .docx 文件较大，确认是否需要提交到 Git
4. **消息评价**：需要前端配合更新才能完整使用
5. **向后兼容**：所有新功能都是增量添加，不影响现有功能

---

## 🎉 功能亮点

1. **用户反馈闭环**：通过消息评价功能收集用户反馈，持续改进 AI 质量
2. **资源管理**：配额系统帮助控制资源使用，防止滥用
3. **知识增强**：新增知识库文档提升 AI 回复质量
4. **数据洞察**：增强的统计功能帮助了解用户行为和系统使用情况

---

**建议**: 在非高峰时段进行合并和部署，并做好回滚准备。
