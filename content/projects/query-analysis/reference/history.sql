WITH history AS (
  SELECT revision, value,
         lag(value) OVER (ORDER BY revision) AS previous,
         sum(value) OVER (ORDER BY revision ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
         row_number() OVER (ORDER BY revision DESC) = 1 AS latest
  FROM feed_record WHERE namespace = :namespace AND id = :id
)
SELECT revision, value, previous, value - previous AS delta, running_total, latest
FROM history ORDER BY revision LIMIT :limit
