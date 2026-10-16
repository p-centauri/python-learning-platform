CREATE TABLE {report}.query_note (
  namespace text COLLATE "C" NOT NULL,
  id text COLLATE "C" NOT NULL,
  revision integer NOT NULL,
  note_id text COLLATE "C" NOT NULL CHECK (note_id ~ '^[a-z][a-z0-9-]{{0,31}}$'),
  body jsonb NOT NULL CHECK (jsonb_typeof(body) = 'object' AND octet_length(body::text) <= 1024),
  PRIMARY KEY(namespace,id,revision,note_id),
  FOREIGN KEY(namespace,id,revision) REFERENCES {source}.feed_record(namespace,id,revision)
)
