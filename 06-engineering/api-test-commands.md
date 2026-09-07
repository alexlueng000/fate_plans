# API 测试命令

## 测试聊天启动接口

用于测试 `/api/chat/start` 接口是否正常工作。

### 基础测试请求

```bash
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{
    "paipan": {
      "gender": "男",
      "four_pillars": {
        "year": ["甲", "子"],
        "month": ["乙", "丑"],
        "day": ["丙", "寅"],
        "hour": ["丁", "卯"]
      },
      "dayun": []
    }
  }'
```

### 完整测试请求（包含大运）

```bash
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{
    "paipan": {
      "gender": "男",
      "four_pillars": {
        "year": ["甲", "子"],
        "month": ["乙", "丑"],
        "day": ["丙", "寅"],
        "hour": ["丁", "卯"]
      },
      "dayun": [
        {"age": 5, "start_year": 2020, "pillar": ["丙", "寅"]},
        {"age": 15, "start_year": 2030, "pillar": ["丁", "卯"]}
      ]
    }
  }'
```

### 测试流式响应

```bash
curl -X POST "http://localhost:8000/api/chat/start?stream=true" \
  -H "Content-Type: application/json" \
  -d '{
    "paipan": {
      "gender": "男",
      "four_pillars": {
        "year": ["甲", "子"],
        "month": ["乙", "丑"],
        "day": ["丙", "寅"],
        "hour": ["丁", "卯"]
      },
      "dayun": []
    }
  }'
```

### 带认证的请求

```bash
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "paipan": {
      "gender": "男",
      "four_pillars": {
        "year": ["甲", "子"],
        "month": ["乙", "丑"],
        "day": ["丙", "寅"],
        "hour": ["丁", "卯"]
      },
      "dayun": []
    }
  }'
```

## 其他测试接口

### 测试健康检查

```bash
curl http://localhost:8000/
```

### 测试八字计算

```bash
curl -X POST http://localhost:8000/api/bazi/calc_paipan \
  -H "Content-Type: application/json" \
  -d '{
    "calendar": "公历",
    "gender": "男",
    "birth_date": "1990-01-01",
    "birth_time": "12:00",
    "birthplace": "北京市"
  }'
```

## 故障排查

如果请求失败，检查：

1. **后端是否运行**：`ps aux | grep uvicorn`
2. **端口是否监听**：`netstat -tlnp | grep 8000`
3. **数据库连接**：检查 `.env` 中的 `DATABASE_URL`
4. **日志输出**：查看后端终端的错误信息
5. **内存使用**：`free -h`
