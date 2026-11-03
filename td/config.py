"""Tunable numbers: map, towers, enemies, waves. Change balance here."""

TILE = 48
COLS, ROWS = 20, 13
SIDEBAR_W = 260
WIDTH, HEIGHT = COLS * TILE + SIDEBAR_W, ROWS * TILE
FPS = 60

START_GOLD = 150
START_LIVES = 20
SELL_REFUND = 0.7          # fraction of everything spent on a tower
WAVE_BONUS = 25            # gold for clearing a wave, plus 2 per wave number

# Path as grid waypoints (col, row). Enemies enter at the first and leave at the last.
# The first and last points sit just off the map so enemies walk in and out.
PATH = [
    (-1, 2), (4, 2), (4, 8), (9, 8), (9, 3), (14, 3), (14, 9), (17, 9), (17, 5), (20, 5),
]

# Tower stats per level. range/size are in tiles, rate is shots per second.
TOWERS = {
    "arrow": {
        "name": "Arrow",
        "key": "1",
        "color": (90, 170, 90),
        "desc": "Fast single-target shots.",
        "levels": [
            {"cost": 50, "damage": 10, "range": 2.6, "rate": 2.0},
            {"cost": 40, "damage": 16, "range": 2.9, "rate": 2.5},
            {"cost": 70, "damage": 26, "range": 3.2, "rate": 3.0},
        ],
    },
    "cannon": {
        "name": "Cannon",
        "key": "2",
        "color": (160, 110, 70),
        "desc": "Slow shells that hit an area.",
        "levels": [
            {"cost": 90, "damage": 22, "range": 2.4, "rate": 0.6, "splash": 1.0},
            {"cost": 70, "damage": 38, "range": 2.6, "rate": 0.7, "splash": 1.2},
            {"cost": 120, "damage": 60, "range": 2.9, "rate": 0.8, "splash": 1.4},
        ],
    },
    "frost": {
        "name": "Frost",
        "key": "3",
        "color": (90, 160, 220),
        "desc": "Light damage, slows enemies.",
        "levels": [
            {"cost": 70, "damage": 4, "range": 2.2, "rate": 1.2, "slow": 0.5, "slow_time": 1.5},
            {"cost": 60, "damage": 7, "range": 2.5, "rate": 1.4, "slow": 0.4, "slow_time": 2.0},
            {"cost": 90, "damage": 11, "range": 2.8, "rate": 1.6, "slow": 0.3, "slow_time": 2.5},
        ],
    },
}

# speed in tiles per second; reward in gold; leak is lives lost if it gets through.
ENEMIES = {
    "grunt": {"hp": 40, "speed": 1.6, "reward": 6, "leak": 1, "radius": 11, "color": (210, 80, 80)},
    "runner": {"hp": 25, "speed": 3.0, "reward": 5, "leak": 1, "radius": 8, "color": (230, 200, 70)},
    "brute": {"hp": 180, "speed": 0.9, "reward": 18, "leak": 3, "radius": 16, "color": (150, 70, 170)},
}


def wave_plan(n):
    """Spawn list for wave n (1-based): [(enemy_kind, delay_before_spawn_s), ...]."""
    plan = []
    grunts = 6 + 2 * n
    for _ in range(grunts):
        plan.append(("grunt", 0.8))
    if n >= 2:
        for _ in range(2 + n):
            plan.append(("runner", 0.45))
    if n >= 4:
        for _ in range(n // 2):
            plan.append(("brute", 1.6))
    return plan


def hp_scale(n):
    """Enemy HP multiplier for wave n, so later waves keep up with upgrades."""
    return 1.0 + 0.18 * (n - 1) + 0.012 * (n - 1) ** 2
