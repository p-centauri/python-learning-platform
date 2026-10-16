A webhook is an HTTP request sent by another system when something happens. Receiving a request does not prove who sent it. A shared secret can authenticate the message with an HMAC, a keyed digest. The sender and receiver compute the same digest from the same bytes and secret. The receiver compares the fixed-format digest with hmac.compare_digest. An ordinary body hash alone is not authentication: anyone can compute it.

Read the bounded raw body before JSON parsing or formatting. Adding one space can leave JSON meaning unchanged but change its signature. This lab uses its own academy-webhook-v1 protocol, not a GitHub or Stripe wire format. The signed message is the fixed version line, route namespace, delivery ID and decimal timestamp, each followed by a newline, then the original body bytes. Identity fields cannot contain delimiters. The signature header is v1= followed by exactly 64 lowercase hexadecimal characters. Real integrations must follow their provider's exact protocol rather than substitute this one.

The receiver chooses the secret from copied server configuration for the route. It never chooses authority from an event's claimed namespace. Metadata and route are signed so the same body cannot move between scopes or delivery IDs. This exercise allows timestamps within 300 seconds of the supplied current epoch time, including the boundaries. A valid old signature still fails freshness. A legitimate retry must be signed again with a fresh timestamp and the same stable delivery ID and raw bytes.

After signature verification, parse strict UTF-8 JSON: exactly version, id, revision and value; integer version 1; bounded exact integer fields; no duplicate keys, extra namespace, coercion or booleans masquerading as integers. Authentication failures return generic 401. Authenticated invalid events return 422. Body size and content-type policies may reject before authentication; their replies reveal no event data.

## Guided practice

Predict the printed value before running this small illustration. Then explain which part requires a real request or database observation.

```python
import hmac
secret = b"example-only-key-32-bytes-long!!!"
raw = b'{"value":0}'
signature = hmac.new(secret, raw, "sha256").digest()
print(hmac.compare_digest(signature, hmac.new(secret, raw + b" ", "sha256").digest()))
```

## Independent practice

Implement verify. Use the public independent HMAC vector and tamper each metadata field, secret and raw body. Test both freshness boundaries. Sign invalid JSON and compare its result to the same bytes with a wrong signature.

## Check your work

Keep secrets and raw bodies out of logs, error details and submitted artifacts. The example below signs only raw bytes to illustrate HMAC; the lab signs its complete framed message.

Continue with the [API depth lab](/projects#python-api-depth). Record commands and outcomes; keep private credentials out of submitted evidence.
