-- Career task progress records.
-- Execute this SQL on the production MySQL database before deploying the backend route.

CREATE TABLE IF NOT EXISTS `career_progress` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT 'Owner user id',
  `task_id` VARCHAR(128) NULL COMMENT 'Stable career task identifier from frontend task context',
  `task_context` JSON NOT NULL COMMENT 'Career task snapshot, including mode, title, progress, and review reminder',
  `content` TEXT NULL COMMENT 'Progress note content; null when the row only updates review reminder',
  `review_due_at` DATETIME NULL COMMENT 'Optional review reminder time',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  KEY `idx_career_progress_user_updated` (`user_id`, `updated_at`),
  KEY `idx_career_progress_user_task` (`user_id`, `task_id`),
  CONSTRAINT `fk_career_progress_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
