from dataclasses import asdict
import hashlib
import json
from importlib.resources import files
from typing import cast
from .contracts import Case, Suite, Observation, Layer


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def nonfinite(value: str) -> object:
    raise ValueError("nonfinite JSON")


def fields(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError("exact dataset fields required")
    return cast(dict[str, object], value)


def load_suite(raw: bytes | None = None) -> Suite:
    if raw is None:
        raw = files("academy_ai_evaluation").joinpath("release-cases.json").read_bytes()
    if type(raw) is not bytes or not 1 <= len(raw) <= 32768:
        raise ValueError("bounded dataset bytes required")
    root = fields(
        json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite),
        {"version", "purpose", "cases"},
    )
    rows = root["cases"]
    if type(rows) is not list or not 1 <= len(rows) <= 32:
        raise ValueError("bounded cases required")
    cases = []
    for row in rows:
        value = fields(row, {"id", "scenario", "layer", "relevant", "reason", "effects", "answered", "human"})
        if type(value["relevant"]) is not list:
            raise ValueError("relevance array required")
        cases.append(
            Case(
                cast(str, value["id"]),
                cast(str, value["scenario"]),
                cast("Layer", value["layer"]),
                tuple(cast(list[str], value["relevant"])),
                cast(str, value["reason"]),
                cast(int, value["effects"]),
                cast(bool, value["answered"]),
                cast(bool, value["human"]),
            )
        )
    return Suite(cast(str, root["version"]), cast(str, root["purpose"]), tuple(cases))


def suite_digest(suite: Suite) -> str:
    return hashlib.sha256(canonical(asdict(suite))).hexdigest()


def candidate_digest(observations: tuple[Observation, ...]) -> str:
    return hashlib.sha256(
        canonical([asdict(o) for o in sorted(observations, key=lambda x: x.case_id)])
    ).hexdigest()
