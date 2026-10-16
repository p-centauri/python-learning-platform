import json
from academy_typed_transforms import decode_row, first, map_rows, watch_call


def main() -> None:
    events: list[str] = []
    observed = watch_call(decode_row, observer=events.append)
    rows = map_rows([{"id": "api", "value": 5}, {"id": "worker", "value": 10}], observed)
    result = first(rows)
    print(
        json.dumps(
            {
                "count": len(rows),
                "total": sum(row.value for row in rows),
                "first": None if result is None else result.id,
                "events": events,
            }
        )
    )


if __name__ == "__main__":
    main()
