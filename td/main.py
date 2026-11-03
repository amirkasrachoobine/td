"""pygame front end: drawing and input."""

import math

import pygame

from . import config as C
from .game import Game

BG = (34, 52, 38)
GRASS_A = (52, 84, 56)
GRASS_B = (48, 78, 52)
PATH_COLOR = (150, 128, 92)
PANEL = (28, 30, 36)
TEXT = (232, 232, 232)
MUTED = (150, 154, 164)
GOLD = (240, 200, 80)
RED = (220, 80, 80)
GOOD = (120, 210, 120)


class Button:
    def __init__(self, rect, label, action, sub=""):
        self.rect = pygame.Rect(rect)
        self.label, self.action, self.sub = label, action, sub
        self.enabled = True
        self.active = False


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tower Defense")
        self.screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans,liberationsans,arial", 16)
        self.small = pygame.font.SysFont("dejavusans,liberationsans,arial", 13)
        self.big = pygame.font.SysFont("dejavusans,liberationsans,arial", 34, bold=True)
        self.game = Game()
        self.build_kind = None     # tower kind being placed
        self.selected = None       # Tower whose info panel is open
        self.speed = 1
        self.paused = False
        self.map_surface = self._draw_map()

    # --- input ----------------------------------------------------------
    def buttons(self):
        g = self.game
        x0 = C.COLS * C.TILE + 14
        w = C.SIDEBAR_W - 28
        out = []
        y = 112
        for kind, spec in C.TOWERS.items():
            cost = spec["levels"][0]["cost"]
            b = Button((x0, y, w, 46), f"[{spec['key']}] {spec['name']}  {cost}g",
                       ("pick", kind), spec["desc"])
            b.enabled = g.gold >= cost and not g.over
            b.active = self.build_kind == kind
            out.append(b)
            y += 52
        y += 6
        wave = Button((x0, y, w, 36), "[Space] Send next wave", ("wave",))
        wave.enabled = not g.wave_active and not g.over
        out.append(wave)
        y += 42
        half = (w - 8) // 2
        sp = Button((x0, y, half, 30), f"[F] Speed x{self.speed}", ("speed",))
        sp.active = self.speed > 1
        pa = Button((x0 + half + 8, y, half, 30), "[P] Pause", ("pause",))
        pa.active = self.paused
        out += [sp, pa]

        t = self.selected
        if t:
            y = 424
            cost = t.upgrade_cost()
            up = Button((x0, y, w, 34),
                        f"[U] Upgrade  {cost}g" if cost else "Max level", ("upgrade",))
            up.enabled = cost is not None and g.gold >= cost and not g.over
            sell = Button((x0, y + 40, w, 30), f"[S] Sell  +{t.sell_value()}g", ("sell",))
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
        elif name == "upgrade" and self.selected:
            g.upgrade(self.selected)
        elif name == "sell" and self.selected:
            g.sell(self.selected)
            self.selected = None

    def on_click(self, pos, button):
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
        elif key == pygame.K_r and g.over:
            g.reset()
            self.build_kind = self.selected = None
            self.speed, self.paused = 1, False

    # --- drawing --------------------------------------------------------
    def _draw_map(self):
        surf = pygame.Surface((C.COLS * C.TILE, C.ROWS * C.TILE))
        for c in range(C.COLS):
            for r in range(C.ROWS):
                color = PATH_COLOR if (c, r) in self.game.path else (
                    GRASS_A if (c + r) % 2 == 0 else GRASS_B)
                pygame.draw.rect(surf, color, (c * C.TILE, r * C.TILE, C.TILE, C.TILE))
        pts = [(int(x), int(y)) for x, y in self.game.waypoints]
        pygame.draw.lines(surf, (128, 108, 78), False, pts, 4)
        return surf

    def text(self, s, pos, font=None, color=TEXT, center=False):
        img = (font or self.font).render(s, True, color)
        rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        self.screen.blit(img, rect)

    def draw_tower(self, t, alpha_surface=None):
        spec = C.TOWERS[t.kind]
        x, y = int(t.x), int(t.y)
        pygame.draw.rect(self.screen, (60, 60, 66), (x - 19, y - 19, 38, 38), border_radius=6)
        pygame.draw.circle(self.screen, spec["color"], (x, y), 14)
        pygame.draw.circle(self.screen, (20, 20, 20), (x, y), 14, 2)
        for i in range(t.level):            # upgrade pips
            pygame.draw.circle(self.screen, GOLD, (x - 12 + i * 8, y + 15), 3)

    def draw(self):
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
        if self.build_kind and mcol < C.COLS:
            ok = g.can_build(mcol, mrow)
            cx, cy = (mcol + 0.5) * C.TILE, (mrow + 0.5) * C.TILE
            col = (120, 255, 120) if ok else (255, 90, 90)
            pygame.draw.rect(overlay, (*col, 70), (mcol * C.TILE, mrow * C.TILE, C.TILE, C.TILE))
            rng = C.TOWERS[self.build_kind]["levels"][0]["range"] * C.TILE
            pygame.draw.circle(overlay, (*col, 35), (int(cx), int(cy)), int(rng))
            pygame.draw.circle(overlay, (*col, 120), (int(cx), int(cy)), int(rng), 2)
        scr.blit(overlay, (0, 0))

        for t in g.towers.values():
            self.draw_tower(t)

        for e in g.enemies:
            x, y = int(e.x), int(e.y)
            pygame.draw.circle(scr, e.color, (x, y), e.radius)
            pygame.draw.circle(scr, (20, 20, 20), (x, y), e.radius, 2)
            if e.slow < 1:
                pygame.draw.circle(scr, (140, 200, 255), (x, y), e.radius + 3, 2)
            w = e.radius * 2 + 4
            frac = max(0.0, e.hp / e.max_hp)
            pygame.draw.rect(scr, (40, 0, 0), (x - w // 2, y - e.radius - 9, w, 4))
            pygame.draw.rect(scr, GOOD, (x - w // 2, y - e.radius - 9, int(w * frac), 4))

        for p in g.projectiles:
            color = {"arrow": (240, 240, 200), "cannon": (40, 40, 40),
                     "frost": (170, 220, 255)}[p.kind]
            pygame.draw.circle(scr, color, (int(p.x), int(p.y)), 5 if p.kind == "cannon" else 3)

        for fx in g.effects:
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
                self.text("GAME OVER", (mid[0], mid[1] - 24), self.big, RED, center=True)
                self.text(f"You reached wave {g.wave} with {g.kills} kills. Press R to restart.",
                          (mid[0], mid[1] + 18), center=True)
            else:
                self.text("PAUSED", mid, self.big, center=True)

        pygame.display.flip()

    def draw_sidebar(self):
        g = self.game
        x0 = C.COLS * C.TILE
        pygame.draw.rect(self.screen, PANEL, (x0, 0, C.SIDEBAR_W, C.HEIGHT))
        x = x0 + 14
        self.text(f"Gold  {g.gold}", (x, 12), color=GOLD)
        self.text(f"Lives {g.lives}", (x + 130, 12), color=RED if g.lives <= 5 else TEXT)
        self.text(f"Wave  {g.wave}", (x, 36))
        self.text(f"Kills {g.kills}", (x + 130, 36))
        status = "in progress" if g.wave_active else "waiting"
        self.text(f"Status: {status}", (x, 60), self.small, MUTED)
        self.text("Build", (x, 88), color=MUTED)

        for b in self.buttons():
            bg = (70, 90, 130) if b.active else (52, 56, 66) if b.enabled else (40, 42, 48)
            pygame.draw.rect(self.screen, bg, b.rect, border_radius=6)
            pygame.draw.rect(self.screen, (90, 96, 110), b.rect, 1, border_radius=6)
            color = TEXT if b.enabled else MUTED
            if b.sub:
                self.text(b.label, (b.rect.x + 10, b.rect.y + 5), color=color)
                self.text(b.sub, (b.rect.x + 10, b.rect.y + 25), self.small, MUTED)
            else:
                self.text(b.label, b.rect.center, self.small, color, center=True)

        t = self.selected
        if t:
            spec = C.TOWERS[t.kind]
            s = t.stats
            y = 362
            self.text(f"{spec['name']} tower  (level {t.level + 1})", (x, y))
            line = f"Dmg {s['damage']}  Range {s['range']}  Rate {s['rate']}/s"
            self.text(line, (x, y + 24), self.small, MUTED)
            extra = ""
            if "splash" in s:
                extra = f"Splash radius {s['splash']} tiles"
            elif "slow" in s:
                extra = f"Slows to {int(s['slow'] * 100)}% for {s['slow_time']}s"
            self.text(extra, (x, y + 42), self.small, MUTED)

        # message line and help at the bottom
        self.wrap(g.message, (x, C.HEIGHT - 110), C.SIDEBAR_W - 28, TEXT)
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
            if not self.paused:
                for _ in range(self.speed):
                    self.game.update(dt)
            self.draw()


def main():
    App().run()


if __name__ == "__main__":
    main()
