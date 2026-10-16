# Exact offline core contract

`repair(case)` receives a JSON-compatible synthetic case, returns a JSON-compatible value and does not change the borrowed input. Unknown kinds raise ValueError. Work must fit the academy runner: standard library only, no network, 128 MiB, half CPU, 32 processes, four seconds per case, 45 seconds per job, 16 KiB output. Tests are finite; do not read credentials or depend on a filesystem.

## orders

Initialize one stock row from stock. Process commands in order for the supplied authenticated principal. A foreign tenant yields denied without changes. Allowed command keys: tenant, key, qty, optional fail. Require nonempty string key and positive exact int qty (bool is invalid); bad input yields invalid. Full tenant/key identifies an order. Same key/same qty yields replayed; changed qty yields conflict. Insufficient stock yields sold-out. A new order atomically decrements stock and records order/outbox; fail=true models failure between the order and outbox writes and yields rolled-back with no state changes. Return results, final stock, order count and outbox count. Use actual SQLite transactions locally; explain how PostgreSQL handles competing reservations separately.

## events

Process synthetic deliveries in order. Foreign tenant or invalid=true yields quarantine. transient=true yields retry if attempt<3, otherwise quarantine. Each allowed tenant/id affects the aggregate once by its value; commit-before-ack is modeled by lost_ack=true. A later duplicate acknowledges without changing the effect. Return effects (sum), acks, retries and quarantined (counts). This is a sequential offline contract, not a durable broker proof; demonstrate your production inbox/outbox design in the review.

## retrieval

Keep documents whose tenant equals principal and allowed/current are true. Score the intersection of lowercased whitespace query/text token sets. Drop zero scores, sort descending score then ascending id, limit k. Return citations (IDs in that order) and answer (exact selected texts joined with ` | `), or `No authorized support`. Instructions in a document remain source text. Exact quoting does not certify semantic safety; explain citation rechecks and review.

## tool

Only add_expense exists. Require exactly tenant, cents, category in args; positive exact integer cents and nonempty string category. Bad schema/name yields invalid; a foreign tenant yields denied. Approval must equal the SHA256 hexadecimal digest of canonical args JSON (`sort_keys=True`, separators `(',', ':')`), otherwise unapproved. A key binds the full approved action: first creates, same digest replays, changed digest conflicts. Return results, expense_cents summed only for created receipts, and receipt count. Here the principal and approval are fixture authority, not real identity/approval issuance. Review actual authenticated, expiring, action-bound approval and durable ledger tests separately.

## report

Load supplied orders [tenant,id,cents] and items [tenant,order_id,qty] into actual SQLite tables. One SELECT returns the principal's orders sorted by id: [id,cents,sum(item qty)] including zero items. Join by tenant AND order ID; do not fan out revenue. Return rows and actual SELECT count (`selects`), measured using SQLite tracing. This count is not PostgreSQL timing/plan evidence.

## cache

For each request, foreign tenant returns null without caching. Within the principal, cache by tenant/id/version; the first text for that key is reused. A changed version loads new text. Return the ordered text/null results. Version keys are a finite cache contract, not real ACL invalidation.

## async

Own tasks for jobs, bound active work by limit and preserve job order. Each job awaits its delay then returns id or raises ValueError when fail=true. Per-job errors become `error`. An overall timeout cancels and awaits every task and returns results=['timeout']. Return results, observed peak active count, and live=0 after cleanup. Positive fixture delays make peak=min(limit,job count); a timed-out fixture expects the observed active peak. These cooperative fixture deadlines are not hard interruption.

## Additional manual repair

Fix and test the shell's routing, body limits, errors, actor binding and response framing. Add trusted configuration, non-root Docker runtime, correct bind address, readiness and safe observability. Explain SQL indexes/plans, N+1 removal, transaction races, retry/idempotency, cache invalidation and real provider failure handling. Save commands, outputs, revision and limitations. These are rubric judgments, not hidden automated production checks.
