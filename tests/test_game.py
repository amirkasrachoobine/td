"""Headless rule tests: python3 -m unittest discover tests"""

import unittest

from td import config as C
from td.game import Game

DT = 1 / 60


def run(game, seconds):
    for _ in range(int(seconds / DT)):
        game.update(DT)


class GameTest(unittest.TestCase):
    def test_cannot_build_on_path_or_twice(self):
        g = Game()
        col, row = next(iter(g.path))
        self.assertFalse(g.build("arrow", col, row))
        self.assertTrue(g.build("arrow", 3, 1))
        self.assertFalse(g.build("arrow", 3, 1))
        self.assertEqual(g.gold, C.START_GOLD - 50)

    def test_cannot_build_on_scenery(self):
        g = Game()
        name, col, row, w, h = C.MAPS["village"]["decor"][0]
        self.assertFalse(g.build("arrow", col, row))

    def test_maps_are_consistent(self):
        from td.game import path_tiles
        for map_id, m in C.MAPS.items():
            g = Game(map_id)
            tiles = [(c + dc, r + dr) for _, c, r, w, h in m["decor"]
                     for dc in range(w) for dr in range(h)]
            self.assertEqual(len(tiles), len(set(tiles)), f"{map_id}: scenery overlaps")
            for t in tiles:
                self.assertTrue(0 <= t[0] < C.COLS and 0 <= t[1] < C.ROWS, f"{map_id}: {t}")
                self.assertNotIn(t, g.path, f"{map_id}: scenery on the path at {t}")
                self.assertNotIn(t, g.water, f"{map_id}: scenery in the river at {t}")
            # enough room to build next to the path
            free = [(c, r) for c in range(C.COLS) for r in range(C.ROWS) if g.can_build(c, r)]
            self.assertGreater(len(free), 100, map_id)

    def test_river_map_has_bridges_and_water(self):
        g = Game("river")
        self.assertEqual(len(g.bridges), 3)
        col, row = next(iter(g.water))
        self.assertFalse(g.can_build(col, row))

    def test_difficulty_scales_enemy_hp_and_speed(self):
        made = {}
        for diff in C.DIFFICULTIES:
            g = Game("village", diff)
            g.start_wave()
            g.update(DT)
            made[diff] = g.enemies[0]
        self.assertLess(made["easy"].max_hp, made["normal"].max_hp)
        self.assertLess(made["normal"].max_hp, made["hard"].max_hp)
        self.assertLess(made["easy"].speed, made["normal"].speed)
        self.assertLess(made["normal"].speed, made["hard"].speed)

    def test_build_needs_gold(self):
        g = Game()
        g.gold = 10
        self.assertFalse(g.build("cannon", 3, 1))
        self.assertEqual(g.towers, {})

    def test_upgrade_and_sell(self):
        g = Game()
        g.build("arrow", 3, 1)
        t = g.towers[(3, 1)]
        self.assertTrue(g.upgrade(t))
        self.assertEqual(t.level, 1)
        gold = g.gold
        g.sell(t)
        self.assertEqual(g.gold, gold + int(90 * C.SELL_REFUND))
        self.assertEqual(g.towers, {})

    def test_undefended_wave_leaks_lives(self):
        g = Game()
        g.start_wave()
        run(g, 60)
        self.assertFalse(g.wave_active)
        self.assertEqual(g.lives, C.START_LIVES - len(C.wave_plan(1)))
        self.assertEqual(g.kills, 0)

    def test_defended_wave_one_is_cleared(self):
        g = Game()
        g.build("arrow", 5, 4)
        g.build("arrow", 3, 5)
        g.start_wave()
        run(g, 60)
        self.assertFalse(g.wave_active)
        self.assertGreater(g.kills, 0)
        self.assertEqual(g.lives, C.START_LIVES)

    def test_burn_damages_over_time(self):
        from td.game import Enemy
        g = Game()
        e = Enemy("special", g.waypoints, 1.0)
        g.enemies.append(e)
        e.apply_burn(20, 2.0)
        for _ in range(60):
            e.update(DT, g)
        self.assertAlmostEqual(e.hp, e.max_hp - 20, delta=0.5)
        for _ in range(120):
            e.update(DT, g)
        self.assertAlmostEqual(e.hp, e.max_hp - 40, delta=0.5)
        self.assertEqual(e.burn_left <= 0, True)

    def test_lightning_chains_to_nearby_enemies(self):
        from td.game import Enemy, Projectile, Tower
        g = Game()
        t = Tower("lightning", 5, 4)
        enemies = [Enemy("special", g.waypoints, 1.0) for _ in range(6)]
        for i, e in enumerate(enemies):
            e.x, e.y = 300 + i * 30, 300        # 30px apart, inside chain range
        g.enemies = enemies
        Projectile(t, enemies[0]).chain(g)
        hit = [e for e in enemies if e.hp < e.max_hp]
        self.assertEqual(len(hit), 1 + C.TOWERS["lightning"]["levels"][0]["chain"])

    def test_every_enemy_has_a_sprite_per_faction(self):
        import os
        root = os.path.join(os.path.dirname(__file__), "..", "assets", "enemies")
        for faction in C.FACTIONS:
            for kind in C.ENEMIES:
                self.assertTrue(os.path.exists(os.path.join(root, f"{faction}_{kind}.png")))

    def test_waves_cycle_factions_and_bring_champions(self):
        self.assertEqual([C.wave_faction(n) for n in (1, 2, 3, 4, 5)],
                         ["human", "elf", "goblin", "skeleton", "human"])
        self.assertNotIn("champion", [k for k, _ in C.wave_plan(4)])
        self.assertIn("champion", [k for k, _ in C.wave_plan(5)])

    def test_every_tower_has_sprites(self):
        import os
        root = os.path.join(os.path.dirname(__file__), "..", "assets", "towers")
        for kind, spec in C.TOWERS.items():
            for name in spec["sprites"]:
                self.assertTrue(os.path.exists(os.path.join(root, name + ".png")), name)

    def test_game_over(self):
        g = Game()
        g.lives = 1
        g.start_wave()
        run(g, 60)
        self.assertTrue(g.over)
        self.assertFalse(g.start_wave())


if __name__ == "__main__":
    unittest.main()
