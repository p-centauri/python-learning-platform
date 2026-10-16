A model can suggest an action, but a suggestion is not permission to perform it. Imagine a proposal saying “save a note for another account.” A well-formed JSON object still cannot prove that the caller owns that account. The application must decide which operations exist, which arguments they accept and whether the current person may use them. Keep these decisions outside generated text.

The local lab has two deliberately small tools. source_excerpt reads one selected current RAG citation. save_note saves a bounded label and source digest in a separate local database. Neither tool accepts a URL, filesystem path, shell command, tenant, role or approval from the model. Names and argument fields are exact: extra fields cause rejection rather than being silently ignored. Read takes only a citation ID; write also takes a nonblank label with a UTF-8 byte limit and no control characters.

The proposal envelope pins the configured model and tool-proposals-v1 schema. Complete output contains one call or an explicit finish variant. Refusal and incomplete output have no proposal. Metering must use exact bounded integers; True is not accepted as the integer one. Strict bytes, UTF-8, duplicate-field and nonfinite-value checks happen before any dispatch. Invalid envelopes keep a conservative unknown-usage reservation rather than pretending the attempted call was free.

Validation answers “does this proposal match the contract?” Authorization answers “may this current caller do this exact action?” These are different checks. An allowlisted tool can still be forbidden for a particular person or source. A finish proposal does not prove any action happened; the application reports only observed tool outcomes. Generated labels remain data and are never interpreted as executable instructions. Controlled fixtures reproduce these boundaries without contacting a real model.

## Guided practice

Predict the printed result, then explain which tool boundary this small illustration leaves untested.

```python
allowed = {"source_excerpt", "save_note"}
print("run_shell" in allowed)
```

## Independent practice

Implement strict proposal variants and argument shapes. Test unknown names, extra tenant/role fields, invented citation URLs and invalid integer usage before any side effect.

## Check your work

Explain validation versus permission. Verify malformed proposals stop dispatch and finish text cannot invent a completed action.

Use the [Authorized tools project](/projects#tools). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
