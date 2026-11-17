"""pygame front end: drawing and input."""

import math
import os
import random

import pygame

from . import config as C
from .game import Bolt, Game
from .mapart import build_map

BG = (34, 52, 38)
PANEL = (28, 30, 36)
TEXT = (232, 232, 232)
MUTED = (150, 154, 164)
GOLD = (240, 200, 80)
RED = (220, 80, 80)
GOOD = (120, 210, 120)

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SPRITE_BOX = 62     # tower sprites are scaled to fit this square (a tile is 48)
# effects in assets/fx/: <name>_<frame>.png. Bullets are one frame and fly to the
# left in the art; sizes are the longest side in pixels after scaling.
SHOT_SIZE = {"arrow": 22, "arcane": 22, "fire": 22, "frost": 22, "cannon": 34}
HIT_SIZE = {"arrow": 46, "arcane": 50, "fire": 46, "frost": 50, "lightning": 56, "cannon": 70}
BURN_SIZE = 30
FX_FPS = 24
ICON_BOX = 34       # sidebar button icons
THUMB_W, THUMB_H = 340, 221   # map previews on the menu


class Button:
    def __init__(self, rect, label, action, sub=""):
        self.rect = pygame.Rect(rect)
        self.label, self.action, self.sub = label, action, sub
        self.enabled = True
        self.active = False
        self.icon = None


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tower Defense")
        self.screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans,liberationsans,arial", 16)
        self.small = pygame.font.SysFont("dejavusans,liberationsans,arial", 13)
        self.big = pygame.font.SysFont("dejavusans,liberationsans,arial", 34, bold=True)
        self.mode = "menu"         # "menu" (pick map and difficulty) or "play"
        self.menu_map, self.menu_diff = "village", "normal"
        self.maps = {m: build_map(Game(m)) for m in C.MAPS}   # painted once each
        self.thumbs = {m: pygame.transform.smoothscale(img, (THUMB_W, THUMB_H))
                       for m, img in self.maps.items()}
        self.clock_t = 0.0         # seconds of game time, for looping effects
        self.anims = []            # playing hit animations: [frames, x, y, age]
        self.start_game()
        self.mode = "menu"
        self.sprites, self.icons = self._load_sprites()
        self.enemy_sprites = self._load_enemy_sprites()
        self._rotated = {}         # (key, angle) -> rotated sprite
        self.shots, self.hit_frames, self.burn_frames = self._load_fx()

    def start_game(self):
        self.game = Game(self.menu_map, self.menu_diff)
        self.map_surface = self.maps[self.menu_map]
        self.build_kind = None     # tower kind being placed
        self.selected = None       # Tower whose info panel is open
        self.speed, self.paused = 1, False
        self.anims.clear()
        self.mode = "play"

    def _load_fx(self):
        def frames(name):
            out, i = [], 0
            while os.path.exists(path := os.path.join(ASSETS, "fx", f"{name}_{i}.png")):
                out.append(pygame.image.load(path).convert_alpha())
                i += 1
            return out

        def scale_all(imgs, size):
            # one factor for the whole animation so frames keep their relative size
            k = size / max(max(i.get_width(), i.get_height()) for i in imgs)
            return [pygame.transform.smoothscale(
                i, (max(1, round(i.get_width() * k)), max(1, round(i.get_height() * k))))
                for i in imgs]

        shots = {k: scale_all(frames(k + "_shot"), n)[0] for k, n in SHOT_SIZE.items()}
        hits = {k: scale_all(frames(k + "_hit"), n) for k, n in HIT_SIZE.items()}
        return shots, hits, scale_all(frames("burn"), BURN_SIZE)

    def rotated(self, key, img, angle):
        """img turned by `angle` degrees counter-clockwise, cached in 5-degree steps."""
        angle = round(angle / 5) * 5 % 360
        k = (key, angle)
        out = self._rotated.get(k)
        if out is None:
            out = self._rotated[k] = pygame.transform.rotate(img, angle)
        return out

    def _load_enemy_sprites(self):
        """(faction, kind) -> (facing right, facing left) sprites, scaled."""
        out = {}
        for faction in C.FACTIONS:
            for kind, spec in C.ENEMIES.items():
                path = os.path.join(ASSETS, "enemies", f"{faction}_{kind}.png")
                img = pygame.image.load(path).convert_alpha()
                k = spec["size"] / img.get_height()
                img = pygame.transform.smoothscale(img, (round(img.get_width() * k), spec["size"]))
                out[(faction, kind)] = (img, pygame.transform.flip(img, True, False))
        return out

    def enemy_image(self, e):
        right, left = self.enemy_sprites[(e.faction, e.kind)]
        return right if e.facing > 0 else left

    def _load_sprites(self):
        """Per tower kind: one map sprite per level, plus a sidebar icon."""
        def fit(img, box):
            k = box / max(img.get_width(), img.get_height())
            return pygame.transform.smoothscale(
                img, (round(img.get_width() * k), round(img.get_height() * k)))

        sprites, icons = {}, {}
        for kind, spec in C.TOWERS.items():
            imgs = [pygame.image.load(os.path.join(ASSETS, "towers", n + ".png")).convert_alpha()
                    for n in spec["sprites"]]
            per_level = [imgs[min(i, len(imgs) - 1)] for i in range(len(spec["levels"]))]
            sprites[kind] = [fit(img, SPRITE_BOX) for img in per_level]
            icons[kind] = fit(imgs[0], ICON_BOX)
        return sprites, icons

    # --- input ----------------------------------------------------------
    def buttons(self):
        g = self.game
        x0 = C.COLS * C.TILE + 14
        w = C.SIDEBAR_W - 28
        out = []
        y = 112
        half = (w - 6) // 2
        for i, (kind, spec) in enumerate(C.TOWERS.items()):   # two-column grid
            cost = spec["levels"][0]["cost"]
            bx = x0 + (i % 2) * (half + 6)
            by = y + (i // 2) * 58
            b = Button((bx, by, half, 54), spec["name"], ("pick", kind),
                       f"[{spec['key']}]  {cost}g")
            b.icon = kind
            b.enabled = not g.over
            b.active = self.build_kind == kind
            out.append(b)
        y += (len(C.TOWERS) + 1) // 2 * 58 + 4
        label = "[Space] Send next wave"
        if g.wave < C.TOTAL_WAVES and not g.over:
            next_wave = g.wave + 1
            faction = C.FACTION_NAMES[C.wave_faction(next_wave)]
            label = f"[Space] {next_wave}: {faction} ({len(C.wave_plan(next_wave))})"
        wave = Button((x0, y, w, 34), label, ("wave",))
        wave.enabled = not g.wave_active and not g.over
        out.append(wave)
        y += 40
        third = (w - 12) // 3
        sp = Button((x0, y, third, 28), f"[F] x{self.speed}", ("speed",))
        sp.active = self.speed > 1
        pa = Button((x0 + third + 6, y, third, 28), "[P] Pause", ("pause",))
        pa.active = self.paused
        mn = Button((x0 + 2 * (third + 6), y, third, 28), "[M] Menu", ("menu",))
        out += [sp, pa, mn]

        t = self.selected
        if t:
            y = 456
            cost = t.upgrade_cost()
            up = Button((x0, y, w, 32),
                        f"[U] Upgrade  {cost}g" if cost else "Max level", ("upgrade",))
            up.enabled = cost is not None and g.gold >= cost and not g.over
            sell = Button((x0, y + 37, w, 28), f"[S] Sell  +{t.sell_value()}g", ("sell",))
            sell.enabled = not g.over
            out += [up, sell]
        return out

    def do(self, action):
        g = self.game
        name = action[0]
        if name == "pick":
            self.build_kind = None if self.build_kind == action[1] else action[1]
            self.selected = None
        elif name == "wave":
            g.start_wave()
        elif name == "speed":
            self.speed = 2 if self.speed == 1 else 1
        elif name == "pause":
            self.paused = not self.paused
        elif name == "menu":
            self.mode = "menu"
        elif name == "map":
            self.menu_map = action[1]
        elif name == "difficulty":
            self.menu_diff = action[1]
        elif name == "start":
            self.start_game()
        elif name == "upgrade" and self.selected:
            g.upgrade(self.selected)
        elif name == "sell" and self.selected:
            g.sell(self.selected)
            self.selected = None

    def replay_button(self):
        x, y = C.COLS * C.TILE // 2, C.HEIGHT // 2
        return Button((x - 90, y + 42, 180, 36), "[R] Play again", ("replay",))

    def replay(self):
        self.menu_map, self.menu_diff = self.game.map_id, self.game.difficulty
        self.start_game()

    def menu_buttons(self):
        out = []
        gap = 30
        x = (C.WIDTH - 3 * THUMB_W - 2 * gap) // 2
        for i, (m, spec) in enumerate(C.MAPS.items()):
            b = Button((x + i * (THUMB_W + gap), 130, THUMB_W, THUMB_H + 34), spec["name"], ("map", m))
            b.active = self.menu_map == m
            out.append(b)
        bw, bg = 220, 20
        x = (C.WIDTH - 3 * bw - 2 * bg) // 2
        for i, (d, spec) in enumerate(C.DIFFICULTIES.items()):
            sub = f"Enemy HP x{spec['hp']:g}   Speed x{spec['speed']:g}"
            b = Button((x + i * (bw + bg), 436, bw, 58), spec["name"], ("difficulty", d), sub)
            b.active = self.menu_diff == d
            out.append(b)
        out.append(Button(((C.WIDTH - 260) // 2, 528, 260, 50), "Start  [Enter]", ("start",)))
        return out

    def on_click(self, pos, button):
        if self.mode == "menu":
            for b in self.menu_buttons():
                if button == 1 and b.rect.collidepoint(pos):
                    self.do(b.action)
            return
        if self.game.over and self.replay_button().rect.collidepoint(pos):
            if button == 1:
                self.replay()
            return
        if button == 3:                       # right click cancels
            self.build_kind = self.selected = None
            return
        for b in self.buttons():
            if b.rect.collidepoint(pos):
                if b.enabled:
                    self.do(b.action)
                return
        col, row = pos[0] // C.TILE, pos[1] // C.TILE
        if col >= C.COLS:
            return
        tower = self.game.towers.get((col, row))
        if tower:
            self.selected = tower
            self.build_kind = None
        elif self.build_kind:
            if self.game.build(self.build_kind, col, row):
                # keep placing with shift held, otherwise drop out of build mode
                if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.build_kind = None
        else:
            self.selected = None

    def on_key(self, key):
        if self.mode == "menu":
            maps, diffs = list(C.MAPS), list(C.DIFFICULTIES)
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                i = maps.index(self.menu_map) + (1 if key == pygame.K_RIGHT else -1)
                self.menu_map = maps[i % len(maps)]
            elif key in (pygame.K_UP, pygame.K_DOWN):
                i = diffs.index(self.menu_diff) + (1 if key == pygame.K_DOWN else -1)
                self.menu_diff = diffs[i % len(diffs)]
            return
        g = self.game
        for kind, spec in C.TOWERS.items():
            if key == pygame.key.key_code(spec["key"]):
                self.do(("pick", kind))
                return
        if key == pygame.K_SPACE:
            g.start_wave()
        elif key == pygame.K_f:
            self.do(("speed",))
        elif key == pygame.K_p:
            self.do(("pause",))
        elif key == pygame.K_u:
            self.do(("upgrade",))
        elif key == pygame.K_s:
            self.do(("sell",))
        elif key == pygame.K_ESCAPE:
            self.build_kind = self.selected = None
        elif key == pygame.K_m:
            self.mode = "menu"
        elif key == pygame.K_r and g.over:
            self.replay()

    # --- drawing --------------------------------------------------------
    def text(self, s, pos, font=None, color=TEXT, center=False):
        img = (font or self.font).render(s, True, color)
        rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        self.screen.blit(img, rect)

    def draw_tower(self, t):
        x, y = int(t.x), int(t.y)
        img = self.sprites[t.kind][t.level]
        # stand the sprite on the bottom of its tile; tall ones reach into the tile above
        self.screen.blit(img, img.get_rect(midbottom=(x, y + C.TILE // 2 - 1)))
        for i in range(t.level):            # upgrade pips
            pygame.draw.circle(self.screen, (20, 20, 20), (x - 17 + i * 9, y + 17), 4)
            pygame.draw.circle(self.screen, GOLD, (x - 17 + i * 9, y + 17), 3)

    def draw_menu(self):
        scr = self.screen
        scr.fill((24, 30, 26))
        self.text("Tower Defense", (C.WIDTH // 2, 52), self.big, GOLD, center=True)
        self.text("Choose a map", (C.WIDTH // 2, 104), color=MUTED, center=True)
        self.text("Difficulty", (C.WIDTH // 2, 412), color=MUTED, center=True)
        for b in self.menu_buttons():
            kind = b.action[0]
            if kind == "map":
                border = GOLD if b.active else (70, 76, 86)
                scr.blit(self.thumbs[b.action[1]], b.rect.topleft)
                pygame.draw.rect(scr, border, b.rect.inflate(6, 6), 3, border_radius=6)
                self.text(b.label, (b.rect.centerx, b.rect.bottom - 16),
                          color=TEXT if b.active else MUTED, center=True)
                continue
            bg = (70, 90, 130) if b.active else (52, 56, 66)
            if kind == "start":
                bg = (60, 120, 70)
            pygame.draw.rect(scr, bg, b.rect, border_radius=8)
            pygame.draw.rect(scr, (90, 96, 110), b.rect, 1, border_radius=8)
            if b.sub:
                self.text(b.label, (b.rect.centerx, b.rect.y + 18), center=True)
                self.text(b.sub, (b.rect.centerx, b.rect.y + 40), self.small, MUTED, center=True)
            else:
                self.text(b.label, b.rect.center, center=True)
        self.text("Arrow keys: change map / difficulty", (C.WIDTH // 2, C.HEIGHT - 22),
                  self.small, MUTED, center=True)
        pygame.display.flip()

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
            return
        g = self.game
        scr = self.screen
        scr.fill(BG)
        scr.blit(self.map_surface, (0, 0))

        mouse = pygame.mouse.get_pos()
        mcol, mrow = mouse[0] // C.TILE, mouse[1] // C.TILE

        overlay = pygame.Surface((C.COLS * C.TILE, C.ROWS * C.TILE), pygame.SRCALPHA)
        if self.selected:
            t = self.selected
            pygame.draw.circle(overlay, (255, 255, 255, 40), (int(t.x), int(t.y)), int(t.range_px))
            pygame.draw.circle(overlay, (255, 255, 255, 120), (int(t.x), int(t.y)), int(t.range_px), 2)
        if self.build_kind:
            for c in range(C.COLS):
                for r in range(C.ROWS):
                    if g.can_build(c, r):
                        pygame.draw.rect(overlay, (255, 255, 255, 28),
                                         (c * C.TILE, r * C.TILE, C.TILE, C.TILE), 1)
        if self.build_kind and mcol < C.COLS:
            ok = g.can_build(mcol, mrow)
            cx, cy = (mcol + 0.5) * C.TILE, (mrow + 0.5) * C.TILE
            col = (120, 255, 120) if ok else (255, 90, 90)
            pygame.draw.rect(overlay, (*col, 70), (mcol * C.TILE, mrow * C.TILE, C.TILE, C.TILE))
            rng = C.TOWERS[self.build_kind]["levels"][0]["range"] * C.TILE
            pygame.draw.circle(overlay, (*col, 35), (int(cx), int(cy)), int(rng))
            pygame.draw.circle(overlay, (*col, 120), (int(cx), int(cy)), int(rng), 2)
        scr.blit(overlay, (0, 0))

        # draw top rows first so a tower's sprite overlaps the one behind it
        for t in sorted(g.towers.values(), key=lambda t: t.row):
            self.draw_tower(t)
        if self.build_kind and mcol < C.COLS and g.can_build(mcol, mrow):
            ghost = self.sprites[self.build_kind][0].copy()
            ghost.set_alpha(150)
            cx, cy = int((mcol + 0.5) * C.TILE), int((mrow + 1) * C.TILE - 1)
            scr.blit(ghost, ghost.get_rect(midbottom=(cx, cy)))

        for e in g.enemies:
            x, y = int(e.x), int(e.y)
            half = C.ENEMIES[e.kind]["size"] // 2
            img = self.enemy_image(e)
            scr.blit(img, img.get_rect(center=(x, y - 4)))
            if e.slow < 1:
                pygame.draw.circle(scr, (140, 200, 255), (x, y), half + 2, 2)
            if e.burn_left > 0:
                flame = self.burn_frames[int(self.clock_t * 12 + id(e) % 4) % len(self.burn_frames)]
                scr.blit(flame, flame.get_rect(midbottom=(x, y + 6)))
            w = half * 2
            frac = max(0.0, e.hp / e.max_hp)
            pygame.draw.rect(scr, (40, 0, 0), (x - w // 2, y - half - 12, w, 4))
            pygame.draw.rect(scr, GOOD, (x - w // 2, y - half - 12, int(w * frac), 4))

        for p in g.projectiles:
            img = self.shots.get(p.kind)
            if img is None:                    # lightning: a small glowing spark
                pygame.draw.circle(scr, (120, 170, 255), (int(p.x), int(p.y)), 5)
                pygame.draw.circle(scr, (235, 245, 255), (int(p.x), int(p.y)), 3)
                continue
            # the art flies left (180 degrees); pygame turns counter-clockwise
            angle = math.degrees(math.atan2(p.heading[1], p.heading[0]))
            img = self.rotated(("shot", p.kind), img, 180 - angle)
            scr.blit(img, img.get_rect(center=(int(p.x), int(p.y))))

        for frames, x, y, age in self.anims:
            img = frames[min(int(age * FX_FPS), len(frames) - 1)]
            scr.blit(img, img.get_rect(center=(int(x), int(y))))

        for fx in g.effects:
            if isinstance(fx, Bolt):
                self.draw_bolt(fx)
                continue
            k = 1 - fx.left / fx.duration
            pygame.draw.circle(scr, fx.color, (int(fx.x), int(fx.y)),
                               max(1, int(fx.radius * (0.3 + 0.7 * k))), 3)

        self.draw_sidebar()

        if g.over or self.paused:
            shade = pygame.Surface((C.COLS * C.TILE, C.ROWS * C.TILE), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            scr.blit(shade, (0, 0))
            mid = (C.COLS * C.TILE // 2, C.ROWS * C.TILE // 2)
            if g.over:
                title, color = ("VICTORY", GOLD) if g.victory else ("DEFEAT", RED)
                self.text(title, (mid[0], mid[1] - 24), self.big, color, center=True)
                self.text(f"You reached wave {g.wave} with {g.kills} kills.",
                          (mid[0], mid[1] + 18), center=True)
                replay = self.replay_button()
                pygame.draw.rect(scr, PANEL, replay.rect, border_radius=6)
                self.text(replay.label, replay.rect.center, center=True)
                self.text("[M] Menu", (mid[0], mid[1] + 94), center=True)
            else:
                self.text("PAUSED", mid, self.big, center=True)

        pygame.display.flip()

    def draw_bolt(self, fx):
        """Jagged lightning through the bolt's points, re-jittered every frame."""
        pts = []
        for (x0, y0), (x1, y1) in zip(fx.points, fx.points[1:]):
            for i in range(4):
                t = i / 4
                j = 0 if i == 0 else 6
                pts.append((x0 + (x1 - x0) * t + random.uniform(-j, j),
                            y0 + (y1 - y0) * t + random.uniform(-j, j)))
        pts.append(fx.points[-1])
        if len(pts) < 2:
            pygame.draw.circle(self.screen, (200, 225, 255), [int(v) for v in pts[0]], 8, 2)
            return
        pygame.draw.lines(self.screen, (120, 170, 255), False, pts, 5)
        pygame.draw.lines(self.screen, (235, 245, 255), False, pts, 2)

    def draw_sidebar(self):
        g = self.game
        x0 = C.COLS * C.TILE
        pygame.draw.rect(self.screen, PANEL, (x0, 0, C.SIDEBAR_W, C.HEIGHT))
        x = x0 + 14
        self.text(f"Gold  {g.gold}", (x, 12), color=GOLD)
        self.text(f"Lives {g.lives}", (x + 130, 12), color=RED if g.lives <= 5 else TEXT)
        self.text(f"Wave  {g.wave}/{C.TOTAL_WAVES}", (x, 36))
        self.text(f"Kills {g.kills}", (x + 130, 36))
        where = f"{C.MAPS[g.map_id]['name']} · {C.DIFFICULTIES[g.difficulty]['name']}"
        self.text(where, (x, 60), self.small, MUTED)
        self.text("Build", (x, 88), color=MUTED)

        for b in self.buttons():
            bg = (70, 90, 130) if b.active else (52, 56, 66) if b.enabled else (40, 42, 48)
            pygame.draw.rect(self.screen, bg, b.rect, border_radius=6)
            pygame.draw.rect(self.screen, (90, 96, 110), b.rect, 1, border_radius=6)
            color = TEXT if b.enabled else MUTED
            if b.icon:
                icon = self.icons[b.icon]
                if not b.enabled:
                    icon = icon.copy()
                    icon.set_alpha(110)
                self.screen.blit(icon, icon.get_rect(center=(b.rect.x + 21, b.rect.centery)))
                room = b.rect.right - (b.rect.x + 40) - 4
                font = self.font if self.font.size(b.label)[0] <= room else self.small
                self.text(b.label, (b.rect.x + 40, b.rect.y + 9), font, color)
                self.text(b.sub, (b.rect.x + 40, b.rect.y + 30), self.small,
                          GOLD if b.enabled else MUTED)
            elif b.sub:
                self.text(b.label, (b.rect.x + 10, b.rect.y + 5), color=color)
                self.text(b.sub, (b.rect.x + 10, b.rect.y + 25), self.small, MUTED)
            else:
                self.text(b.label, b.rect.center, self.small, color, center=True)

        t = self.selected
        if t or self.build_kind:
            kind = t.kind if t else self.build_kind
            spec = C.TOWERS[kind]
            s = t.stats if t else spec["levels"][0]
            y = 392
            title = f"{spec['name']}  (level {t.level + 1})" if t else f"{spec['name']}: {spec['desc']}"
            self.text(title, (x, y), self.font if self.font.size(title)[0] <= C.SIDEBAR_W - 28 else self.small)
            line = f"Dmg {s['damage']}  Range {s['range']}  Rate {s['rate']}/s"
            self.text(line, (x, y + 24), self.small, MUTED)
            extra = ""
            if "splash" in s:
                extra = f"Splash radius {s['splash']} tiles"
            elif "slow" in s:
                extra = f"Slows to {int(s['slow'] * 100)}% for {s['slow_time']}s"
            elif "burn" in s:
                extra = f"Burns {s['burn']}/s for {s['burn_time']}s"
            elif "chain" in s:
                extra = f"Jumps to {s['chain']} more enemies"
            self.text(extra, (x, y + 42), self.small, MUTED)

        # message line and help at the bottom
        message = g.message
        if self.build_kind and not g.over:
            cost = C.TOWERS[self.build_kind]["levels"][0]["cost"]
            if cost > g.gold:
                message = f"Need {cost} gold to build. You have {g.gold}."
        self.wrap(message, (x, C.HEIGHT - 98), C.SIDEBAR_W - 28, TEXT)
        self.text("Click: place or select a tower", (x, C.HEIGHT - 58), self.small, MUTED)
        self.text("Shift+click: place several", (x, C.HEIGHT - 40), self.small, MUTED)
        self.text("Right-click / Esc: cancel", (x, C.HEIGHT - 22), self.small, MUTED)

    def wrap(self, s, pos, width, color):
        words, line, y = s.split(), "", pos[1]
        for w in words:
            trial = (line + " " + w).strip()
            if self.small.size(trial)[0] > width:
                self.text(line, (pos[0], y), self.small, color)
                y += 17
                line = w
            else:
                line = trial
        if line:
            self.text(line, (pos[0], y), self.small, color)

    # --- loop -----------------------------------------------------------
    def run(self):
        while True:
            dt = min(self.clock.tick(C.FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    self.on_click(ev.pos, ev.button)
                elif ev.type == pygame.KEYDOWN:
                    self.on_key(ev.key)
            if self.selected and (self.selected.col, self.selected.row) not in self.game.towers:
                self.selected = None
            if self.mode == "play" and not self.paused:
                for _ in range(self.speed):
                    self.step(dt)
            self.draw()

    def step(self, dt):
        """Advance the game and the hit animations by dt seconds."""
        self.game.update(dt)
        self.clock_t += dt
        for kind, x, y in self.game.hits:
            frames = self.hit_frames.get(kind)
            if frames:
                self.anims.append([frames, x, y, 0.0])
        self.game.hits.clear()
        for a in self.anims:
            a[3] += dt
        self.anims = [a for a in self.anims if a[3] * FX_FPS < len(a[0])]


def main():
    App().run()


if __name__ == "__main__":
    main()
