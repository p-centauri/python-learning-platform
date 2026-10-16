## Validation has layers
A Pydantic request model can enforce types, lengths and local shape. It cannot establish that an account belongs to the current tenant or that a balance is still available when another transaction runs. Those checks belong in application logic and database invariants. Keep the route responsible for transport concerns: parse input, resolve identity, call a use case and translate its outcome.

```python
class TransferRequest(BaseModel):
    destination_id: int
    amount_minor: int = Field(gt=0)

@router.post('/transfers')
def transfer(body: TransferRequest,
             user: User = Depends(current_user),
             session: Session = Depends(get_session)):
    return transfer_service.execute(session, user, body)
```
This sketch deliberately uses a synchronous endpoint with a synchronous database session. Putting a blocking SQL driver inside `async def` does not make it nonblocking; it blocks the event loop. Use synchronous routes for synchronous stacks or consistently use async drivers and awaitable APIs.

## Transaction ownership
Choose the application use case as the unit of work. Helpers may query and flush, but should not independently commit partial work. An endpoint that reserves inventory, creates an order and records an outbox event needs one success/failure boundary. A repository that commits secretly makes that guarantee difficult to inspect.

Dependencies are useful for providing sessions and identity, not an excuse to distribute business decisions across a chain of invisible side effects. Return a response model instead of exposing ORM objects wholesale; sensitive columns and lazy relationships should not leak through serialization.

## Background work and production
In-process background tasks disappear with the process. They fit disposable work, not guaranteed billing, ingestion or reconciliation. Durable jobs need durable intent and idempotent workers. Translate expected domain conflicts into deliberate HTTP errors; unexpected failures should preserve diagnostic context in structured logs without returning secrets.

## Review exercise
Find a route that validates a tenant ID supplied by the request, commits inside two repositories and calls a synchronous HTTP library in an async function. Repair the authorization source, transaction boundary and scheduling behavior independently. Mastery means explaining why each fix addresses a different class of failure rather than declaring the endpoint clean because it is short.
