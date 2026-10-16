SELECT id, revision, note_id FROM query_note
WHERE namespace = :namespace AND body @> CAST(:filter AS jsonb)
ORDER BY id, revision, note_id LIMIT :limit
