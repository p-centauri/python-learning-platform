SELECT id, revision, value FROM feed_record
WHERE namespace = :namespace AND value BETWEEN :minimum AND :maximum
ORDER BY value, id, revision LIMIT :limit
