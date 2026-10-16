"""Supplied closed-query observations. EXPLAIN ANALYZE executes the fixed SELECT."""
from dataclasses import dataclass
from enum import Enum
import math
from sqlalchemy import Engine, text
from .contracts import Filter, copied, limit as valid_limit, scoped
from .support import read, resource


class PlanQuery(str, Enum):
    RANGE = "range"
    NOTES = "notes"


@dataclass(frozen=True, slots=True)
class Node:
    kind: str
    estimated_rows: int
    actual_rows: float
    loops: int
    index: str | None


@dataclass(frozen=True, slots=True)
class Plan:
    estimated_rows: int
    actual_rows: int
    loops: int
    total_cost: float
    execution_ms: float
    shared_hits: int
    shared_reads: int
    node_types: tuple[str, ...]
    indexes: tuple[str, ...]
    nodes: tuple[Node, ...]


def summarize_plan(document: object) -> Plan:
    if type(document) is not list or len(document) != 1 or type(document[0]) is not dict:
        raise ValueError("one JSON plan required")
    root = document[0].get("Plan")
    if type(root) is not dict:
        raise ValueError("plan root required")
    types: list[str] = []
    observed: list[Node] = []
    indexes: list[str] = []
    todo = [root]
    while todo:
        if len(types) >= 64:
            raise ValueError("plan exceeds observation bound")
        node = todo.pop()
        types.append(str(node["Node Type"]))
        if "Index Name" in node:
            indexes.append(str(node["Index Name"]))
        observed.append(Node(str(node["Node Type"]), int(node["Plan Rows"]), float(node["Actual Rows"]), int(node["Actual Loops"]), str(node["Index Name"]) if "Index Name" in node else None))
        children = node.get("Plans", [])
        if type(children) is not list or any(type(child) is not dict for child in children):
            raise ValueError("invalid child plans")
        todo.extend(reversed(children))
    execution = float(document[0]["Execution Time"])
    cost = float(root["Total Cost"])
    if not math.isfinite(execution) or not math.isfinite(cost) or execution < 0 or cost < 0:
        raise ValueError("invalid plan observation")
    return Plan(int(root["Plan Rows"]), int(root["Actual Rows"]), int(root["Actual Loops"]), cost, execution, int(root.get("Shared Hit Blocks", 0)), int(root.get("Shared Read Blocks", 0)), tuple(types), tuple(indexes), tuple(observed))


def explain(engine: Engine, query: PlanQuery, namespace: str, /, *, filter: Filter | None = None, minimum: int = 900000, maximum: int = 900100, limit: int = 32) -> Plan:
    scoped(namespace)
    valid_limit(limit)
    if type(query) is not PlanQuery:
        raise ValueError("closed PlanQuery required")
    for number in (minimum, maximum):
        if type(number) is not int or not 0 <= number <= 1000000:
            raise ValueError("bounded exact value required")
    if minimum > maximum:
        raise ValueError("ordered range required")
    configured = copied(filter) if filter is not None else Filter('{"kind":"rare"}')
    parameters: dict[str, object] = {"namespace": namespace, "minimum": minimum, "maximum": maximum, "filter": configured.encoded, "limit": limit}
    sql = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + resource(query.value + ".sql")
    with read(engine) as connection:
        document: object = connection.execute(text(sql), parameters).scalar_one()
    return summarize_plan(document)
