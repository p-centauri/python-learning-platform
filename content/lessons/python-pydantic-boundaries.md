## The idea in plain language

Type hints describe intended values; incoming JSON still needs validation. Pydantic models define the allowed shape, types and ranges. Strict mode prevents convenient conversions such as a numeric string becoming an integer. Extra fields can be forbidden rather than silently ignored.

The batch accepts only items, at most 64. Each item contains only id, revision and value. Revision is an exact integer 1..8 and value 0..1000000. Booleans and floats do not pass as integers; zero remains valid. ASCII identifiers use an explicit whole-string validator. The path supplies namespace after authorization, so the body cannot choose another namespace.

ConfigDict(strict=True, extra="forbid") makes boundary choices explicit. Pydantic's behavior depends on the target type and whether input is Python or JSON: learn the documented conversion rules rather than assume strict means every possible object is identical. This lab evaluates its integer/string JSON contract directly. Frozen models prevent ordinary field assignment but nested containers can still be mutable; the route creates immutable domain values before persistence.

Use output models separately from ORM entities. Loading a full database row and handing it to serialization can reveal internal fields or trigger lazy database work after session closure. Build the receipt/page DTO while the transaction/session is active. The lab returns only chosen fields, then closes its request session.

Validation errors can echo input in default details. Here expected validation failures use a generic 422 without raw body/credentials. That is an explicit response policy, not semantic AI grading. Payload item bounds happen after reading/parsing input; public byte/rate limits require their own ingress controls later. The worked example executes real Pydantic validation locally without a database.

## Worked example

Save this local Python illustration as example.py. Actual database evidence comes from the PostgreSQL lab, not this illustration.

```python
from pydantic import BaseModel, ConfigDict, ValidationError
class Count(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    value: int
print(Count.model_validate({"value": 0}).value)
try:
    Count.model_validate({"value": "5"})
except ValidationError:
    print("string rejected")
```

## Guided practice

Compare shape/type/range validation with annotations. Explain zero, forbidden namespace fields and JSON versus Python conversion rules.

## Independent practice

Run malformed payloads and the output allowlist cases; add a regression for a misleading conversion or extra field.

## Check your work

Strict input does not certify database correctness or bound request bytes. Return explicit public values.

Continue to [Authenticate first, authorize each namespace](/lessons/python-api-permissions).
