from dataclasses import dataclass
from academy_feed_objects import FeedKey, Reading, Snapshot
from academy_ingestion_service import Datum


@dataclass(frozen=True, slots=True)
class Item:
    namespace: str
    datum: Datum

    def __post_init__(self) -> None:
        if type(self.datum) is not Datum:
            raise ValueError("exact Datum required")
        Datum(self.datum.id, self.datum.revision, self.datum.value)
        Reading(FeedKey(self.namespace, self.datum.id), self.datum.value)


@dataclass(frozen=True, slots=True)
class Analysis:
    snapshot: Snapshot
    fingerprints: tuple[str, ...]
    computations: int
    hits: int
    cache_size: int
