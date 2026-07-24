BEGIN TRANSACTION READ ONLY;

WITH case_terms(case_id, term) AS (
  VALUES
    ('BEAUTY-01', '메이크업'),
    ('BEAUTY-01', '립'),
    ('BEAUTY-01', '틴트'),
    ('BEAUTY-01', '젤광'),
    ('PRODUCT-01', '음식물처리기'),
    ('PRODUCT-01', '자취'),
    ('PRODUCT-01', '꿀템'),
    ('IDOL-01', '르세라핌'),
    ('IDOL-01', 'LE SSERAFIM'),
    ('IDOL-01', 'CELEBRATION'),
    ('EXPERT-01', '재테크'),
    ('EXPERT-01', '채권')
),
matched AS (
  SELECT DISTINCT ON (ct.case_id, v.id)
    ct.case_id,
    v.id AS row_id,
    v.platform_video_id,
    v.title,
    v.channel,
    v.keyword,
    v.naver_category,
    v.tags,
    v.discovery_views,
    v.upload_date
  FROM case_terms ct
  JOIN shorts_videos v
    ON lower(concat_ws(' ', v.title, v.description, v.keyword, v.tags::text))
       LIKE '%' || lower(ct.term) || '%'
  WHERE v.discovered_at < TIMESTAMPTZ '2026-07-25 00:00:00+09:00'
    AND (v.upload_date IS NULL OR v.upload_date <= DATE '2026-07-24')
  ORDER BY ct.case_id, v.id, length(ct.term) DESC
),
ranked_snapshots AS (
  SELECT
    s.video_id,
    s.snapshot_date,
    s.view_count,
    s.like_count,
    s.comment_count,
    row_number() OVER (
      PARTITION BY s.video_id ORDER BY s.snapshot_date DESC
    ) AS rn
  FROM shorts_snapshots s
  WHERE s.snapshot_date <= DATE '2026-07-24'
),
latest_snapshot AS (
  SELECT *
  FROM ranked_snapshots
  WHERE rn = 1
),
sentiment AS (
  SELECT
    video_id,
    count(*) FILTER (WHERE label = '긍정')::int AS positive,
    count(*) FILTER (WHERE label = '부정')::int AS negative,
    count(*) FILTER (WHERE label = '중립')::int AS neutral,
    count(*) FILTER (WHERE label IS NOT NULL)::int AS classified
  FROM comment_sentiments
  WHERE EXISTS (
    SELECT 1
    FROM shorts_comments c
    WHERE c.video_id = comment_sentiments.video_id
      AND c.comment_id = comment_sentiments.comment_id
      AND c.snapshot_date <= DATE '2026-07-24'
  )
  GROUP BY video_id
),
market_ranked AS (
  SELECT
    m.*,
    ls.snapshot_date,
    ls.view_count,
    ls.like_count,
    ls.comment_count,
    se.positive,
    se.negative,
    se.neutral,
    se.classified,
    row_number() OVER (
      PARTITION BY m.case_id
      ORDER BY coalesce(ls.view_count, m.discovery_views) DESC NULLS LAST,
               m.platform_video_id
    ) AS case_rank
  FROM matched m
  LEFT JOIN latest_snapshot ls ON ls.video_id = m.row_id
  LEFT JOIN sentiment se ON se.video_id = m.row_id
),
last_three AS (
  SELECT
    video_id,
    max(view_count) FILTER (WHERE rn = 1) AS view_new,
    max(snapshot_date) FILTER (WHERE rn = 1) AS date_new,
    max(view_count) FILTER (WHERE rn = 3) AS view_old,
    max(snapshot_date) FILTER (WHERE rn = 3) AS date_old,
    count(*) FILTER (WHERE rn <= 3) AS snapshot_count
  FROM ranked_snapshots
  WHERE rn <= 3
  GROUP BY video_id
  HAVING count(*) FILTER (WHERE rn <= 3) >= 3
),
growth_base AS (
  SELECT
    v.id AS row_id,
    v.platform_video_id,
    (DATE '2026-07-24' - v.upload_date)::int AS age_days,
    CASE
      WHEN DATE '2026-07-24' - v.upload_date <= 7 THEN '0-7'
      WHEN DATE '2026-07-24' - v.upload_date <= 30 THEN '8-30'
      WHEN DATE '2026-07-24' - v.upload_date <= 90 THEN '31-90'
      WHEN DATE '2026-07-24' - v.upload_date <= 365 THEN '91-365'
      ELSE '365+'
    END AS age_bucket,
    l.date_old,
    l.date_new,
    round(
      (l.view_new - l.view_old)::numeric
      / nullif(l.date_new - l.date_old, 0)
    )::double precision AS daily_view_delta
  FROM last_three l
  JOIN shorts_videos v ON v.id = l.video_id
  WHERE l.view_old IS NOT NULL
    AND v.discovered_at < TIMESTAMPTZ '2026-07-25 00:00:00+09:00'
    AND v.upload_date IS NOT NULL
    AND v.upload_date <= DATE '2026-07-24'
),
growth_scored AS (
  SELECT
    gb.*,
    round(
      percent_rank() OVER (
        PARTITION BY gb.age_bucket ORDER BY gb.daily_view_delta
      ) * 100
    )::int AS percentile,
    count(*) OVER (PARTITION BY gb.age_bucket)::int AS peer_sample_size
  FROM growth_base gb
  WHERE gb.daily_view_delta IS NOT NULL
),
growth_ranked AS (
  SELECT
    m.case_id,
    m.row_id,
    m.platform_video_id,
    m.keyword,
    m.naver_category,
    gs.date_old,
    gs.date_new,
    gs.daily_view_delta,
    gs.age_days,
    gs.age_bucket,
    gs.percentile,
    gs.peer_sample_size,
    row_number() OVER (
      PARTITION BY m.case_id
      ORDER BY gs.percentile DESC, gs.daily_view_delta DESC,
               m.platform_video_id
    ) AS case_rank
  FROM matched m
  JOIN growth_scored gs ON gs.row_id = m.row_id
)
SELECT jsonb_build_object(
  'market',
  coalesce((
    SELECT jsonb_agg(jsonb_build_object(
      'caseId', mr.case_id,
      'rowId', mr.row_id,
      'platformVideoId', mr.platform_video_id,
      'title', mr.title,
      'channel', mr.channel,
      'keyword', mr.keyword,
      'category', mr.naver_category,
      'tags', coalesce(mr.tags, '[]'::jsonb),
      'snapshotDate', mr.snapshot_date,
      'views', coalesce(mr.view_count, mr.discovery_views),
      'viewsSource', CASE WHEN mr.view_count IS NULL THEN 'discovery' ELSE 'snapshot' END,
      'likes', mr.like_count,
      'comments', mr.comment_count,
      'positive', coalesce(mr.positive, 0),
      'negative', coalesce(mr.negative, 0),
      'neutral', coalesce(mr.neutral, 0),
      'classified', coalesce(mr.classified, 0)
    ) ORDER BY mr.case_id, mr.case_rank)
    FROM market_ranked mr
    WHERE mr.case_rank <= 3
  ), '[]'::jsonb),
  'growth',
  coalesce((
    SELECT jsonb_agg(jsonb_build_object(
      'caseId', gr.case_id,
      'rowId', gr.row_id,
      'platformVideoId', gr.platform_video_id,
      'keyword', gr.keyword,
      'category', gr.naver_category,
      'snapshotFrom', gr.date_old,
      'snapshotTo', gr.date_new,
      'snapshotCount', 3,
      'dailyViewDelta', gr.daily_view_delta,
      'ageDays', gr.age_days,
      'ageBucket', gr.age_bucket,
      'percentile', gr.percentile,
      'peerSampleSize', gr.peer_sample_size,
      'risingThreshold', 90,
      'isRising', gr.percentile >= 90,
      'isNewRising', gr.percentile >= 90 AND gr.age_days <= 7
    ) ORDER BY gr.case_id, gr.case_rank)
    FROM growth_ranked gr
    WHERE gr.case_rank <= 2
  ), '[]'::jsonb)
);

ROLLBACK;
