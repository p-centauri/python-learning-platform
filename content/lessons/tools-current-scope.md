A tool loop takes time. The model waits for a response, a tool waits for a resource, and the user may lose permission between those events. Permission checked once at the beginning is insufficient. The local lab reads current Authority from an application-owned callback before each provider request, after a valid proposal and immediately before local execution. The complete original principal snapshot and actor must still match, and read permission must remain enabled.

Selected RAG citations are checked against the current source index too. Deleted, updated, inactive or newly restricted documents no longer resolve to the old exact span. An old citation cannot restore the earlier document version. The context check is intentionally conservative: every selected citation must still resolve, even if the next action targets only one. This can stop useful work, but its finite freshness rule is easy to state and test.

The controlled local tool adapter can wait before executing. After that wait, execution refreshes authority again; it never relies on the permission captured before waiting. A post-execution wait can model a delayed result. The loop checks source and authority after this wait before exposing or resending that result. Public reports redact source excerpts, while a fresh permitted provider request can receive the observed read text. A previous read cannot become permanent access to a private source.

A note may already have committed when permission later changes. Rejecting a stale result does not undo that historical local effect. Distinguish the time of authorization, commit and returned observation. Local source and note databases do not share one distributed transaction; a check cannot eliminate all races between stores or prevent future revocation. Production systems need a policy for these windows. The lab proves its stated local observation points and uses trusted authority metadata; it does not establish complete authentication or distributed revocation.

## Guided practice

Predict the printed result, then explain which tool boundary this small illustration leaves untested.

```python
current_groups = {"reader"}
required_group = "finance"
print(required_group in current_groups)
```

## Independent practice

Test permission loss and source update/deletion during provider waits, before tool execution and after a committed write. Verify old read text is excluded from public reports.

## Check your work

Separate a blocked action from a committed action whose result became stale. State the cross-store race and final observation limits.

Use the [Authorized tools project](/projects#tools). Record commands, versions and failures. Reported tests and manual review remain separate from mastery.
