"""Read and validate shared version 1 campaign data."""

import json
from math import isfinite


def require(condition, field, message):
    if not condition:
        raise ValueError(f"{field}: {message}")


def polyline(points, cols, rows, field):
    require(isinstance(points, list) and len(points) >= 2, field,
            "expected at least two waypoints")
    for index, point in enumerate(points):
        here = f"{field}[{index}]"
        require(isinstance(point, list) and len(point) == 2
                and all(type(value) is int for value in point), here,
                "expected two integer coordinates")
        col, row = point
        inside = 0 <= col < cols and 0 <= row < rows
        edge = ((col in (-1, cols) and 0 <= row < rows)
                or (row in (-1, rows) and 0 <= col < cols))
        require(edge if index in (0, len(points) - 1) else inside, here,
                "endpoints must sit one tile outside the board and other points inside")
        if index:
            last_col, last_row = points[index - 1]
            require((last_col == col) != (last_row == row), here,
                    "expected a nonzero horizontal or vertical segment")
    require(points[0] != points[-1], field, "endpoints must differ")


def validate(level):
    require(isinstance(level, dict), "campaign", "expected an object")
    version = level.get("version")
    require(type(version) is int and version == 1, "version", "expected version 1")
    cols, rows = (level["board"][key] for key in ("cols", "rows"))
    require(all(type(value) is int and value > 0 for value in (cols, rows)),
            "board", "expected positive integer dimensions")
    for map_id, spec in level["maps"].items():
        polyline(spec["path"], cols, rows, f"maps.{map_id}.path")
        if "river" in spec:
            polyline(spec["river"], cols, rows, f"maps.{map_id}.river")
        for index, (sprite, col, row, width, height) in enumerate(spec["decor"]):
            require(isinstance(sprite, str) and bool(sprite)
                    and all(type(n) is int for n in (col, row, width, height))
                    and 0 <= col < col + width <= cols
                    and 0 <= row < row + height <= rows,
                    f"maps.{map_id}.decor[{index}]", "invalid scenery footprint")

    require(isinstance(level["waves"], list) and bool(level["waves"]),
            "waves", "expected a nonempty wave list")
    for index, wave in enumerate(level["waves"]):
        field = f"waves[{index}]"
        require(wave["faction"] in level["factions"], f"{field}.faction",
                "unknown faction ID")
        hp = wave["hp_multiplier"]
        require(type(hp) in (int, float) and isfinite(hp) and hp > 0,
                f"{field}.hp_multiplier", "expected a finite positive multiplier")
        require(isinstance(wave["groups"], list) and bool(wave["groups"]),
                f"{field}.groups", "expected at least one spawn group")
        for group_index, group in enumerate(wave["groups"]):
            entry = f"{field}.groups[{group_index}]"
            require(group["enemy"] in level["enemies"], f"{entry}.enemy",
                    f"unknown enemy ID {group['enemy']!r}")
            count, delay = group["count"], group["delay"]
            require(type(count) is int and count > 0, f"{entry}.count",
                    "expected a positive integer")
            require(type(delay) in (int, float) and isfinite(delay) and delay >= 0,
                    f"{entry}.delay", "expected finite nonnegative seconds")


def load_level(filename):
    try:
        with filename.open(encoding="utf-8") as source:
            level = json.load(source)
        validate(level)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        raise ValueError(f"{filename}: {error}") from error
    return level
