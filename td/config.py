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

# Maps. "path" is grid waypoints (col, row): enemies enter at the first and leave at the
# last, which sit just off the map. "decor" is scenery from assets/map/ as
# (sprite, col, row, width, height) in tiles; sprites stand on the bottom edge of their
# footprint. "river" (optional) is a polyline of tile waypoints; where the path crosses
# it a bridge is drawn. Towers can't be built on the path, scenery or water.
MAPS = {
    "village": {
        "name": "Village Road",
        "path": [
            (-1, 2), (4, 2), (4, 8), (9, 8), (9, 3), (14, 3), (14, 9), (17, 9), (17, 5), (20, 5),
        ],
        "decor": [
            ("pine", 0, 0, 1, 1), ("oak", 2, 0, 1, 1),
            ("cottage_thatch", 6, 0, 2, 2), ("well", 8, 1, 1, 1),
            ("stall_blue", 11, 0, 1, 1), ("stall_yellow", 12, 0, 1, 1), ("lamp", 13, 1, 1, 1),
            ("roof_red", 16, 0, 2, 2), ("pine", 19, 0, 1, 1), ("oak", 18, 2, 1, 1),
            ("cottage_blue", 0, 4, 2, 2),
            ("vegetable_patch", 0, 7, 1, 1), ("vegetable_patch", 1, 7, 1, 1),
            ("fence", 0, 9, 1, 1), ("fence", 1, 9, 1, 1), ("fence_corner", 2, 9, 1, 1),
            ("pine", 0, 11, 1, 1), ("pine", 1, 12, 1, 1), ("oak", 3, 11, 1, 1),
            ("flower_bed", 6, 5, 1, 1),
            ("crates", 6, 10, 1, 1), ("crate", 7, 10, 1, 1), ("barrel", 8, 10, 1, 1),
            ("cart", 10, 10, 1, 1), ("barrel", 11, 10, 1, 1), ("crates", 12, 11, 1, 1),
            ("rocks", 8, 12, 1, 1), ("pine", 5, 12, 1, 1), ("oak", 13, 12, 1, 1),
            ("well", 11, 6, 1, 1), ("rocks", 16, 6, 1, 1),
            ("signpost", 18, 4, 1, 1), ("lamp", 19, 6, 1, 1), ("plaza", 18, 7, 2, 2),
            ("cottage_thatch", 18, 10, 2, 2), ("pine", 19, 12, 1, 1), ("oak", 17, 11, 1, 1),
            ("flower_bed", 15, 11, 1, 1),
        ],
    },
    "farm": {
        "name": "Farmland",
        "path": [(-1, 10), (3, 10), (3, 2), (8, 2), (8, 10), (13, 10), (13, 2), (17, 2), (17, 7), (20, 7)],
        "decor": [
            ("pine", 0, 0, 1, 1), ("oak", 1, 0, 1, 1), ("pine", 5, 0, 1, 1),
            ("cottage_blue", 9, 0, 2, 2), ("well", 11, 1, 1, 1),
            ("oak", 18, 0, 1, 1), ("pine", 19, 0, 1, 1),
            ("roof_red", 0, 4, 2, 2),
            ("vegetable_patch", 0, 7, 1, 1), ("vegetable_patch", 1, 7, 1, 1),
            ("vegetable_patch", 0, 8, 1, 1), ("vegetable_patch", 1, 8, 1, 1),
            ("vegetable_patch", 5, 4, 1, 1), ("vegetable_patch", 6, 4, 1, 1),
            ("vegetable_patch", 5, 5, 1, 1), ("vegetable_patch", 6, 5, 1, 1),
            ("fence", 5, 7, 1, 1), ("fence", 6, 7, 1, 1),
            ("lamp", 11, 4, 1, 1), ("flower_bed", 10, 5, 1, 1), ("bench", 10, 8, 1, 1),
            ("stall_blue", 14, 5, 1, 1), ("stall_yellow", 15, 5, 1, 1),
            ("lamp", 19, 4, 1, 1), ("signpost", 18, 6, 1, 1),
            ("plaza", 18, 8, 2, 2), ("cottage_thatch", 18, 10, 2, 2),
            ("pine", 0, 12, 1, 1), ("oak", 2, 12, 1, 1), ("crates", 5, 12, 1, 1),
            ("barrel", 6, 12, 1, 1), ("cart", 10, 12, 1, 1), ("rocks", 15, 12, 1, 1),
            ("pine", 19, 12, 1, 1),
        ],
    },
    "river": {
        "name": "Riverside",
        "path": [(-1, 2), (14, 2), (14, 6), (5, 6), (5, 10), (20, 10)],
        "river": [(10, -1), (10, 13)],
        "decor": [
            ("pine", 0, 0, 1, 1), ("oak", 1, 0, 1, 1), ("cottage_blue", 3, 0, 2, 2),
            ("well", 6, 1, 1, 1), ("stall_blue", 7, 0, 1, 1), ("stall_yellow", 8, 0, 1, 1),
            ("roof_red", 11, 0, 2, 2), ("lamp", 15, 1, 1, 1),
            ("pine", 17, 0, 1, 1), ("oak", 18, 1, 1, 1),
            ("vegetable_patch", 0, 4, 1, 1), ("vegetable_patch", 1, 4, 1, 1),
            ("flower_bed", 7, 4, 1, 1), ("rocks", 12, 4, 1, 1),
            ("plaza", 17, 4, 2, 2), ("signpost", 16, 7, 1, 1), ("cottage_thatch", 17, 8, 2, 2),
            ("cottage_thatch", 1, 8, 2, 2), ("well", 8, 8, 1, 1),
            ("crates", 12, 8, 1, 1), ("barrel", 13, 8, 1, 1),
            ("pine", 0, 11, 1, 1), ("oak", 2, 11, 1, 1), ("pine", 1, 12, 1, 1),
            ("crates", 7, 12, 1, 1), ("cart", 12, 12, 1, 1), ("rocks", 15, 12, 1, 1),
            ("flower_bed", 16, 12, 1, 1), ("oak", 19, 11, 1, 1), ("pine", 18, 12, 1, 1),
        ],
    },
}
GROUND_DECOR = {"plaza", "flower_bed", "vegetable_patch"}   # drawn flat, under everything

# Difficulty multiplies every enemy's health and speed.
DIFFICULTIES = {
    "easy": {"name": "Easy", "hp": 0.75, "speed": 0.85},
    "normal": {"name": "Normal", "hp": 1.0, "speed": 1.0},
    "hard": {"name": "Hard", "hp": 1.5, "speed": 1.25},
}

# Tower stats per level. range/size are in tiles, rate is shots per second.
# "sprites" lists one image per level in assets/towers/; a level without its own
# image reuses the last one.
TOWERS = {
    "arrow": {
        "name": "Arrow",
        "key": "1",
        "color": (90, 170, 90),
        "desc": "Fast single-target shots",
        "sprites": ["arrow_1", "arrow_2", "arrow_3"],
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
        "desc": "Slow, splash damage",
        "sprites": ["cannon_1", "cannon_2", "cannon_3"],
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
        "desc": "Slows enemies down",
        "sprites": ["frost_1", "frost_2", "frost_3"],
        "levels": [
            {"cost": 70, "damage": 4, "range": 2.2, "rate": 1.2, "slow": 0.5, "slow_time": 1.5},
            {"cost": 60, "damage": 7, "range": 2.5, "rate": 1.4, "slow": 0.4, "slow_time": 2.0},
            {"cost": 90, "damage": 11, "range": 2.8, "rate": 1.6, "slow": 0.3, "slow_time": 2.5},
        ],
    },
    "fire": {
        "name": "Fire",
        "key": "4",
        "color": (230, 110, 40),
        "desc": "Burns over time",
        "sprites": ["fire_1", "fire_2", "fire_3"],
        "levels": [
            {"cost": 80, "damage": 4, "range": 2.3, "rate": 1.0, "burn": 10, "burn_time": 3.0},
            {"cost": 70, "damage": 6, "range": 2.5, "rate": 1.1, "burn": 18, "burn_time": 3.0},
            {"cost": 110, "damage": 9, "range": 2.8, "rate": 1.2, "burn": 30, "burn_time": 3.5},
        ],
    },
    "arcane": {
        "name": "Arcane",
        "key": "5",
        "color": (160, 100, 220),
        "desc": "Long range, heavy hits",
        "sprites": ["arcane_1", "arcane_2", "arcane_3"],
        "levels": [
            {"cost": 100, "damage": 45, "range": 3.6, "rate": 0.5},
            {"cost": 90, "damage": 75, "range": 3.9, "rate": 0.55},
            {"cost": 140, "damage": 120, "range": 4.3, "rate": 0.6},
        ],
    },
    "lightning": {
        "name": "Lightning",
        "key": "6",
        "color": (120, 170, 255),
        "desc": "Chains between enemies",
        "sprites": ["lightning_1", "lightning_2"],
        # chain: extra enemies the bolt jumps to; chain_range in tiles between jumps
        "levels": [
            {"cost": 110, "damage": 14, "range": 2.6, "rate": 0.9, "chain": 3, "chain_range": 1.6},
            {"cost": 90, "damage": 22, "range": 2.8, "rate": 1.0, "chain": 4, "chain_range": 1.8},
            {"cost": 130, "damage": 34, "range": 3.0, "rate": 1.1, "chain": 5, "chain_range": 2.0},
        ],
    },
}

# speed in tiles per second; reward in gold; leak is lives lost if it gets through.
# Every faction has every kind: the sprite is assets/enemies/<faction>_<kind>.png,
# facing right (the game mirrors it when the enemy walks left).
# size is the sprite's height on screen in pixels.
ENEMIES = {
    "soldier": {"name": "Soldier", "hp": 40, "speed": 1.6, "reward": 6, "leak": 1,
                "radius": 11, "size": 38},
    "spearman": {"name": "Spearman", "hp": 60, "speed": 1.4, "reward": 7, "leak": 1,
                 "radius": 11, "size": 40},
    "archer": {"name": "Archer", "hp": 30, "speed": 2.0, "reward": 6, "leak": 1,
               "radius": 11, "size": 38},
    "cavalry": {"name": "Cavalry", "hp": 35, "speed": 3.0, "reward": 7, "leak": 1,
                "radius": 13, "size": 46},
    "special": {"name": "Elite", "hp": 180, "speed": 0.9, "reward": 18, "leak": 3,
                "radius": 14, "size": 46},
    "champion": {"name": "Champion", "hp": 900, "speed": 0.7, "reward": 80, "leak": 10,
                 "radius": 20, "size": 62},
}

# Each wave is one faction, in this order, repeating.
FACTIONS = ["human", "elf", "goblin", "skeleton"]
FACTION_NAMES = {"human": "Humans", "elf": "Elves", "goblin": "Goblins", "skeleton": "Skeletons"}


def wave_faction(n):
    return FACTIONS[(n - 1) % len(FACTIONS)]


def wave_plan(n):
    """Spawn list for wave n (1-based): [(enemy_kind, delay_before_spawn_s), ...]."""
    plan = [("soldier", 0.8)] * (5 + n)
    if n >= 2:
        plan += [("spearman", 0.9)] * (1 + n // 2)
        plan += [("cavalry", 0.45)] * (1 + n)
    if n >= 3:
        plan += [("archer", 0.6)] * (1 + n // 2)
    if n >= 4:
        plan += [("special", 1.6)] * (n // 2)
    plan += [("champion", 2.5)] * (n // 5)   # a champion every fifth wave
    return plan


def hp_scale(n):
    """Enemy HP multiplier for wave n, so later waves keep up with upgrades."""
    return 1.0 + 0.18 * (n - 1) + 0.012 * (n - 1) ** 2
