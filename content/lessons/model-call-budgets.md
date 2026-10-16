A run budget should decide whether another call is allowed before making that call. Checking cost only after several responses arrive can overspend the stated policy. The fixture computes a maximum local reservation from the request's input bound and configured maximum output, multiplied by fictional integer rates. Admit a call only when its full reservation fits the remaining run credits. This avoids float rounding and makes exact boundary cases reproducible.

After a fully valid reply, the ledger settles to the bounded provider-reported usage and releases unused credits. This also applies to known refusal and incomplete variants, though both stop the run. If the response is malformed, the provider fails, or the call times out, keep the entire reservation. The system cannot safely infer zero usage from missing or invalid metering. A later attempt is still gated by a fresh full reservation; a low actual charge from the first call does not remove that gate.

The step limit counts attempts, including failed attempts, rather than only useful answers. The lab accepts at most eight preflight prompts and at most max_steps actual calls. It never automatically retries refusals, malformed output or timeouts. Extra attempts consume time and possibly provider usage; they need a deliberate bounded retry and reconciliation policy. The current run ends with a fixed stop kind and a copied tuple of step evidence.

These credits are fictional teaching units, not current provider prices or a real-money ceiling. The fixture input bound is a full-byte counting rule, not a verified tokenizer. Metering is a provider claim checked against fixture bounds, not an audited invoice. Each new run gets an independent local ledger; it does not enforce a durable account quota or recover cancelled work. Keep these limits visible when presenting results. Production billing, hidden usage, price versions, concurrency and persistent reservation/reconciliation belong to separate work, while these tests establish the finite admission and settlement contract.

## Guided practice

Predict the printed result, then describe the part of the real model boundary that this small illustration leaves untested.

```python
reserved = 10 * 2 + 5 * 4
known_charge = 4 * 2 + 1 * 4
print(reserved - known_charge)
```

## Independent practice

Implement async run. Test reserve-minus-one refusal/no call, exact-reserve admission, later settlement and next-call gating, actual attempt limits, zero rates and full reservations for unknown usage.

## Check your work

Report fictional rates and fixture units explicitly. Show no request was made when admission failed; explain why the ledger is not durable billing or an account quota.

Use the [Model contracts project](/projects#model-contracts). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
