import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch
import pico2d
from code.player import Player
from code.tutorial import Tutorial, ABILITY_TEXT
from code.tutorial_level import TutorialLevel
from code.color_system import ColorSystem
from code.water import AnimatedWater


class TutorialTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', return_value=Mock(w=640, h=352)), \
             patch('pico2d.load_font', return_value=Mock()):
            self.ui = Tutorial()
            self.level = TutorialLevel()
            self.player = Player(self.level)
            self.player.enter_level(self.level)
            self.water = AnimatedWater()
        self.colors = ColorSystem()

    def key(self, key, repeat=False):
        self.ui.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=key, repeat=repeat), self.player)

    def release(self, key):
        self.ui.handle_event(Event(type=pico2d.SDL_KEYUP, key=key), self.player)

    def test_lessons_require_fresh_inputs_and_actual_jump_and_airborne_fall(self):
        self.key(pico2d.SDLK_a)
        for _ in range(10):
            self.key(pico2d.SDLK_a, True)
        self.assertEqual(self.ui.counts[pico2d.SDLK_a], 1)
        self.assertEqual(self.ui.lesson, 'move')
        for key in (pico2d.SDLK_a, pico2d.SDLK_d, pico2d.SDLK_d):
            self.release(key)
            self.key(key)
        self.assertEqual(self.ui.lesson, 'jump')
        self.player.grounded = False
        self.key(pico2d.SDLK_SPACE)
        self.assertEqual(self.ui.lesson, 'jump')
        self.release(pico2d.SDLK_SPACE)
        self.player.grounded = True
        self.key(pico2d.SDLK_SPACE)
        self.assertEqual(self.ui.lesson, 'fall')
        self.key(pico2d.SDLK_s)
        self.assertEqual(self.ui.lesson, 'fall')
        self.release(pico2d.SDLK_s)
        self.player.grounded = False
        self.key(pico2d.SDLK_s)
        self.assertEqual(self.ui.lesson, 'color')

    def test_hover_and_transfer_share_range_and_state_validation(self):
        p, fall = self.player, self.level.water[0]
        p.x = fall.left - 40
        self.assertIs(self.colors.target_at(fall.left, p.y, self.level, p), fall)
        self.assertTrue(self.colors.interact_at(fall.left, p.y, self.level, p))
        self.ui.update(.1, self.level, p, self.colors)
        self.assertEqual(self.ui.message, ABILITY_TEXT['blue'])
        p.x = 100
        self.assertIsNone(self.colors.target_at(fall.left, p.y, self.level, p))
        self.assertFalse(self.colors.interact_at(fall.left, p.y, self.level, p))

    def test_freezing_waterfall_pushes_sideways_without_ceiling_teleport(self):
        fall = self.level.water[0]
        p = self.player
        p.x = fall.left - 40
        self.colors.interact_at(fall.left, p.y, self.level, p)
        p.x = fall.right - 10
        old_y = p.y
        self.assertTrue(self.colors.interact_at(p.x, p.y, self.level, p))
        self.assertEqual(p.y, old_y)
        self.assertEqual(p.left, fall.right)

    def test_waterfall_basin_shares_color_clock_and_has_a_recessed_floor(self):
        fall, _, basin = self.level.water
        self.assertIs(basin.color_owner, fall)
        self.assertEqual(basin.top, fall.bottom)
        self.assertTrue(any(p.left <= basin.left and p.right >= basin.right
                            and p.top == basin.bottom for p in self.level.platforms))
        self.player.x = 650
        self.assertTrue(self.colors.interact_at(basin.left, basin.top - 4,
                                                self.level, self.player))
        self.assertTrue(fall.has_blue)
        self.water.update(.1, self.level.water)
        self.assertAlmostEqual(fall.animation_time, .1)
        self.assertEqual(basin.animation_time, fall.animation_time)
        self.level.reset_water()
        self.assertFalse(basin.has_blue)
        self.assertFalse(fall.has_blue)

    def test_color_dialog_waits_for_enter_and_has_a_blinking_corner_prompt(self):
        self.ui.message = ABILITY_TEXT['blue']
        self.ui.update(60, self.level, self.player, self.colors)
        self.assertIsNotNone(self.ui.message)
        self.key(pico2d.SDLK_SPACE)
        self.assertIsNotNone(self.ui.message)
        with patch('pico2d.draw_rectangle'):
            self.ui.time = 0
            self.ui.draw(self.level, self.player, self.colors, 0)
            self.ui.small.draw.assert_any_call(834, 242, '[ ENTER ]', (241, 221, 163))
            self.ui.small.draw.reset_mock()
            self.ui.time = .6
            self.ui.draw(self.level, self.player, self.colors, 0)
            self.assertFalse(any(c.args[2] == '[ ENTER ]' for c in self.ui.small.draw.call_args_list))
        self.key(pico2d.SDLK_RETURN)
        self.assertIsNone(self.ui.message)

    def test_key_icons_and_normal_play_have_no_explanatory_text(self):
        with patch('pico2d.draw_rectangle'):
            self.ui.draw(self.level, self.player, self.colors, 0)
            self.ui.font.draw.assert_not_called()
            self.ui.small.draw.assert_not_called()
            self.ui.keyboard.clip_draw.assert_called()
            self.ui.moved = self.ui.jumped = self.ui.fell = True
            self.ui.draw(self.level, self.player, self.colors, 0)
            self.ui.small.draw.assert_not_called()

    def test_falls_animate_only_with_blue_and_clip_inside_sheet(self):
        fall = self.level.water[0]
        self.water.update(.2, [fall])
        self.assertEqual(fall.animation_time, 0)
        fall.has_blue = True
        self.water.update(.2, [fall])
        self.water.draw_surface([fall], 0)
        self.assertGreater(fall.animation_time, 0)
        for call in self.water.falls.clip_draw.call_args_list:
            x, y, w, h, *_ = call.args
            self.assertGreaterEqual(min(x, y), 0)
            self.assertLessEqual(x + w, 640)
            self.assertLessEqual(y + h, 352)

    def test_reset_works_while_paused_and_does_not_replay_old_message(self):
        self.key(pico2d.SDLK_ESCAPE)
        self.assertTrue(self.ui.paused)
        self.key(pico2d.SDLK_r)
        self.assertFalse(self.ui.paused)
        self.assertEqual(self.ui.lesson, 'move')
        self.colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_r),
                                 self.level, self.player, 0)
        self.ui.update(.1, self.level, self.player, self.colors)
        self.assertIsNone(self.ui.message)

    def test_full_tile_route_with_real_physics_and_waterfall_transfer(self):
        p, fall = self.player, self.level.water[0]
        p.keys.add(pico2d.SDLK_d)
        gave = reclaimed = False
        for _ in range(3600):
            if not gave and p.x >= 672:
                self.assertTrue(self.colors.interact_at(fall.left, p.y, self.level, p))
                gave = True
            if gave and not reclaimed and p.x > fall.right + p.HALF_WIDTH + 8:
                self.assertTrue(self.colors.interact_at(fall.right - 1, p.y, self.level, p))
                reclaimed = True
            if p.grounded:
                ahead = any(s.left > p.x and s.left - p.right < 48
                            and s.top > p.bottom + 1 and s.bottom < p.top
                            for s in self.level.collision_platforms())
                support = next((s for s in self.level.collision_platforms()
                                if abs(s.top-p.bottom) < 1 and s.left <= p.x < s.right), None)
                gap = support and support.right - p.x < 40
                if ahead or gap:
                    p.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
            p.update(1/60)
            p.keys.discard(pico2d.SDLK_SPACE)
            if self.level.at_end(p):
                break
        self.assertTrue(self.level.at_end(p), (p.x, p.y))
        self.assertTrue(reclaimed)
