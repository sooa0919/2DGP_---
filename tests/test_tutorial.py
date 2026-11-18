import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d
from code.player import Player
from code.level import Platform
from code.tutorial import Tutorial
from code.tutorial_level import TutorialLevel
from code.color_system import ColorSystem


class TutorialTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)), \
             patch('pico2d.load_font', return_value=Mock()):
            self.ui = Tutorial()
            self.level = TutorialLevel()
            self.player = Player(self.level)
            self.player.enter_level(self.level)
        self.colors = ColorSystem()

    def key(self, key, down=True):
        event = Event(type=pico2d.SDL_KEYDOWN if down else pico2d.SDL_KEYUP, key=key)
        self.ui.handle_event(event, self.player)
        self.player.handle_event(event)

    def platform_room(self):
        self.level.platforms = [Platform(0, 0, 640, 32)]
        self.level.thin_platforms = [Platform(64, 148, 256, 160, one_way=True),
                                     Platform(64, 84, 256, 96, one_way=True)]
        self.player.x, self.player.y = 160, 196
        self.player.grounded = True

    def test_revised_map_has_only_tiles_and_three_thin_platforms(self):
        self.assertFalse(self.level.gimmicks_enabled)
        self.assertEqual(self.level.water, [])
        self.assertEqual(self.level.objects, [])
        self.assertEqual(len(self.level.thin_platforms), 3)
        self.assertTrue(all(p.one_way for p in self.level.thin_platforms))
        self.assertEqual(self.level.spawn, (160, 128))

    def test_key_repeat_does_not_finish_movement_lesson(self):
        self.key(pico2d.SDLK_a)
        for _ in range(5):
            self.key(pico2d.SDLK_a)
        self.assertEqual(self.ui.counts[pico2d.SDLK_a], 1)
        for key in (pico2d.SDLK_a, pico2d.SDLK_d, pico2d.SDLK_d):
            self.key(key, False)
            self.key(key)
        self.assertEqual(self.ui.lesson, 'jump')

    def test_s_drops_through_only_current_platform_and_lands_on_next(self):
        self.platform_room()
        self.key(pico2d.SDLK_s)
        self.assertFalse(self.player.grounded)
        for _ in range(60):
            self.player.update(1 / 120)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.bottom, 96)
        self.assertEqual(self.player.drop_serial, 1)
        # Holding S does not drop through a second platform on landing.
        self.player.update(.2)
        self.assertEqual(self.player.bottom, 96)
        self.key(pico2d.SDLK_s, False)
        self.key(pico2d.SDLK_s)
        self.player.update(.5)
        self.assertEqual(self.player.bottom, 32)

    def test_jump_passes_through_underside_and_lands_on_top(self):
        self.platform_room()
        self.level.thin_platforms = self.level.thin_platforms[1:]
        self.player.y = 68
        self.key(pico2d.SDLK_SPACE)
        self.player.update(.2)
        self.assertGreater(self.player.bottom, 96)
        self.player.update(.7)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.bottom, 96)

    def test_s_on_solid_floor_does_not_drop(self):
        start = self.player.y
        self.key(pico2d.SDLK_s)
        self.player.update(.2)
        self.assertEqual(self.player.y, start)
        self.assertEqual(self.player.drop_serial, 0)

    def test_s_in_air_keeps_normal_gravity(self):
        self.key(pico2d.SDLK_SPACE)
        self.player.update(.1)
        velocity = self.player.velocity_y
        self.key(pico2d.SDLK_s)
        self.player.update(.1)
        self.assertAlmostEqual(self.player.velocity_y, velocity - self.player.GRAVITY * .1)
        self.assertEqual(self.player.drop_serial, 0)

    def test_no_color_message_and_icons_follow_head(self):
        self.colors.transfer_serial = 1
        self.colors.last_transfer = ('blue', 'give')
        self.ui.update(.1, self.level, self.player, self.colors)
        self.assertIsNone(self.ui.message)
        self.ui.draw(self.level, self.player, self.colors, 0)
        self.ui.font.draw.assert_not_called()
        self.ui.small.draw.assert_not_called()
        calls = self.ui.keyboard.clip_draw.call_args_list
        self.assertAlmostEqual((calls[0].args[4] + calls[1].args[4]) / 2, self.player.x)
        self.assertLess(calls[0].args[5] - self.player.top, 34)

    def test_s_lesson_completes_after_successful_drop(self):
        self.platform_room()
        self.ui.moved = self.ui.jumped = True
        self.key(pico2d.SDLK_s)
        self.ui.update(.1, self.level, self.player, self.colors)
        self.assertTrue(self.ui.fell)

    def test_reset_clears_ignored_platforms(self):
        self.platform_room()
        self.key(pico2d.SDLK_s)
        self.assertTrue(self.player.ignored_platforms)
        self.player.enter_level(self.level)
        self.assertEqual(self.player.ignored_platforms, [])
        self.assertEqual(self.player.drop_serial, 0)
