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
        self.assertTrue(g.build("arrow", 0, 0))
        self.assertFalse(g.build("arrow", 0, 0))
        self.assertEqual(g.gold, C.START_GOLD - 50)

    def test_build_needs_gold(self):
        g = Game()
        g.gold = 10
        self.assertFalse(g.build("cannon", 0, 0))
        self.assertEqual(g.towers, {})

    def test_upgrade_and_sell(self):
        g = Game()
        g.build("arrow", 0, 0)
        t = g.towers[(0, 0)]
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

    def test_game_over(self):
        g = Game()
        g.lives = 1
        g.start_wave()
        run(g, 60)
        self.assertTrue(g.over)
        self.assertFalse(g.start_wave())


if __name__ == "__main__":
    unittest.main()
