"""Game state and rules. No pygame here, so it can be tested headless."""

import math

from . import config as C


def tile_center(col, row):
    return ((col + 0.5) * C.TILE, (row + 0.5) * C.TILE)


def path_tiles(path):
    """Every grid tile the path passes through (on the map)."""
    tiles = set()
    for (c0, r0), (c1, r1) in zip(path, path[1:]):
        dc = (c1 > c0) - (c1 < c0)
        dr = (r1 > r0) - (r1 < r0)
        c, r = c0, r0
        while True:
            if 0 <= c < C.COLS and 0 <= r < C.ROWS:
                tiles.add((c, r))
            if (c, r) == (c1, r1):
                break
            c, r = c + dc, r + dr
    return tiles


class Enemy:
    def __init__(self, kind, waypoints, hp_mult):
        spec = C.ENEMIES[kind]
        self.kind = kind
        self.max_hp = spec["hp"] * hp_mult
        self.hp = self.max_hp
        self.speed = spec["speed"] * C.TILE
        self.reward = spec["reward"]
        self.leak = spec["leak"]
        self.radius = spec["radius"]
        self.color = spec["color"]
        self.waypoints = waypoints
        self.x, self.y = waypoints[0]
        self.next_wp = 1
        self.distance = 0.0      # how far along the path; towers target the leader
        self.slow = 1.0
        self.slow_left = 0.0
        self.alive = True
        self.leaked = False

    def apply_slow(self, factor, duration):
        if factor <= self.slow:
            self.slow = factor
            self.slow_left = max(self.slow_left, duration)

    def update(self, dt):
        if self.slow_left > 0:
            self.slow_left -= dt
            if self.slow_left <= 0:
                self.slow = 1.0
        step = self.speed * self.slow * dt
        while step > 0 and self.next_wp < len(self.waypoints):
            tx, ty = self.waypoints[self.next_wp]
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy)
            if d <= step:
                self.x, self.y = tx, ty
                self.distance += d
                step -= d
                self.next_wp += 1
            else:
                self.x += dx / d * step
                self.y += dy / d * step
                self.distance += step
                step = 0
        if self.next_wp >= len(self.waypoints):
            self.alive = False
            self.leaked = True


class Projectile:
    SPEED = 9 * C.TILE

    def __init__(self, tower, target):
        self.x, self.y = tower.x, tower.y
        self.target = target
        self.tx, self.ty = target.x, target.y
        self.kind = tower.kind
        self.stats = tower.stats
        self.alive = True

    def update(self, dt, game):
        if self.target.alive:
            self.tx, self.ty = self.target.x, self.target.y
        dx, dy = self.tx - self.x, self.ty - self.y
        d = math.hypot(dx, dy)
        step = self.SPEED * dt
        if d > step:
            self.x += dx / d * step
            self.y += dy / d * step
            return
        self.x, self.y = self.tx, self.ty
        self.alive = False
        s = self.stats
        if "splash" in s:
            r = s["splash"] * C.TILE
            for e in game.enemies:
                if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= r + e.radius:
                    game.damage(e, s["damage"])
            game.effects.append(Effect(self.x, self.y, r, 0.25, (255, 170, 80)))
        elif self.target.alive:
            game.damage(self.target, s["damage"])
            if "slow" in s:
                self.target.apply_slow(s["slow"], s["slow_time"])


class Tower:
    def __init__(self, kind, col, row):
        self.kind = kind
        self.col, self.row = col, row
        self.x, self.y = tile_center(col, row)
        self.level = 0
        self.spent = C.TOWERS[kind]["levels"][0]["cost"]
        self.cooldown = 0.0

    @property
    def stats(self):
        return C.TOWERS[self.kind]["levels"][self.level]

    @property
    def range_px(self):
        return self.stats["range"] * C.TILE

    def upgrade_cost(self):
        levels = C.TOWERS[self.kind]["levels"]
        if self.level + 1 >= len(levels):
            return None
        return levels[self.level + 1]["cost"]

    def sell_value(self):
        return int(self.spent * C.SELL_REFUND)

    def update(self, dt, game):
        self.cooldown -= dt
        if self.cooldown > 0:
            return
        r = self.range_px
        best = None
        for e in game.enemies:
            if e.alive and math.hypot(e.x - self.x, e.y - self.y) <= r + e.radius:
                if best is None or e.distance > best.distance:
                    best = e
        if best:
            game.projectiles.append(Projectile(self, best))
            self.cooldown = 1.0 / self.stats["rate"]


class Effect:
    """A short-lived expanding ring (explosions)."""

    def __init__(self, x, y, radius, duration, color):
        self.x, self.y, self.radius = x, y, radius
        self.duration = self.left = duration
        self.color = color

    @property
    def alive(self):
        return self.left > 0

    def update(self, dt):
        self.left -= dt


class Game:
    def __init__(self):
        self.waypoints = [tile_center(c, r) for c, r in C.PATH]
        self.path = path_tiles(C.PATH)
        self.reset()

    def reset(self):
        self.gold = C.START_GOLD
        self.lives = C.START_LIVES
        self.wave = 0
        self.towers = {}            # (col, row) -> Tower
        self.enemies = []
        self.projectiles = []
        self.effects = []
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.kills = 0
        self.over = False
        self.message = "Place towers, then press SPACE to send wave 1."

    # --- queries --------------------------------------------------------
    @property
    def wave_active(self):
        return bool(self.spawn_queue) or bool(self.enemies)

    def can_build(self, col, row):
        return (0 <= col < C.COLS and 0 <= row < C.ROWS
                and (col, row) not in self.path and (col, row) not in self.towers)

    # --- player actions -------------------------------------------------
    def build(self, kind, col, row):
        cost = C.TOWERS[kind]["levels"][0]["cost"]
        if self.over or not self.can_build(col, row):
            return False
        if self.gold < cost:
            self.message = f"Not enough gold for {C.TOWERS[kind]['name']} ({cost})."
            return False
        self.gold -= cost
        self.towers[(col, row)] = Tower(kind, col, row)
        return True

    def upgrade(self, tower):
        cost = tower.upgrade_cost()
        if cost is None or self.over:
            return False
        if self.gold < cost:
            self.message = f"Upgrade costs {cost} gold."
            return False
        self.gold -= cost
        tower.spent += cost
        tower.level += 1
        return True

    def sell(self, tower):
        if self.over:
            return
        self.gold += tower.sell_value()
        del self.towers[(tower.col, tower.row)]

    def start_wave(self):
        if self.over or self.wave_active:
            return False
        self.wave += 1
        self.spawn_queue = list(C.wave_plan(self.wave))
        self.spawn_timer = 0.0
        self.message = f"Wave {self.wave}!"
        return True

    # --- simulation -----------------------------------------------------
    def damage(self, enemy, amount):
        if not enemy.alive:
            return
        enemy.hp -= amount
        if enemy.hp <= 0:
            enemy.alive = False
            self.gold += enemy.reward
            self.kills += 1

    def update(self, dt):
        if self.over:
            return
        if self.spawn_queue:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                kind, delay = self.spawn_queue.pop(0)
                self.enemies.append(Enemy(kind, self.waypoints, C.hp_scale(self.wave)))
                self.spawn_timer = delay

        had_enemies = self.wave_active
        for e in self.enemies:
            e.update(dt)
            if e.leaked:
                self.lives -= e.leak
        for t in self.towers.values():
            t.update(dt, self)
        for p in self.projectiles:
            p.update(dt, self)
        for fx in self.effects:
            fx.update(dt)

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.effects = [fx for fx in self.effects if fx.alive]

        if self.lives <= 0:
            self.lives = 0
            self.over = True
            self.message = f"Game over on wave {self.wave}. Press R to restart."
        elif had_enemies and not self.wave_active:
            bonus = C.WAVE_BONUS + 2 * self.wave
            self.gold += bonus
            self.message = f"Wave {self.wave} cleared! +{bonus} gold. SPACE for the next."
