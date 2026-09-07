-- Configure the uploaded Tencent Cloud VOD video for a member-only lesson.
-- Replace the course fields if you already have a target course/lesson.

SET @course_slug = 'member-vod-course';
SET @lesson_slug = 'vod-5001834812993268502';

INSERT INTO video_courses (
    slug,
    title,
    subtitle,
    description,
    sort_order,
    is_active
)
VALUES (
    @course_slug,
    'Member Video Course',
    'Member-only content',
    'Tencent Cloud VOD member video course.',
    10,
    TRUE
)
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    subtitle = VALUES(subtitle),
    description = VALUES(description),
    is_active = TRUE;

SET @course_id = (
    SELECT id
    FROM video_courses
    WHERE slug = @course_slug
    LIMIT 1
);

INSERT INTO video_lessons (
    course_id,
    slug,
    title,
    description,
    duration_seconds,
    sort_order,
    access_level,
    provider,
    provider_video_id,
    source_url,
    is_active
)
VALUES (
    @course_id,
    @lesson_slug,
    'Five Elements Intro',
    'Member-only VOD video.',
    NULL,
    10,
    'member',
    'vod',
    '5001834812993268502',
    NULL,
    TRUE
)
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    description = VALUES(description),
    access_level = 'member',
    provider = 'vod',
    provider_video_id = '5001834812993268502',
    source_url = NULL,
    is_active = TRUE;
