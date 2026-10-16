A citation needs more than a link to an existing document. It must connect visible output to the evidence actually allowed and supplied for this answer. The lab assigns e0, e1 and e2 only to selected excerpts in one Bundle. These short IDs have no meaning in another run. Their source identity includes tenant, document, revision, chunk ordinal, character offsets and digest.

The controlled generator proposes a small list of evidence IDs and quotes. The application checks strict JSON shape, configured model and schema identity, complete status and exact usage values before treating the response as a proposal. Every reference must name a distinct selected ID. The quote must equal that entire source chunk. Extra commands, unknown IDs, duplicate references and changed wording fail rather than being repaired. A document that was retrieved but omitted from context is not available for citation.

This is an extractive baseline: visible text is built from validated source excerpts. It deliberately does not validate arbitrary paraphrases or freeform conclusions. Exact equality establishes where the quote came from, not whether the source is reliable or the excerpt answers the question. A chunk may start in the middle of a sentence, and conflicting sources still require a stated policy or human judgment. Do not claim that valid citations eliminate hallucination in a general model.

The citation resolver reads current application-owned document state and permissions without fetching a URL. It returns the excerpt only if the current source key, text, offsets and digest still match and the principal may read it. An old source revision, deletion or revoked access returns no text. Refreshing this check when revisiting a citation prevents a saved answer from becoming a permanent permission grant. Source metadata and the authority service remain application assumptions, not facts a model can choose.

## Guided practice

Predict the printed result, then explain which evidence boundary this small illustration leaves untested.

```python
source = "Close the file."
quote = "Close"
print(quote == source)
```

## Independent practice

Validate a complete response with at most two whole-excerpt claims, distinct selected IDs and no extra fields. Bind citations to exact source spans and resolve them under current permissions.

## Check your work

Separate exact provenance, semantic support and source truth. No generated URL or citation ID can authorize a source or a business action.

Use the [Evidence answering project](/projects#rag). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
