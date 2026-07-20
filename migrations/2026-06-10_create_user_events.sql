-- Minimal user behavior events for retention analysis.
-- Execute this SQL before deploying the backend events route.

CREATE TABLE IF NOT EXISTS `user_events` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `user_id` BIGINT UNSIGNED NULL COMMENT 'Logged-in user id; null for anonymous events',
  `event_name` VARCHAR(80) NOT NULL COMMENT 'Event name, for example dashboard_view',
  `event_source` VARCHAR(40) NULL COMMENT 'Client source, for example web',
  `page_path` VARCHAR(255) NULL COMMENT 'Current page path',
  `payload` JSON NULL COMMENT 'Small structured event payload',
  `session_id` VARCHAR(80) NULL COMMENT 'Client session id',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  PRIMARY KEY (`id`),
  KEY `idx_user_events_user_created` (`user_id`, `created_at`),
  KEY `idx_user_events_name_created` (`event_name`, `created_at`),
  KEY `idx_user_events_session` (`session_id`),
  CONSTRAINT `fk_user_events_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

