A local test run and an installed package answer different questions. Tests run from a source checkout may find files that were accidentally omitted from the wheel. Build the completed package, install it into a fresh environment, and run from an unrelated directory. Verify the import path, dependency consistency, py.typed marker and packaged fixture.json resource. Importing the package should remain quiet; the demo runs only under its main guard.

The demo computes exact cosine and keyword reports at k=1 and k=3. It records the package, dataset and vector-space versions, case counts, actual keys and scores, and the stated fixture limits. Save retrieval.json and read it back to confirm the stored evidence matches the computed report. The report excludes raw document text and includes only the metadata needed for this finite ranking review. Test output copied into a form is reported evidence, not a server-executed grading result.

For independent practice, design a new regression before running it. Predict what a wrong implementation would return, choose a permission, revision, tie or denominator failure, then show the test catches it. Explain the expected result using the contract rather than repeating supplied tests. Add a short decision note about chunk size or threshold, the observed tradeoff and which future data would challenge it. A reviewer must judge whether this work is original and well reasoned.

Passing 83 supplied cases establishes only their finite behavior. Hand-supplied vectors cannot prove a real embedding model understands language. The fixture is development data, not held-out evaluation. Exact in-memory ranking cannot establish vector-database operations or ANN recall. Retrieved evidence cannot by itself certify an answer, a permission system or Python expertise. The linked project keeps milestones, reported tests, self review and human feedback separate from objective mastery. Later RAG work will add evidence selection, citations and missing-evidence abstention without changing what this lab actually measured.

## Guided practice

Predict the printed result, then explain which retrieval boundary this small illustration leaves untested.

```python
versions = {"dataset": "retrieval-fixture-v1", "model": "manual-vectors"}
print(versions["dataset"])
```

## Independent practice

Build/install the completed wheel outside source, run all cases/types/demo, save retrieval.json and submit one independently predicted regression plus decision note through the linked project.

## Check your work

Separate reported commands, manual originality/reasoning, finite ranking evidence and unverified real-model quality. Reading and manual milestones do not certify mastery.

Use the [Scoped retrieval project](/projects#retrieval). Record exact commands, versions and failures. Reported tests and manual review remain separate from mastery.
