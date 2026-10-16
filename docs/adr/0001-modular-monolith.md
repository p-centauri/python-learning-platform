# ADR 0001 — modular monolith
Status: accepted. Date: 2026-09-14.

Use FastAPI + SQLAlchemy with feature routers and small domain services. A separate Next.js app owns UI. A single learner product does not justify service-to-service failure modes. Extract an isolated execution runner later because it has a distinct trust boundary, not to imitate a microservice architecture.
