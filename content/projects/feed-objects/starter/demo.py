import json
from academy_feed_objects import Budget, FeedKey, Reading, Snapshot

def main() -> None:
    budget = Budget(2)
    snapshot = Snapshot([Reading(FeedKey("demo", "api"), 5), Reading(FeedKey("demo", "worker"), 10)])
    print(json.dumps({"limit": budget.limit, "count": len(snapshot), "total": sum(row.value for row in snapshot)}))

if __name__ == "__main__":
    main()
