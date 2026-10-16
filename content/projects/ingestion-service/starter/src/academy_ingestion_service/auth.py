from collections.abc import Mapping


def authorize(tokens: Mapping[str, str], authorization: str | None, namespace: str, /) -> str:
    """Authenticate a configured bearer, validate scope, then authorize exact namespace."""
    raise NotImplementedError("implement credential and namespace permission boundary")
