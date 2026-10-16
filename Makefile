PYTHON ?= .venv/bin/python

.PHONY: setup dev test typecheck build up down lint format seed migrate runner-setup runner verify-runner verify-ingestion verify-feed-policy verify-async-feeds verify-feed-objects verify-typed-transforms verify-resource-scopes verify-bounded-offload verify-measured-cache verify-ingestion-persistence verify-ingestion-service verify-competing-ingestion verify-durable-outbox verify-leased-worker verify-stream-delivery verify-delivery-schema verify-delivery-recovery verify-api-depth verify-practical-review verify-model-contracts verify-retrieval verify-rag verify-tools verify-ai-evaluation audit-learning-paths verify-backups
setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
	cd apps/web && npm ci
dev:
	bash scripts/dev.sh
test:
	cd apps/api && ../../$(PYTHON) -m unittest discover -s tests -v
typecheck:
	cd apps/web && npm run typecheck
build:
	cd apps/web && npm run build
up:
	docker compose up --build
down:
	docker compose down
lint:
	$(PYTHON) -m ruff check apps/api apps/runner apps/web/tests/fixtures scripts/setup_runner.py scripts/verify_ingestion_package.py scripts/verify_feed_policy.py scripts/verify_async_feeds.py scripts/verify_feed_objects.py scripts/verify_typed_transforms.py scripts/verify_resource_scopes.py scripts/verify_bounded_offload.py scripts/verify_measured_cache.py scripts/verify_ingestion_persistence.py scripts/persistence_db.py scripts/verify_ingestion_service.py scripts/verify_competing_ingestion.py scripts/verify_durable_outbox.py scripts/verify_leased_worker.py scripts/verify_stream_delivery.py scripts/stream_broker.py scripts/verify_delivery_schema.py scripts/verify_delivery_recovery.py scripts/verify_delivery_release.py scripts/verify_query_analysis.py scripts/verify_api_depth.py scripts/verify_practical_review.py scripts/verify_model_contracts.py scripts/verify_retrieval.py scripts/verify_rag.py scripts/verify_tools.py scripts/verify_ai_evaluation.py scripts/verify_comprehensive.py scripts/audit_learning_paths.py scripts/academy_backup.py scripts/configure_compose_runner.py scripts/tests
	cd apps/web && npm run typecheck
format:
	$(PYTHON) -m ruff format apps/api apps/runner
	cd apps/web && npm run format
seed:
	cd apps/api && ../../$(PYTHON) -m app.seed
migrate:
	cd apps/api && ../../$(PYTHON) -m alembic upgrade head
runner-setup:
	docker pull python@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26
	docker pull postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24
	$(PYTHON) scripts/setup_runner.py
runner:
	bash scripts/runner.sh
verify-runner:
	PYTHONPATH=apps/runner $(PYTHON) -m unittest discover -s apps/runner/tests -v
verify-ingestion:
	$(PYTHON) scripts/verify_ingestion_package.py

verify-feed-policy:
	$(PYTHON) scripts/verify_feed_policy.py

verify-async-feeds:
	$(PYTHON) scripts/verify_async_feeds.py

verify-feed-objects:
	$(PYTHON) scripts/verify_feed_objects.py

verify-typed-transforms:
	$(PYTHON) scripts/verify_typed_transforms.py

verify-resource-scopes:
	$(PYTHON) scripts/verify_resource_scopes.py

verify-bounded-offload:
	$(PYTHON) scripts/verify_bounded_offload.py

verify-measured-cache:
	$(PYTHON) scripts/verify_measured_cache.py

verify-ingestion-persistence:
	$(PYTHON) scripts/verify_ingestion_persistence.py

verify-ingestion-service:
	$(PYTHON) scripts/verify_ingestion_service.py

verify-competing-ingestion:
	$(PYTHON) scripts/verify_competing_ingestion.py

verify-durable-outbox:
	$(PYTHON) scripts/verify_durable_outbox.py

verify-leased-worker:
	$(PYTHON) scripts/verify_leased_worker.py

verify-stream-delivery:
	$(PYTHON) scripts/verify_stream_delivery.py

verify-delivery-schema:
	$(PYTHON) scripts/verify_delivery_schema.py

verify-delivery-recovery:
	$(PYTHON) scripts/verify_delivery_recovery.py

verify-delivery-release:
	$(PYTHON) scripts/verify_delivery_release.py

verify-query-analysis:
	$(PYTHON) scripts/verify_query_analysis.py

verify-api-depth:
	$(PYTHON) scripts/verify_api_depth.py

verify-practical-review:
	$(PYTHON) scripts/verify_practical_review.py

verify-model-contracts:
	$(PYTHON) scripts/verify_model_contracts.py

verify-retrieval:
	$(PYTHON) scripts/verify_retrieval.py

verify-rag:
	$(PYTHON) scripts/verify_rag.py

verify-tools:
	$(PYTHON) scripts/verify_tools.py

verify-ai-evaluation:
	$(PYTHON) scripts/verify_ai_evaluation.py

audit-learning-paths:
	$(PYTHON) scripts/audit_learning_paths.py

verify-comprehensive:
	$(PYTHON) scripts/verify_comprehensive.py

verify-backups:
	$(PYTHON) -m unittest discover -s scripts/tests -v
