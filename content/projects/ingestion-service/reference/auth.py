from collections.abc import Mapping
from hmac import compare_digest
import re
from .contracts import AuthenticationRequired, PermissionDenied, field


def authorize(tokens: Mapping[str, str], authorization: str | None, namespace: str, /) -> str:
    if type(authorization) is not str:
        raise AuthenticationRequired()
    scheme, separator, token = authorization.partition(" ")
    if (
        separator != " "
        or scheme.casefold() != "bearer"
        or re.fullmatch(r"[A-Za-z0-9_-]{16,64}", token) is None
    ):
        raise AuthenticationRequired()
    principal: str | None = None
    for configured, scope in tokens.items():
        if compare_digest(token, configured):
            principal = scope
    if principal is None:
        raise AuthenticationRequired()
    field(namespace)
    if namespace != principal:
        raise PermissionDenied()
    return principal
