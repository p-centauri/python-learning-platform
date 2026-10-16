WITH newest AS (
  SELECT namespace, id, revision, value,
         row_number() OVER (PARTITION BY namespace, id ORDER BY revision DESC) AS position
  FROM feed_record WHERE namespace = :namespace
)
SELECT n.id, n.revision, n.value FROM newest n
WHERE n.position = 1 AND EXISTS (
  SELECT 1 FROM query_note q
  WHERE q.namespace = n.namespace AND q.id = n.id AND q.revision = n.revision
    AND q.body @> CAST(:filter AS jsonb)
)
ORDER BY n.value DESC, n.id, n.revision LIMIT :limit
