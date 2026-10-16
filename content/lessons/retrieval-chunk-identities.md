Retrieval starts with documents split into smaller pieces called chunks. A chunk must still point to the document it came from. Keep the tenant, document ID, document revision and chunk ordinal together as its identity. The tenant matters because two accounts may use the same document ID. The revision matters because an updated document can have different text at the same position. An ordinal alone cannot identify evidence safely.

The lab splits text into fixed character windows. With width 16 and overlap 4, the next window starts 12 characters after the previous start. Overlap repeats a small part to reduce the chance that a useful phrase disappears across a boundary. It also increases repeated evidence and storage. There is no universally best size: a later real corpus needs measured choices. This exercise fixes width and overlap so its results are reproducible.

Save start and end as Python string indices and keep the exact original slice. These are character offsets, not UTF-8 byte offsets. An accented character or emoji can occupy multiple bytes. Compute SHA256 from the chunk's UTF-8 bytes to detect a text mismatch. The digest cannot prove that the source is trusted or that a statement is true. Never trim a window silently; its saved offsets would then describe different text.

Stop after a window reaches the document end. Do not emit another overlapping suffix. A document requiring more than 32 windows fails the whole operation rather than returning an incomplete prefix. The supplied Document is immutable and validated, but the function revalidates current values before copying. The current corpus is a teaching input, not a database with atomic update or deletion guarantees. Your independent regression should challenge one of these assumptions and predict the failure before execution.

## Guided practice

Predict the printed result, then explain which retrieval boundary this small illustration leaves untested.

```python
text = "éabc"
print(len(text.encode("utf-8")) - len(text))
```

## Independent practice

Implement make_chunks. Verify exact slices, Unicode offsets, overlap, final-tail behavior and stable complete keys. Show that changing revision changes identity without mutating the input.

## Check your work

Explain which chunking choice you measured and which source-lifecycle assumptions remain supplied by the application.

Use the [Scoped retrieval project](/projects#retrieval). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
