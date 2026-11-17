"""Paints the static map: pixel-art grass, the dirt road and the scenery."""

import os
import random

import pygame

from . import config as C

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

PX = 3  # size of one "art pixel" on screen, to match the scale of the sprites

# palettes sampled from the tileset's grass and dirt
GRASS = [(88, 125, 36), (91, 129, 38), (94, 132, 40), (86, 122, 35)]
GRASS_DARK = [(56, 84, 22), (64, 94, 26)]
GRASS_LIGHT = [(110, 148, 50), (118, 156, 56)]
FLOWERS = [(236, 236, 220), (240, 214, 90), (226, 150, 190)]
DIRT = [(191, 136, 64), (198, 143, 70), (203, 147, 75), (177, 123, 52), (211, 156, 84)]
PEBBLE = [(150, 104, 46), (222, 176, 104)]
WATER = [(30, 72, 84), (34, 80, 92), (26, 64, 76), (38, 88, 100)]   # from the bridge tile
RIPPLE = [(70, 130, 140), (90, 150, 160)]
BANK = [(52, 70, 40), (60, 80, 46), (96, 92, 80)]
RIVER_WIDTH = 0.9   # of a tile

ROAD_WIDTH = 0.62   # of a tile
RIM = 5             # px of bushy grass edge along the road


def _speckle(surf, rect, palette, rng, density=1.0):
    x0, y0, w, h = rect
    for y in range(y0, y0 + h, PX):
        for x in range(x0, x0 + w, PX):
            if density >= 1 or rng.random() < density:
                surf.fill(rng.choice(palette), (x, y, PX, PX))


def _road_mask(size, waypoints, width):
    """White-on-transparent mask of the road: thick lines with round joins."""
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pts = [(int(x), int(y)) for x, y in waypoints]
    for a, b in zip(pts, pts[1:]):
        pygame.draw.line(mask, (255, 255, 255, 255), a, b, width)
    for p in pts:
        pygame.draw.circle(mask, (255, 255, 255, 255), p, width // 2)
    return mask


def _masked(texture, mask):
    out = texture.copy()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def _load(name):
    return pygame.image.load(os.path.join(ASSETS, "map", name + ".png")).convert_alpha()


def _draw_decor(surf, name, col, row, w, h, cache):
    img = cache.get(name) or cache.setdefault(name, _load(name))
    box_w, box_h = w * C.TILE, h * C.TILE
    if name not in C.GROUND_DECOR:
        box_h = int(box_h * 1.3)          # tall things may reach into the row above
    k = min(box_w / img.get_width(), box_h / img.get_height())
    img = pygame.transform.smoothscale(
        img, (round(img.get_width() * k), round(img.get_height() * k)))
    bottom = ((col + w / 2) * C.TILE, (row + h) * C.TILE)
    surf.blit(img, img.get_rect(midbottom=(int(bottom[0]), int(bottom[1]))))


def build_map(game, seed=7):
    """The play area for game's map as one surface. Deterministic for a given seed."""
    m = C.MAPS[game.map_id]
    waypoints = game.waypoints
    rng = random.Random(seed)
    size = (C.COLS * C.TILE, C.ROWS * C.TILE)
    surf = pygame.Surface(size)

    # grass: noisy base, darker and lighter tufts, the odd flower
    _speckle(surf, (0, 0, *size), GRASS, rng)
    _speckle(surf, (0, 0, *size), GRASS_DARK, rng, 0.03)
    _speckle(surf, (0, 0, *size), GRASS_LIGHT, rng, 0.04)
    for _ in range(size[0] * size[1] // 5200):
        x = rng.randrange(0, size[0], PX)
        y = rng.randrange(0, size[1], PX)
        surf.fill(rng.choice(FLOWERS), (x, y, PX, PX))

    # river: stony bank, then water with ripples
    if "river" in m:
        river = [((c + 0.5) * C.TILE, (r + 0.5) * C.TILE) for c, r in m["river"]]
        rw = int(C.TILE * RIVER_WIDTH)
        bank = pygame.Surface(size, pygame.SRCALPHA)
        _speckle(bank, (0, 0, *size), BANK, rng)
        surf.blit(_masked(bank, _road_mask(size, river, rw + 8)), (0, 0))
        water = pygame.Surface(size, pygame.SRCALPHA)
        _speckle(water, (0, 0, *size), WATER, rng)
        _speckle(water, (0, 0, *size), RIPPLE, rng, 0.03)
        surf.blit(_masked(water, _road_mask(size, river, rw)), (0, 0))

    # road: dark bushy rim, then dirt with pebbles on top
    width = int(C.TILE * ROAD_WIDTH)
    rim = pygame.Surface(size, pygame.SRCALPHA)
    _speckle(rim, (0, 0, *size), GRASS_DARK + [(48, 72, 18)], rng)
    surf.blit(_masked(rim, _road_mask(size, waypoints, width + 2 * RIM)), (0, 0))
    dirt = pygame.Surface(size, pygame.SRCALPHA)
    _speckle(dirt, (0, 0, *size), DIRT, rng)
    _speckle(dirt, (0, 0, *size), PEBBLE, rng, 0.025)
    surf.blit(_masked(dirt, _road_mask(size, waypoints, width)), (0, 0))

    # bridges where the road crosses the river. The art's deck runs left-right over a
    # river flowing top-bottom; turn it for a river that runs sideways.
    cache = {}
    if game.bridges:
        img = _load("bridge")
        (c0, r0), (c1, r1) = m["river"][0], m["river"][1]
        if abs(c1 - c0) > abs(r1 - r0):
            img = pygame.transform.rotate(img, 90)
        side = int(C.TILE * 1.3)
        img = pygame.transform.smoothscale(img, (side, side))
        for c, r in game.bridges:
            surf.blit(img, img.get_rect(center=(int((c + 0.5) * C.TILE), int((r + 0.5) * C.TILE))))

    # scenery: flat ground pieces first, then the rest from back (top) to front
    decor = sorted(m["decor"], key=lambda d: (d[0] not in C.GROUND_DECOR, d[2] + d[4]))
    for name, col, row, w, h in decor:
        _draw_decor(surf, name, col, row, w, h, cache)
    return surf
