-- Provision in a fresh schema in a disposable PostgreSQL 17 database.
CREATE TABLE feed_source (
    namespace text PRIMARY KEY,
    CONSTRAINT source_namespace CHECK (namespace COLLATE "C" ~ '^[a-z][a-z0-9-]{0,31}$')
);
CREATE TABLE feed_record (
    namespace text NOT NULL REFERENCES feed_source(namespace),
    id text NOT NULL,
    revision integer NOT NULL,
    value integer NOT NULL,
    PRIMARY KEY (namespace, id, revision),
    CONSTRAINT record_id CHECK (id COLLATE "C" ~ '^[a-z][a-z0-9-]{0,31}$'),
    CONSTRAINT record_revision CHECK (revision BETWEEN 1 AND 8),
    CONSTRAINT record_value CHECK (value BETWEEN 0 AND 1000000)
);
