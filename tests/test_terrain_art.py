import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from code.terrain_art import TerrainArt
from code.level import Platform


class TerrainArtTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', side_effect=lambda path: Mock(w=64, h=64)):
            self.art = TerrainArt()

    def test_frozen_water_is_static_and_blue_water_animates(self):
        water = SimpleNamespace(left=0, right=64, bottom=0, top=80, has_blue=False)
        self.art.water(water, 0, 0, 0, vertical=True)
        self.art.water(water, 0, 0, 2, vertical=True)
        self.assertEqual(self.art.images['fall_gray'].draw.call_count, 2)
        self.art.images['fall_0'].draw.assert_not_called()
        water.has_blue = True
        self.art.water(water, 0, 0, 0, vertical=True)
        self.art.water(water, 0, 0, .23, vertical=True)
        self.art.images['fall_0'].draw.assert_called_once()
        self.art.images['fall_1'].draw.assert_called_once()

    def test_partial_tiles_stay_inside_platform_collision_edges(self):
        self.art.terrain(Platform(0, 0, 96, 96), 0, 0)
        calls = [call for image in self.art.images.values() for call in image.clip_draw.call_args_list]
        self.assertGreater(len(calls), 0)
        for call in calls:
            _, _, _, _, x, y, width, height = call.args
            self.assertGreaterEqual(x - width / 2, 0)
            self.assertLessEqual(x + width / 2, 96)
            self.assertGreaterEqual(y - height / 2, 0)
            self.assertLessEqual(y + height / 2, 96)
