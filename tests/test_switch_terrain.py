from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from PIL import Image, ImageChops
import pico2d

from code.color_system import ColorSystem
from code.illustrated_level import IllustratedLevel
from code.player import Player


ROOT = Path(__file__).resolve().parent.parent


class SwitchTerrainTests(unittest.TestCase):
    def test_switch_ledge_collision_matches_visible_tile_top_and_underside(self):
        level = IllustratedLevel()
        with Image.open(ROOT / 'image/background/tile/tile.png') as source:
            alpha = source.convert('RGBA').resize((4096, 1008), Image.Resampling.LANCZOS).getchannel('A')
        for x in (2942, 2982, 3022, 3062, 3102):
            runs = []
            start = None
            for y in range(300, 551):
                solid = y < 550 and alpha.getpixel((x, y)) >= 160
                if solid and start is None:
                    start = y
                elif not solid and start is not None:
                    runs.append((start, y))
                    start = None
            top, bottom = max(runs, key=lambda run: run[1] - run[0])
            surface = next(p for p in level.platforms if p.left <= x < p.right and 550 < p.top < 700)
            self.assertEqual(surface.top, 1008 - top)
            self.assertEqual(surface.bottom, 1008 - bottom)

    def test_player_can_land_and_walk_to_switch_on_the_actual_tile_surface(self):
        level = IllustratedLevel()
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)):
            player = Player(level)
        player.enter_level(level)
        player.x, player.y = 2940, 650 + player.FOOT_OFFSET
        player.grounded = False
        for _ in range(60):
            player.update(1/120)
            level.update(1/120, player)
        self.assertTrue(player.grounded)
        player.keys.add(pico2d.SDLK_d)
        for _ in range(100):
            if player.x >= 3060:
                player.keys.clear()
            player.update(1/120)
            level.update(1/120, player)
        self.assertGreaterEqual(player.x, 3060)
        self.assertTrue(player.grounded)
        self.assertAlmostEqual(player.bottom, 619, delta=5)
        player.color = 'yellow'
        self.assertTrue(ColorSystem().interact_at(3060, 655, level, player))
        self.assertTrue(level.door_switch.active)

    def test_colored_door_preserves_silhouette_and_has_warm_color(self):
        folder = ROOT / 'image/background/stage1'
        with Image.open(folder / 'door.png') as gray, Image.open(folder / 'door_on.png') as colored:
            self.assertIsNone(ImageChops.difference(gray.getchannel('A'), colored.getchannel('A')).getbbox())
            r, g, b, a = colored.getpixel((35, 180))
            self.assertGreater(a, 200)
            self.assertGreater(r, g)
            self.assertGreater(g, b)
