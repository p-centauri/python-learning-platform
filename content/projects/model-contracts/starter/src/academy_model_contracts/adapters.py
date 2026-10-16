from .contracts import Dialect, Request, Transport, identifier


class Adapter:
    """Borrow a configured async transport; the caller owns its lifetime. No SDK/network/credentials."""

    def __init__(self, provider_id: str, dialect: Dialect, transport: Transport) -> None:
        self._provider_id = identifier(provider_id)
        if dialect not in ("message-v1", "completion-v1"):
            raise ValueError("unsupported adapter dialect")
        self._dialect = dialect
        self._transport = transport

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def dialect(self) -> Dialect:
        return self._dialect

    async def complete(self, request: Request) -> object:
        if request.config.provider_id != self.provider_id or request.config.dialect != self.dialect:
            raise ValueError("configured provider mismatch")
        return await self._transport.send(request.body)
