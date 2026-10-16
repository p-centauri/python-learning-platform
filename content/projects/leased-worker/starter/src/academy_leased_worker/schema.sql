CREATE TABLE worker_policy (
 namespace text COLLATE "C" PRIMARY KEY REFERENCES feed_source(namespace),
 lease_ms integer NOT NULL CHECK (lease_ms BETWEEN 100 AND 60000),
 max_attempts integer NOT NULL CHECK (max_attempts BETWEEN 1 AND 8),
 delays_ms integer[] NOT NULL CHECK (cardinality(delays_ms) = max_attempts - 1)
   CHECK (0 <= ALL(delays_ms) AND 60000 >= ALL(delays_ms))
);
CREATE TABLE delivery_job (
 namespace text COLLATE "C" NOT NULL REFERENCES worker_policy(namespace),
 id text COLLATE "C" NOT NULL,
 revision integer NOT NULL,
 generation bigint NOT NULL DEFAULT 0 CHECK (generation BETWEEN 0 AND 8),
 state text NOT NULL DEFAULT 'ready' CHECK (state IN ('ready','leased','done','dead')),
 next_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 lease_until timestamptz,
 reason text CHECK (reason IN ('retry','poison','exhausted')),
 PRIMARY KEY(namespace,id,revision),
 FOREIGN KEY(namespace,id,revision) REFERENCES delivery_outbox(namespace,id,revision),
 CHECK ((state = 'leased') = (lease_until IS NOT NULL)),
 CHECK (state <> 'leased' OR generation > 0)
);
CREATE INDEX delivery_job_ready ON delivery_job(namespace,next_at,id,revision) WHERE state='ready';
