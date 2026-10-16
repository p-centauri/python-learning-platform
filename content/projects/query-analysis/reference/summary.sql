WITH notes AS (
  SELECT namespace, id, revision, count(*) AS notes
  FROM query_note WHERE namespace = :namespace
  GROUP BY namespace, id, revision
)
SELECT s.namespace, count(r.id) AS records, coalesce(sum(r.value), 0) AS total,
       coalesce(sum(CASE WHEN n.notes > 0 THEN 1 ELSE 0 END), 0) AS noted_records
FROM feed_source s
LEFT JOIN feed_record r ON r.namespace = s.namespace
LEFT JOIN notes n ON n.namespace = r.namespace AND n.id = r.id AND n.revision = r.revision
WHERE s.namespace = :namespace
GROUP BY s.namespace
