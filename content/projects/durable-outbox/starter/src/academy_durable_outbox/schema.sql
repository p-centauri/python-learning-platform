-- Explicit one-time addition after the prior service_002 migration in a disposable schema.
CREATE TABLE delivery_outbox (
 namespace text COLLATE "C" NOT NULL,
 id text COLLATE "C" NOT NULL,
 revision integer NOT NULL,
 value integer NOT NULL CHECK (value BETWEEN 0 AND 1000000),
 acknowledged boolean NOT NULL DEFAULT false,
 PRIMARY KEY (namespace,id,revision),
 FOREIGN KEY (namespace,id,revision) REFERENCES feed_record(namespace,id,revision)
);
CREATE TABLE delivery_inbox (
 namespace text COLLATE "C" NOT NULL CHECK (namespace ~ '^[a-z][a-z0-9-]{0,31}$'),
 id text COLLATE "C" NOT NULL CHECK (id ~ '^[a-z][a-z0-9-]{0,31}$'),
 revision integer NOT NULL CHECK (revision BETWEEN 1 AND 8),
 value integer NOT NULL CHECK (value BETWEEN 0 AND 1000000),
 PRIMARY KEY (namespace,id,revision)
);
CREATE TABLE delivery_effect (
 namespace text COLLATE "C" PRIMARY KEY CHECK (namespace ~ '^[a-z][a-z0-9-]{0,31}$'),
 total bigint NOT NULL CHECK (total >= 0),
 applied bigint NOT NULL CHECK (applied > 0)
);
