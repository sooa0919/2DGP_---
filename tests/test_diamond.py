import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.color_system import ColorSystem
from code.diamond import Diamond, DiamondRenderer
from code.player import Player
from code.tutorial_level import TutorialLevel
from code.water import AnimatedWater


class DiamondTests(unittest.TestCase):
    def setUp(self):
        self.level = TutorialLevel()
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)):
            self.player = Player(self.level)
            self.water = AnimatedWater()
            self.renderer = DiamondRenderer()
        self.player.enter_level(self.level)
        self.colors = ColorSystem()
        self.source = self.level.color_sources[0]
        self.fall, self.basin = self.level.water

    def assert_one_blue(self):
        self.assertEqual(sum((self.player.has_blue, self.source.has_blue, self.fall.has_blue)), 1)
        self.assertEqual(self.basin.has_blue, self.fall.has_blue)

    def extract(self):
        self.assertTrue(self.colors.interact_at(self.source.x, self.source.y,
                                                self.level, self.player))

    def test_gray_start_and_extract_switch_character_and_diamond_colors(self):
        self.assertFalse(self.player.has_blue)
        self.assertIs(self.player.current_images, self.player.gray_images)
        self.assertTrue(self.source.has_blue)
        self.assert_one_blue()
        self.extract()
        self.assertTrue(self.player.has_blue)
        self.assertIs(self.player.current_images, self.player.images)
        self.assertFalse(self.source.has_blue)
        self.assertEqual(self.colors.last_transfer, ('blue', 'extract'))
        self.assert_one_blue()

    def test_diamond_requires_nearby_hit_and_fresh_click(self):
        self.assertIsNone(self.colors.target_at(self.source.left - 1, self.source.y,
                                                self.level, self.player))
        self.player.x = 64
        self.assertFalse(self.colors.interact_at(self.source.x, self.source.y,
                                                 self.level, self.player))
        self.player.x = self.level.spawn[0]
        event = Event(type=pico2d.SDL_MOUSEBUTTONDOWN, button=pico2d.SDL_BUTTON_LEFT,
                      x=self.source.x, y=648 - self.source.y)
        self.colors.handle_event(event, self.level, self.player, 0)
        self.colors.handle_event(event, self.level, self.player, 0)
        self.assertTrue(self.player.has_blue)
        self.assertFalse(self.source.has_blue)
        self.assert_one_blue()

    def test_extracted_blue_opens_waterfall_and_character_can_cross_basin(self):
        self.extract()
        self.player.x = 304
        self.assertTrue(self.colors.interact_at(self.basin.left, self.basin.top - 4,
                                                self.level, self.player))
        self.assertFalse(self.player.has_blue)
        self.assertFalse(self.fall.solid)
        self.assert_one_blue()
        self.water.update(.2, self.level.water)
        self.assertAlmostEqual(self.fall.animation_time, .2)
        self.player.keys.add(pico2d.SDLK_d)
        for _ in range(65):
            self.player.update(1 / 60)
        self.assertGreater(self.player.x, self.fall.right)
        self.assertEqual(self.player.bottom, 0)
        self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
        self.player.update(.7)
        self.assertGreater(self.player.x, self.basin.right)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.bottom, 64)

    def test_gray_waterfall_blocks_walking_and_jumping_from_both_sides(self):
        for x, key, boundary in ((304, pico2d.SDLK_d, self.fall.left),
                                 (544, pico2d.SDLK_a, self.fall.right)):
            with self.subTest(key=key):
                self.player.enter_level(self.level)
                self.player.x = x
                self.player.keys.add(key)
                self.player.update(1)
                edge = self.player.right if key == pico2d.SDLK_d else self.player.left
                self.assertAlmostEqual(edge, boundary)
                self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN,
                                               key=pico2d.SDLK_SPACE))
                self.player.update(1)
                edge = self.player.right if key == pico2d.SDLK_d else self.player.left
                self.assertAlmostEqual(edge, boundary)
                self.assertEqual(self.player.bottom, self.basin.top)

    def test_reclaiming_blue_restores_waterfall_collision(self):
        self.extract()
        self.player.x = 304
        self.colors.interact_at(self.basin.left, self.basin.top - 4,
                                self.level, self.player)
        self.assertFalse(self.fall.solid)
        self.assertTrue(self.colors.interact_at(self.basin.left, self.basin.top - 4,
                                                self.level, self.player))
        self.assertTrue(self.fall.solid)
        self.player.keys.add(pico2d.SDLK_d)
        self.player.update(1)
        self.assertAlmostEqual(self.player.right, self.fall.left)
        self.assert_one_blue()

    def test_reset_after_transfer_restores_source_and_gray_character(self):
        self.extract()
        self.player.x = 304
        self.colors.interact_at(self.basin.left, self.basin.top - 4, self.level, self.player)
        self.colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_r),
                                 self.level, self.player, 0)
        self.assertFalse(self.player.has_blue)
        self.assertTrue(self.source.has_blue)
        self.assertTrue(self.fall.solid)
        self.assertEqual(self.source.animation_time, 0)
        self.assert_one_blue()

    def test_five_frames_loop_for_both_blue_and_gray_source(self):
        for has_blue in (True, False):
            self.source.has_blue = has_blue
            self.source.animation_time = 0
            frames = []
            for _ in range(5):
                frames.append(self.source.frame)
                self.source.update(1 / Diamond.FPS)
            self.assertEqual(frames, [0, 1, 2, 3, 4])
            self.assertEqual(self.source.frame, 0)
            self.renderer.draw([self.source], 0)
            images = self.renderer.blue if has_blue else self.renderer.gray
            images[0].draw.assert_called()

    def test_falling_out_of_map_restores_the_diamond_color(self):
        self.extract()
        self.player.y = -200
        self.player.update(.01)
        self.assertEqual(self.player.x, self.level.spawn[0])
        self.assertFalse(self.player.has_blue)
        self.assertTrue(self.source.has_blue)
        self.assertTrue(self.fall.solid)
        self.assert_one_blue()

    def test_waterfall_scrolling_does_not_draw_zero_height_slivers(self):
        self.fall.has_blue = True
        for _ in range(120):
            self.water.update(.1, self.level.water)
            self.water.draw_surface(self.level.water, 0)
        for call in self.water.falls.clip_draw.call_args_list:
            self.assertGreaterEqual(call.args[7], 1)
