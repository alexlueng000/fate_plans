-- Guest Liuyao one-time trial records.
-- Allows anonymous visitors to cast one hexagram and receive one AI interpretation before login.

CREATE TABLE IF NOT EXISTS `guest_liuyao` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `public_id` VARCHAR(36) NOT NULL,
  `guest_session_id` VARCHAR(64) NOT NULL,
  `user_id` BIGINT UNSIGNED NULL,
  `status` ENUM('running', 'succeeded', 'failed', 'expired') NOT NULL DEFAULT 'running',
  `error_message` TEXT NULL,
  `question` TEXT NOT NULL,
  `gender` ENUM('male', 'female', 'unknown') NOT NULL DEFAULT 'unknown',
  `method` ENUM('number', 'coin', 'time') NOT NULL,
  `numbers` JSON NULL,
  `timestamp` DATETIME NOT NULL,
  `location` VARCHAR(50) NOT NULL DEFAULT 'beijing',
  `solar_time` TINYINT(1) NOT NULL DEFAULT 1,
  `hexagram_result` JSON NULL,
  `analysis_markdown` MEDIUMTEXT NULL,
  `prompt_version` VARCHAR(64) NULL,
  `request_ip` VARCHAR(45) NULL,
  `user_agent` VARCHAR(512) NULL,
  `bound_at` DATETIME NULL,
  `expires_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_guest_liuyao_public_id` (`public_id`),
  KEY `idx_guest_liuyao_session_created` (`guest_session_id`, `created_at`),
  KEY `idx_guest_liuyao_user_created` (`user_id`, `created_at`),
  KEY `idx_guest_liuyao_status_created` (`status`, `created_at`),
  KEY `idx_guest_liuyao_expires_at` (`expires_at`),
  KEY `idx_guest_liuyao_request_ip_created` (`request_ip`, `created_at`),
  CONSTRAINT `fk_guest_liuyao_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
