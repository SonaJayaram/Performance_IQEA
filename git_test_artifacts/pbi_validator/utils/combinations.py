"""
Filter-combination selection for the PBI validator sweep.

Given the available values of each slicer, produce a bounded, DIVERSE set of
filter combinations to extract. 'Diverse' = spread across every slicer value as
evenly as possible so N runs exercise N different values instead of repeating
one. Selection is deterministic: the same options + count always yield the same
combinations, so a sweep is repeatable.
"""
from functools import reduce


def total_possible(options: dict) -> int:
    """Full cartesian product size across all slicers that have values."""
    sizes = [len(v) for v in options.values() if v]
    if not sizes:
        return 0
    return reduce(lambda a, b: a * b, sizes, 1)


def build_combinations(options: dict, count: int, strategy: str = "diverse") -> list:
    """
    Build up to `count` filter combinations.

    Args:
        options  — {slicer_name: [value, value, ...]} for the slicers to vary.
                   Slicers with an empty list are ignored (held at default).
        count    — max number of combinations to return (the config cap).
        strategy — 'diverse' (round-robin spread, recommended) or
                   'first' (first N of the plain cartesian product).

    Returns:
        list of dicts, each {slicer_name: chosen_value}. Length <= count and
        <= total_possible(options). No duplicate combinations.
    """
    slicers = [s for s, v in options.items() if v]
    if not slicers or count <= 0:
        return []

    total = total_possible(options)
    n = min(count, total)

    if strategy == "first":
        return _cartesian(options, slicers, n)

    # ── diverse: round-robin each slicer through its own values ──────────────
    # combo[i][slicer] = values[i % len(values)] — every slicer cycles through
    # all its values independently, so each value appears before any repeats and
    # the combinations spread across the whole space.
    combos = []
    seen = set()
    i = 0
    guard = 0
    max_guard = total * 3 + n  # bound the loop even if the diagonal repeats
    while len(combos) < n and guard < max_guard:
        combo = {s: options[s][i % len(options[s])] for s in slicers}
        key = tuple(sorted(combo.items()))
        if key not in seen:
            seen.add(key)
            combos.append(combo)
        i += 1
        guard += 1
    return combos


def _cartesian(options: dict, slicers: list, n: int) -> list:
    """First `n` combinations of the plain cartesian product (odometer order)."""
    combos = []
    idx = [0] * len(slicers)
    while len(combos) < n:
        combos.append({s: options[s][idx[k]] for k, s in enumerate(slicers)})
        # increment odometer
        k = len(slicers) - 1
        while k >= 0:
            idx[k] += 1
            if idx[k] < len(options[slicers[k]]):
                break
            idx[k] = 0
            k -= 1
        if k < 0:
            break  # wrapped all the way round — exhausted
    return combos


def combo_label(combo: dict) -> str:
    """
    Human-readable one-line label for a combination, used in the manifest and
    for messaging. e.g. {'Region': 'West', 'Segment': 'Consumer'}
                     -> 'Region=West | Segment=Consumer'
    """
    return " | ".join(f"{k}={v}" for k, v in combo.items())


def combo_filename(combo: dict, index: int) -> str:
    """
    Safe, unique .xlsx filename for a combination.
    e.g. (idx 3, {'Region':'North Asia','Segment':'Consumer'})
         -> '03_Region-North_Asia__Segment-Consumer.xlsx'
    """
    import re
    parts = []
    for k, v in combo.items():
        piece = f"{k}-{v}"
        piece = re.sub(r"[^A-Za-z0-9]+", "_", piece).strip("_")
        parts.append(piece)
    stem = "__".join(parts) if parts else "combo"
    stem = stem[:100]  # keep well under filesystem limits
    return f"{index:02d}_{stem}.xlsx"
