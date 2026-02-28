# Password Reset 功能数据库迁移

## 功能分支

`feature/password-reset`

## 需要执行的 SQL

### 创建 password_reset_codes 表

```sql
CREATE TABLE IF NOT EXISTS `password_reset_codes` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID（自增）',
    `email` VARCHAR(254) NOT NULL COMMENT '用户邮箱',
    `code` VARCHAR(6) NOT NULL COMMENT '6位数字验证码',
    `is_used` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已使用',
    `failed_attempts` SMALLINT NOT NULL DEFAULT 0 COMMENT '验证失败次数',
    `expires_at` DATETIME NOT NULL COMMENT '过期时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `ip_address` VARCHAR(45) NULL COMMENT '请求IP地址',
    PRIMARY KEY (`id`),
    INDEX `ix_password_reset_codes_email` (`email`),
    INDEX `ix_password_reset_codes_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='密码重置验证码表';
```

## 回滚 SQL（如需撤销）

```sql
DROP TABLE IF EXISTS `password_reset_codes`;
```

## 执行方式

### 方式一：使用 init_db.py（推荐）

```bash
cd fate
source venv/bin/activate
python init_db.py
```

### 方式二：手动执行 SQL

```bash
mysql -u fate_app -p fate_dev < migration.sql
```

或登录 MySQL 后执行：

```bash
mysql -u fate_app -p
USE fate_dev;
-- 粘贴上面的 CREATE TABLE 语句
```

## 验证

```sql
-- 检查表是否创建成功
SHOW TABLES LIKE 'password_reset_codes';

-- 查看表结构
DESCRIBE password_reset_codes;

-- 查看索引
SHOW INDEX FROM password_reset_codes;
```
