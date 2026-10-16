The sender may lose a response after the receiver commits. It cannot tell whether the operation happened just by seeing a timeout. Sending the event again is normal. A stable delivery ID lets the receiver reconcile the retry. This lab's receipt key is namespace plus delivery ID. Different namespaces have independent identities. A receipt stores the SHA-256 digest of the authenticated raw body. The signing timestamp is excluded from that stored digest so a fresh signature can retry the same delivery.

Store the receipt and the reading in one PostgreSQL transaction. Insert the receipt with ON CONFLICT DO NOTHING RETURNING. If the identity already exists, read its committed digest. The same digest is a duplicate and returns success without another effect. A different digest is a 409 delivery conflict, even if the changed whitespace produces equal JSON. Stable retry bytes are part of this protocol. Do not silently replace the first receipt.

For a new delivery, insert the source and reading under their original full namespace/id/revision key. An existing equal reading is allowed: another delivery can refer to the same reading without creating another fact. An existing different value is a reading conflict. Raising that conflict rolls the new receipt back too. The sender can correct the event and retry that delivery ID because the failed transaction did not reserve it. A zero returned value still means a successful insert; compare with None, not truthiness.

Two processes can receive the same delivery simultaneously. PostgreSQL's unique key makes one insert wait for the other transaction's outcome. A process dictionary cannot coordinate them. The lab applies individual lock and statement limits; a real blocked receipt returns generic 503, and released connections permit a later retry. Send 200 only after the transaction commits. These guarantees cover the local reading and receipt, not exactly-once email, billing, Redis or another service. The unchanged HTTP ingestion route still does not automatically create an outbox event.

## Guided practice

Predict the printed value before running this small illustration. Then explain which part requires a real request or database observation.

```python
receipts: dict[tuple[str, str], str] = {}
identity = ("north", "delivery-a")
receipts[identity] = "body-hash"
print(receipts.get(identity) == "body-hash")
```

## Independent practice

Implement accept. Rehearse simultaneous duplicates, equal readings under two delivery IDs, a changed body under one ID, and a reading conflict that leaves no receipt. Add a full-key cross-namespace case of your own.

## Check your work

Submit actual receipt/fact counts and pool cleanup. This small dictionary example explains lookup only; actual multi-connection PostgreSQL tests evaluate atomicity and waiting.

Continue with the [API depth lab](/projects#python-api-depth). Record commands and outcomes; keep private credentials out of submitted evidence.
