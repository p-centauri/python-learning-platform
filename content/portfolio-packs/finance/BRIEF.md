# Build contract

## Ledger and domain

Model owned accounts, currency, categories, expenses/income, budgets, recurring schedules/occurrences, immutable audit records, action approvals and operation receipts. Use exact amounts and explicit currency; define conversion policy and never sum unlike currencies. No LLM or client role field owns ledger authority. Corrections/compensation retain an audit trail rather than erasing history.

## Business API

Authenticated POST /expenses accepts {key,cents,currency,category,date}; validates actor ownership, positive exact integer cents, allowed currency/category and unambiguous date. First returns 201 plus durable receipt; same scoped key/body returns 200 same receipt; changed body returns 409. GET /reports/monthly derives owner, bounds interval, groups exact income/expense/budget by currency and exposes only that actor. Implement income, categories, budgets and recurring occurrences with stable occurrence keys.

## AI orchestration and tools

Separate user intent/transcript, model proposal, strict schema, current permissions, action-bound approval and application execution. Only allowlisted domain tools exist. Approval binds actor, exact canonical arguments, expiry and operation identity; changed amounts/owners require fresh approval. Commit ledger and receipt together. A provider timeout after commit recovers the receipt; it cannot imply rollback. No model SQL or arbitrary URL/file tool.

## Languages and clarification

Support Uzbek, Russian and English display/query/action flows. The pack contains 24 synthetic examples (eight per language), including ambiguous dates/currency, refusals and mutation proposals. Human speakers must review translations/intent and locale formats. Dates such as 03/04 need clarification under an ambiguous locale. “100” without an agreed currency is not permission to guess. Translation quality is separate from authorization.

## Analytics and reports

Provide exact currency-scoped totals, category breakdown, budget warnings and recurring forecasts with provenance/date boundaries. Natural-language queries compile to a validated bounded domain query, not model-generated arbitrary SQL. AI insights cite report facts and separate suggestions from financial advice. RAG may support documented product policies; it is not authority to change balances.

## Voice-ready boundary

Specify transcript/provider metadata, locale, confidence/ambiguity, session/action identity and confirmation. A transcript alone is neither authenticated intent nor approval. Keep proposal/confirmation/execution separate so a future mobile/voice client can use the same contracts. Do not claim voice support from a text-only boundary.

## Failure matrix and operations

Required: owner collision; negative/bool/overprecision amount; unlike currencies; ambiguous dates; duplicate orchestration; changed approval; expired approval; duplicate recurring occurrence; provider outage/refusal; tool committed before answer timeout; malicious tool role; private trace leak; reports around timezone boundaries; migration/restore; budget cutoff. Measure language/intent/action outcomes separately, latency/cost/provider versions and human quality judgments. Ship CI, non-root deployment, bounded provider calls, redacted logs, backups and restore evidence.

## Final review packet

Use ledger, tools, languages and operations criteria. Supply exact revision, migrations/invariants, public API examples, approval/deduplication/crash tests, reports, 24 seed cases plus independent multilingual labels, actual provider or clearly marked controlled-fixture outcomes, cost/latency observations, voice contract and a human-reviewed release decision. No fake financial/provider/voice readiness from a checklist.

## Libraries and abilities

- FastAPI/Pydantic: trusted business API and strict tool proposal schemas
- PostgreSQL/SQLAlchemy/Alembic: exact ledger values, constraints and durable receipts
- Decimal or integer minor units plus explicit currency: exact financial arithmetic
- Date/time and zoneinfo: recurring entries, ambiguous local dates and explicit timezones
- Provider adapter and validated tools: action approval, reconciliation and refusal
- pytest/HTTPX, localization and evaluation harness: Uzbek/Russian/English workflows, redaction and metrics

## Official references

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy session ownership](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
