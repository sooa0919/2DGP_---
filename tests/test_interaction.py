import unittest
from unittest.mock import Mock, patch

from PIL import Image
import pico2d
from types import SimpleNamespace as Event

from code.color_system import ColorSystem
from code.interaction import InteractionAnimation
from code.level import Platform
from code.player import Player
from code.settings import IMAGE_ROOT
from code.tutorial_level import TutorialLevel


class InteractionTests(unittest.TestCase):
    def setUp(self):
        def load(path):
            with Image.open(path) as image:
                return Mock(w=image.width, h=image.height)
        self.level = TutorialLevel()
        with patch('pico2d.load_image', side_effect=load):
            self.player = Player(self.level)
        self.player.enter_level(self.level)
        self.colors = ColorSystem()
        self.animation = self.player.interaction

    def test_successful_extraction_giving_and_reclaim_use_correct_pose(self):
        source = self.level.color_sources[0]
        self.assertTrue(self.colors.interact_at(source.x, source.y, self.level, self.player))
        self.assertEqual(self.animation.color, 'blue')
        self.assertTrue(self.animation.extracting)
        self.player.x = 304
        basin = self.level.water[1]
        self.assertTrue(self.colors.interact_at(basin.left, basin.top - 4, self.level, self.player))
        self.assertFalse(self.animation.extracting)
        self.assertTrue(self.colors.interact_at(basin.left, basin.top - 4, self.level, self.player))
        self.assertTrue(self.animation.extracting)

    def test_invalid_click_does_not_start_or_restart_animation(self):
        self.assertFalse(self.colors.interact_at(-100, -100, self.level, self.player))
        self.assertFalse(self.animation.active)
        self.player.start_interaction('blue', True)
        self.animation.update(.2)
        self.colors.interact_at(-100, -100, self.level, self.player)
        self.assertAlmostEqual(self.animation.time, .2)

    def test_all_colors_play_eight_frames_from_the_correct_two_rows(self):
        for color in self.animation.COLORS:
            for extracting in (True, False):
                with self.subTest(color=color, extracting=extracting):
                    self.player.start_interaction(color, extracting)
                    image = self.animation.poses[color]
                    image.reset_mock()
                    self.animation.effect.reset_mock()
                    for frame in range(8):
                        self.player.facing = -1 if frame % 2 == 0 else 1
                        self.player.draw(20, 30)
                        args = image.clip_composite_draw.call_args.args
                        expected_row, column = divmod(frame + (0 if extracting else 8), 4)
                        left = round(column * image.w / 4)
                        right = round((column + 1) * image.w / 4)
                        top = round(expected_row * image.h / 4)
                        bottom = round((expected_row + 1) * image.h / 4)
                        self.assertEqual(args[:4], (left, image.h - bottom, right-left, bottom-top))
                        self.assertEqual(args[5], '' if self.player.facing < 0 else 'h')
                        self.assertEqual(args[6], round(self.player.x - 20))
                        self.animation.update(.1)
                    self.assertFalse(self.animation.active)
                    self.assertEqual(self.animation.effect.clip_draw.call_count, 8 if extracting else 0)

    def test_extraction_swirl_draws_behind_pose_and_follows_camera(self):
        calls = Mock()
        calls.attach_mock(self.animation.effect, 'effect')
        calls.attach_mock(self.animation.poses['green'], 'pose')
        self.player.start_interaction('green', True)
        self.player.draw(20, 30)
        self.assertEqual([call[0] for call in calls.mock_calls],
                         ['effect.clip_draw', 'pose.clip_composite_draw'])
        args = self.animation.effect.clip_draw.call_args.args
        self.assertEqual(args[:4], (0, 64, 64, 64))
        self.assertEqual(args[4:6], (round(self.player.x-20), round(self.player.bottom-30+34)))

    def test_animation_expires_and_reset_or_fall_clears_it(self):
        self.player.start_interaction('yellow', False)
        self.player.update(.8)
        self.assertFalse(self.animation.active)
        self.player.start_interaction('blue', True)
        self.player.enter_level(self.level)
        self.assertFalse(self.animation.active)
        self.player.start_interaction('blue', True)
        self.player.y = -200
        self.player.update(.01)
        self.assertFalse(self.animation.active)

    def test_generated_effect_keeps_source_frames_and_transparency(self):
        root = IMAGE_ROOT / 'character'
        with Image.open(root / 'effefct/Effect and FX Pixel All Free (1)/Free/Part 1/16.png') as original, \
             Image.open(root / 'interaction/extraction_effects.png') as packed:
            self.assertEqual(packed.size, (896, 192))
            self.assertEqual(original.crop((0, 128, 896, 256)).tobytes(),
                             packed.crop((0, 0, 896, 128)).tobytes())
            self.assertEqual(original.getchannel('A').crop((0, 320, 896, 384)).tobytes(),
                             packed.getchannel('A').crop((0, 128, 896, 192)).tobytes())

    def test_movement_is_locked_then_resumes_with_held_direction(self):
        self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_d))
        self.player.start_interaction('blue', True)
        x, facing = self.player.x, self.player.facing
        for _ in range(8):
            self.player.update(.1)
            self.assertEqual(self.player.x, x)
            self.assertEqual(self.player.facing, facing)
        self.assertFalse(self.animation.active)
        self.player.update(.1)
        self.assertGreater(self.player.x, x)

    def test_locked_actions_are_not_queued_and_released_keys_stay_released(self):
        self.level.platforms = [Platform(0, 0, 640, 32)]
        self.level.thin_platforms = [Platform(64, 148, 256, 160, one_way=True)]
        self.player.x, self.player.y = 160, 160 + self.player.FOOT_OFFSET
        self.player.start_interaction('blue', False)
        for key in (pico2d.SDLK_a, pico2d.SDLK_SPACE, pico2d.SDLK_s):
            self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=key))
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.velocity_y, 0)
        self.assertEqual(self.player.drop_serial, 0)
        self.player.handle_event(Event(type=pico2d.SDL_KEYUP, key=pico2d.SDLK_a))
        x = self.player.x
        self.player.update(.8)
        self.player.update(.1)
        self.assertEqual(self.player.x, x)
        self.assertTrue(self.player.grounded)
        self.player.handle_event(Event(type=pico2d.SDL_KEYUP, key=pico2d.SDLK_SPACE))
        self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
        self.assertFalse(self.player.grounded)

    def test_locked_pose_still_falls_and_collides_with_the_floor(self):
        self.player.y += 20
        self.player.grounded = False
        self.player.start_interaction('blue', True)
        self.player.update(.1)
        self.assertLess(self.player.y, 120)
        self.assertTrue(self.animation.active)
        self.player.update(.2)
        self.assertEqual(self.player.bottom, self.level.spawn[1])
