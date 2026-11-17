"""Shared data validation and campaign lifecycle regressions."""

from copy import deepcopy
import json
import unittest

from td import config as C
from td.game import Game
from td.level import validate


class CampaignTest(unittest.TestCase):
    def test_victory_and_replay(self):
        game = Game("river", "hard")
        self.assertEqual(C.TOTAL_WAVES, 10)
        self.assertEqual(C.wave_plan(10)[-1][0], "champion")
        for wave in range(1, C.TOTAL_WAVES + 1):
            self.assertTrue(game.start_wave())
            self.assertEqual(game.wave, wave)
            while game.wave_active:
                game.update(1 / 60)
                for enemy in game.enemies:
                    game.damage(enemy, enemy.max_hp)
        self.assertTrue(game.victory)
        self.assertTrue(game.over)
        self.assertFalse(game.start_wave())
        game.reset()
        self.assertEqual((game.map_id, game.difficulty), ("river", "hard"))
        self.assertEqual((game.wave, game.gold, game.lives), (0, C.START_GOLD, C.START_LIVES))
        self.assertFalse(game.over)
        self.assertFalse(game.victory)
        self.assertFalse(game.towers)

    def test_invalid_campaign_fields(self):
        original = json.loads(C.LEVEL_FILE.read_text(encoding="utf-8"))
        for key, value in (("enemy", "missing"), ("delay", -1), ("delay", float("nan"))):
            with self.subTest(key=key, value=value):
                data = deepcopy(original)
                data["waves"][0]["groups"][0][key] = value
                with self.assertRaisesRegex(ValueError, rf"waves\[0\]\.groups\[0\]\.{key}"):
                    validate(data)

    def test_diagonal_path_is_rejected(self):
        data = json.loads(C.LEVEL_FILE.read_text(encoding="utf-8"))
        data["maps"]["village"]["path"][1] = [4, 3]
        with self.assertRaisesRegex(ValueError, r"maps\.village\.path\[1\]"):
            validate(data)
