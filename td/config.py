"""Display settings and the shared campaign configuration."""

from pathlib import Path

from .level import load_level

TILE = 48
SIDEBAR_W = 260
FPS = 60
LEVEL_FILE = Path(__file__).with_name("data") / "campaign.json"
_level = load_level(LEVEL_FILE)
COLS, ROWS = _level["board"]["cols"], _level["board"]["rows"]
WIDTH, HEIGHT = COLS * TILE + SIDEBAR_W, ROWS * TILE
START_GOLD = _level["economy"]["start_gold"]
START_LIVES = _level["economy"]["start_lives"]
SELL_REFUND = _level["economy"]["sell_refund"]
WAVE_BONUS = _level["economy"]["wave_bonus"]
MAPS = _level["maps"]
GROUND_DECOR = set(_level["ground_decor"])
DIFFICULTIES = _level["difficulties"]
TOWERS = _level["towers"]
ENEMIES = _level["enemies"]
FACTION_NAMES = _level["factions"]
FACTIONS = list(FACTION_NAMES)
CAMPAIGN = _level["waves"]
TOTAL_WAVES = len(CAMPAIGN)


def _wave(n):
    if not 1 <= n <= TOTAL_WAVES:
        raise ValueError(f"Wave must be between 1 and {TOTAL_WAVES}")
    return CAMPAIGN[n - 1]


def wave_faction(n):
    return _wave(n)["faction"]


def wave_plan(n):
    """Return (enemy ID, seconds after spawn) pairs for a 1-based wave."""
    return [(group["enemy"], group["delay"]) for group in _wave(n)["groups"]
            for _ in range(group["count"])]


def hp_scale(n):
    return _wave(n)["hp_multiplier"]
