"""Intentional learner implementation boundary, not a finished service."""
def create_app():
    """Return a FastAPI application using independently configured PostgreSQL storage.

    In synthetic public tests, use fixture tokens alpha-token and beta-token,
    fixture SKU book (stock=1, unit price 100 cents), and the declared fixture corpus.
    Keep fixture provisioning separate from production authentication/data.
    """
    raise NotImplementedError("Build the portfolio service from BRIEF.md")
