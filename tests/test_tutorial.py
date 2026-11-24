import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d
from code.player import Player
from code.level import Platform
from code.tutorial import Tutorial
from code.tutorial_level import TutorialLevel
from code.color_system import ColorSystem
from code.camera import Camera


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

    def test_reference_map_starts_at_far_left_with_gray_player_and_a_blue_gem(self):
        self.assertTrue(self.level.gimmicks_enabled)
        self.assertEqual((self.level.width, self.level.height), (4096, 1008))
        self.assertEqual(self.level.spawn, (80, 96))
        self.assertIsNone(self.player.color)
        self.assertEqual(len(self.level.vines), 4)
        self.assertEqual(len(self.level.droplets), 4)
        source = self.level.color_sources[0]
        self.assertGreater(source.x, self.player.x)
        self.assertLess(source.x, self.level.water[0].left)
        self.assertTrue(source.has_blue)
        self.assertTrue(all(p.one_way for p in self.level.thin_platforms))

    def test_exit_requires_lamp_and_the_final_route_stage(self):
        self.player.x = self.level.end_x + 8
        self.player.y = self.level.end_y + self.player.FOOT_OFFSET
        self.assertFalse(self.level.at_end(self.player))
        self.level.lamp.active = True
        self.assertFalse(self.level.at_end(self.player))
        self.level.progress = 7
        self.assertTrue(self.level.at_end(self.player))
        self.key(pico2d.SDLK_SPACE)
        self.player.update(.2)
        self.assertFalse(self.level.at_end(self.player))
        self.player.update(.7)
        self.assertTrue(self.level.at_end(self.player))

    def test_camera_tracks_vertical_world_and_stops_at_edges(self):
        camera = Camera(1152, 4096, 1536)
        camera.snap_to(*self.level.spawn)
        self.assertEqual((camera.x, camera.y), (0, 0))
        camera.snap_to(2000, 1000)
        self.assertEqual(camera.y, 676)
        camera.snap_to(4096, 1536)
        self.assertEqual(camera.y, 1536 - 648)
        self.assertEqual(camera.x, 4096 - 1152)

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
        self.level.platforms = [Platform(0, 0, 640, 64)]
        self.level.thin_platforms = []
        self.key(pico2d.SDLK_SPACE)
        self.player.update(.1)
        velocity = self.player.velocity_y
        self.key(pico2d.SDLK_s)
        self.player.update(.1)
        self.assertAlmostEqual(self.player.velocity_y, velocity - self.player.GRAVITY * .1)
        self.assertEqual(self.player.drop_serial, 0)

    def test_new_guidance_and_color_selector_draw_without_pausing(self):
        with patch('pico2d.draw_rectangle') as draw:
            self.ui.draw(self.level, self.player, self.colors, 0)
        self.assertTrue(all(call.args[1] > 85 for call in draw.call_args_list))
        self.assertEqual(self.ui.small.draw.call_count, 4)
        self.assertFalse(self.ui.paused)
        self.ui.mouse_pos = (100, 100)
        self.key(pico2d.SDLK_r)
        self.assertIsNone(self.ui.mouse_pos)

    def test_reset_clears_ignored_platforms(self):
        self.platform_room()
        self.key(pico2d.SDLK_s)
        self.assertTrue(self.player.ignored_platforms)
        self.player.enter_level(self.level)
        self.assertEqual(self.player.ignored_platforms, [])
        self.assertEqual(self.player.drop_serial, 0)

    def test_head_key_icons_follow_camera_then_change_from_move_to_jump(self):
        self.player.x, self.player.y = 400, 500
        with patch('pico2d.draw_rectangle'):
            self.ui.draw(self.level, self.player, self.colors, 200, 100)
        calls = self.ui.keyboard.clip_draw.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual((calls[0].args[4] + calls[1].args[4]) / 2, 200)
        self.assertGreater(calls[0].args[5], self.player.top - 100)
        self.ui.update(0, self.level, self.player, self.colors)
        self.ui.keyboard.clip_draw.reset_mock()
        with patch('pico2d.draw_rectangle'):
            self.ui.draw(self.level, self.player, self.colors, 200, 100)
        self.ui.keyboard.clip_draw.assert_called_once()
        self.assertEqual(self.ui.keyboard.clip_draw.call_args.args[0], 8 * 16)

    def test_s_key_appears_only_on_thin_platform_and_finishes_on_successful_drop(self):
        self.platform_room()
        self.ui.moved = self.ui.jumped = True
        with patch('pico2d.draw_rectangle'):
            self.ui.draw(self.level, self.player, self.colors, 0)
        self.ui.keyboard.clip_draw.assert_called_once()
        self.assertEqual(self.ui.keyboard.clip_draw.call_args.args[1], self.ui.keyboard.h - 19 * 16)
        self.key(pico2d.SDLK_s)
        self.ui.update(.01, self.level, self.player, self.colors)
        self.assertTrue(self.ui.fell)
        self.ui.keyboard.clip_draw.reset_mock()
        with patch('pico2d.draw_rectangle'):
            self.ui.draw(self.level, self.player, self.colors, 0)
        self.ui.keyboard.clip_draw.assert_not_called()
