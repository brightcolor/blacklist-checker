from collections.abc import Sequence


def to_csv_int(values: Sequence[int]) -> str:
    return ",".join(str(v) for v in sorted(set(values)))


def from_csv_int(value: str | None) -> list[int]:
    if not value:
        return []
    out: list[int] = []
    for item in value.split(","):
        cleaned = item.strip()
        if not cleaned:
            continue
        out.append(int(cleaned))
    return out
