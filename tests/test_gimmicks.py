import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.color_system import ColorSystem
from code.player import Player
from code.tutorial_level import TutorialLevel


class GimmickTests(unittest.TestCase):
    def setUp(self):
        self.level = TutorialLevel()
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)):
            self.player = Player(self.level)
        self.player.enter_level(self.level)
        self.colors = ColorSystem()

    def convert(self, key):
        self.colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=key),
                                 self.level, self.player, 0)

    def test_conversion_requires_a_held_color_and_selects_matching_character(self):
        self.convert(pico2d.SDLK_2)
        self.assertIsNone(self.player.color)
        gem = self.level.color_sources[0]
        self.assertTrue(self.colors.interact_at(gem.x, gem.y, self.level, self.player))
        for key, color in ((pico2d.SDLK_2, 'green'), (pico2d.SDLK_3, 'yellow'), (pico2d.SDLK_1, 'blue')):
            self.convert(key)
            self.assertEqual(self.player.color, color)
            self.assertIs(self.player.current_images, self.player.color_images[color])
        self.assertFalse(gem.has_blue)

    def test_vine_requires_correct_color_and_earlier_route_checkpoint(self):
        vine = self.level.vines[0]
        self.player.x, self.player.y = 808, 132
        self.player.color = 'green'
        self.assertFalse(self.colors.interact_at(808, 132, self.level, self.player))
        self.level.progress = 1
        self.player.color = 'blue'
        self.assertFalse(self.colors.interact_at(808, 132, self.level, self.player))
        self.player.color = 'green'
        self.assertTrue(self.colors.interact_at(808, 132, self.level, self.player))
        self.assertIsNone(self.player.color)
        self.assertTrue(vine.active)
        self.assertTrue(all(leaf in self.level.collision_platforms() for leaf in vine.leaves()))
        self.assertTrue(self.colors.interact_at(808, 132, self.level, self.player))
        self.assertEqual(self.player.color, 'green')
        self.assertFalse(vine.active)
        self.assertTrue(all(leaf not in self.level.collision_platforms() for leaf in vine.leaves()))

    def test_blue_extraction_freezes_all_falling_blocks_and_return_resumes_them(self):
        drop = self.level.droplets[1]
        self.level.progress = 6
        self.player.x, self.player.y = drop.left - 60, drop.top - 40
        start = drop.top
        self.level.update(.5, self.player)
        self.assertAlmostEqual(drop.top, start - 50)
        self.player.y = drop.top - 40
        self.assertTrue(self.colors.interact_at(drop.left + 1, self.player.y, self.level, self.player))
        self.assertEqual(self.player.color, 'blue')
        self.assertTrue(drop.solid)
        self.assertIn(drop.platform(), self.level.collision_platforms())
        frozen = drop.top
        moving = self.level.droplets[0].top
        self.level.update(.5, self.player)
        self.assertEqual(drop.top, frozen)
        self.assertEqual(self.level.droplets[0].top, moving)
        self.assertTrue(all(d.solid for d in self.level.droplets))
        self.assertTrue(self.colors.interact_at(drop.left + 1, self.player.y, self.level, self.player))
        self.assertFalse(drop.solid)
        self.assertTrue(all(d.has_blue for d in self.level.droplets))
        self.level.update(.1, self.player)
        self.assertAlmostEqual(drop.top, frozen - 10)

    def test_falls_keep_their_interval_and_recycle_after_one_period(self):
        initial = [d.top for d in self.level.droplets]
        for _ in range(880):
            for drop in self.level.droplets:
                drop.update(.01)
        for drop, top in zip(self.level.droplets, initial):
            self.assertAlmostEqual(drop.top, top, delta=1e-6)

    def test_yellow_lamp_opens_door_and_reclaim_closes_it(self):
        self.player.x, self.player.y = self.level.lamp.left - 32, 636
        self.player.color = 'yellow'
        self.assertFalse(self.colors.interact_at(self.level.lamp.left + 1, 636, self.level, self.player))
        self.level.progress = 7
        self.assertTrue(self.colors.interact_at(self.level.lamp.left + 1, 636, self.level, self.player))
        self.assertTrue(self.level.lamp.active)
        self.assertNotIn(self.level.door, self.level.collision_platforms())
        self.assertTrue(self.colors.interact_at(self.level.lamp.left + 1, 636, self.level, self.player))
        self.assertIn(self.level.door, self.level.collision_platforms())
        self.assertEqual(self.player.color, 'yellow')

    def test_reset_restores_all_devices_and_gray_start(self):
        self.level.vines[0].active = True
        self.level.droplets[0].has_blue = False
        self.level.droplets[0].top = 400
        self.level.lamp.active = True
        self.level.progress = 7
        self.player.color = 'yellow'
        self.colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_r),
                                 self.level, self.player, 0)
        self.assertIsNone(self.player.color)
        self.assertEqual(self.level.progress, 0)
        self.assertTrue(self.level.color_sources[0].has_blue)
        self.assertTrue(all(not v.active for v in self.level.vines))
        self.assertTrue(all(d.has_blue and d.top == d.initial_top for d in self.level.droplets))
        self.assertFalse(self.level.lamp.active)

    def test_later_device_cannot_be_used_by_walking_under_the_course(self):
        last = self.level.vines[-1]
        self.player.x, self.player.y = (last.left + last.right) / 2, 132
        self.player.color = 'green'
        self.level.update(.1, self.player)
        self.assertEqual(self.level.progress, 0)
        self.assertFalse(self.colors.interact_at(self.player.x, self.player.y, self.level, self.player))

    def test_falling_from_last_vine_keeps_position_color_and_progress(self):
        self.level.progress = 6
        self.level.water[0].has_blue = True
        self.level.color_sources[0].has_blue = False
        self.player.color = 'green'
        self.player.x, self.player.y = 3000, 480 + self.player.FOOT_OFFSET
        self.player.grounded = False
        for _ in range(180):
            self.player.update(1 / 120)
            self.level.update(1 / 120, self.player)
        self.assertEqual(self.level.progress, 6)
        self.assertEqual(self.player.x, 3000)
        self.assertEqual(self.player.bottom, 96)
        self.assertEqual(self.player.color, 'green')
        self.assertFalse(self.level.color_sources[0].has_blue)
        self.assertTrue(self.level.water[0].has_blue)

    def test_last_vine_can_be_activated_but_cannot_be_climbed_from_ground(self):
        vine = self.level.vines[-1]
        self.level.progress = 5
        self.player.x, self.player.y = 3000, 96 + self.player.FOOT_OFFSET
        self.player.grounded = True
        self.player.color = 'green'
        self.assertTrue(self.colors.interact_at(3000, 132, self.level, self.player))
        self.assertTrue(vine.active)
        self.assertEqual([p.top for p in vine.leaves()], [336, 416, 480])
        self.assertIsNone(self.player.color)
        self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
        highest = self.player.bottom
        for _ in range(180):
            self.player.update(1 / 120)
            self.level.update(1 / 120, self.player)
            highest = max(highest, self.player.bottom)
        self.assertLess(highest, 336)
        self.assertEqual(self.player.bottom, 96)
        self.assertEqual(self.player.x, 3000)

    def test_transfer_does_not_interrupt_running_or_jumping(self):
        self.player.keys.add(pico2d.SDLK_d)
        self.player.update(.05)
        source = self.level.color_sources[0]
        self.assertTrue(self.colors.interact_at(source.x, source.y, self.level, self.player))
        x = self.player.x
        self.player.update(.05)
        self.assertGreater(self.player.x, x)
        self.assertEqual(self.player.state, 'run')
        self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
        self.assertFalse(self.player.grounded)
