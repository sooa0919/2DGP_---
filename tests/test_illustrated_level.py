import unittest
from unittest.mock import Mock, patch

import pico2d

from code.color_system import ColorSystem
from code.illustrated_level import IllustratedLevel
from code.player import Player
from code.stage_art import StageArt


class IllustratedStageTests(unittest.TestCase):
    def setUp(self):
        self.level = IllustratedLevel()
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)):
            self.player = Player(self.level)
        self.player.enter_level(self.level)
        self.colors = ColorSystem()

    def tick(self, duration):
        for _ in range(round(duration * 120)):
            self.player.update(1/120)
            self.level.update(1/120, self.player)

    def test_spawn_and_illustrated_terrain_support_the_player(self):
        self.tick(.3)
        self.assertTrue(self.player.grounded)
        self.assertAlmostEqual(self.player.bottom, 78, delta=2)
        # A former wall at x=960..1184 is now an actual gap between pillars.
        self.assertFalse(any(p.left < 970 < p.right and p.bottom < 200 < p.top
                             for p in self.level.platforms))
        for x, floor in ((830, 438), (1040, 236), (1250, 236), (1470, 310), (3900, 828)):
            self.player.x, self.player.y = x, floor + 60 + self.player.FOOT_OFFSET
            self.player.velocity_y = 0
            self.player.grounded = False
            self.tick(.6)
            self.assertTrue(self.player.grounded, x)
            self.assertAlmostEqual(self.player.bottom, floor, delta=6)

    def test_terrain_underside_blocks_upward_motion(self):
        self.player.x, self.player.y = 650, 330 + self.player.FOOT_OFFSET
        self.player.grounded = False
        self.player.velocity_y = 400
        self.tick(.2)
        self.assertLess(self.player.top, 396)
        self.assertLessEqual(self.player.velocity_y, 0)

    def test_blue_water_cycles_in_order_and_gray_water_stops(self):
        fall = self.level.water[0]
        self.level.update(.3, self.player)
        self.assertEqual(fall.animation_time, 0)
        with patch('pico2d.load_image', return_value=Mock(w=1024, h=1008)):
            art = StageArt(self.level)
        with patch.object(art, 'sprite') as draw, patch('pico2d.draw_rectangle'):
            art.draw_devices(0, 0)
            self.assertEqual(draw.call_args_list[0].args[0], 'water1')
            self.assertTrue(draw.call_args_list[0].kwargs['gray'])
            fall.has_blue = True
            for expected in ('water1', 'water2', 'water3', 'water1'):
                art.draw_devices(0, 0)
                water_call = [c for c in draw.call_args_list if c.args[0].startswith('water')][-1]
                self.assertEqual(water_call.args[0], expected)
                self.level.update(.22, self.player)
            fall.has_blue = False
            clock = fall.animation_time
            self.level.update(2, self.player)
            self.assertEqual(fall.animation_time, clock)
            art.draw_devices(0, 0)
            water_call = [c for c in draw.call_args_list if c.args[0].startswith('water')][-1]
            self.assertEqual(water_call.args[0], 'water1')
            self.assertTrue(water_call.kwargs['gray'])

    def test_water_shape_does_not_block_or_slow_empty_space(self):
        fall = self.level.water[0]
        self.assertFalse(fall.contains_point(200, 300))
        self.assertTrue(fall.contains_point(345, 300))
        self.player.x, self.player.y = 210, 300
        fall.has_blue = True
        self.assertFalse(self.player.in_water)
        self.player.x = 345
        self.assertTrue(self.player.in_water)
        fall.has_blue = False
        self.player.resolve_solid_water(fall)
        self.assertFalse(fall.overlaps(self.player.left, self.player.bottom, self.player.right, self.player.top))

    def test_pond_has_a_recessed_bottom_instead_of_a_hidden_surface_floor(self):
        pond = self.level.water[1]
        self.player.x, self.player.y = 2570, 130
        self.player.grounded = False
        self.tick(.6)
        self.assertGreaterEqual(self.player.bottom, 65)
        pond.has_blue = True
        self.tick(.6)
        self.assertAlmostEqual(self.player.bottom, 35, delta=2)

    def test_ceiling_sources_start_colored_and_support_extraction_and_reset(self):
        sources = [source for source in self.level.color_sources if getattr(source, 'sprite_name', None)]
        self.assertEqual(len(sources), 2)
        for source in sources:
            self.player.color = None
            self.player.x = (source.left + source.right) / 2
            self.player.y = (source.bottom + source.top) / 2
            self.assertEqual(source.stored_color, source.required_color)
            self.assertTrue(self.colors.interact_at(self.player.x, self.player.y, self.level, self.player))
            self.assertEqual(self.player.color, source.required_color)
            self.assertIsNone(source.stored_color)
            self.assertEqual(self.colors.last_transfer, (source.required_color, 'extract'))
        self.player.enter_level(self.level)
        self.assertTrue(all(source.active for source in sources))

    def test_colored_water_is_transparent_and_draws_after_the_character(self):
        from code.blockout import ForestBlockout
        with patch('pico2d.load_image', return_value=Mock(w=1024, h=1008)):
            bg = ForestBlockout(self.level)
        self.level.water[0].has_blue = True
        with patch.object(bg.stage, 'sprite') as sprites, patch('pico2d.draw_rectangle'):
            bg.draw(0)
            self.assertFalse(any(c.args[0].startswith('water') for c in sprites.call_args_list))
            bg.draw_overlay(0, self.player)
            water = [c for c in sprites.call_args_list if c.args[0].startswith('water')][-1]
            self.assertEqual(water.kwargs['opacity'], .45)
            self.assertFalse(water.kwargs['gray'])
            self.level.water[0].has_blue = False
            bg.draw_overlay(0, self.player)
            water = [c for c in sprites.call_args_list if c.args[0].startswith('water')][-1]
            self.assertEqual(water.kwargs['opacity'], 1.0)
            self.assertTrue(water.kwargs['gray'])

    def test_leaf_visuals_and_collision_toggle_together(self):
        leaf = self.level.leaves[0]
        self.player.x, self.player.y = leaf.left + 20, leaf.top + 15
        self.player.color = 'green'
        self.assertNotIn(leaf.platform(), self.level.collision_platforms())
        self.assertTrue(self.colors.interact_at(leaf.left + 20, leaf.top - 20, self.level, self.player))
        self.assertIn(leaf.platform(), self.level.collision_platforms())
        self.assertTrue(self.colors.interact_at(leaf.left + 20, leaf.top - 20, self.level, self.player))
        self.assertNotIn(leaf.platform(), self.level.collision_platforms())

    def test_elevator_switch_raises_rider_and_reclaim_returns_it(self):
        lift = self.level.elevator
        switch = self.level.elevator_switch
        self.player.x, self.player.y = 3630, lift.top + self.player.FOOT_OFFSET
        self.player.grounded = True
        self.player.color = 'yellow'
        self.assertTrue(self.colors.interact_at(switch.left + 10, switch.top - 25, self.level, self.player))
        self.tick(6)
        self.assertEqual(lift.top, lift.high)
        self.assertAlmostEqual(self.player.bottom, lift.high)
        self.assertTrue(self.player.grounded)
        # Jump down to the adjacent device and reclaim its yellow color.
        self.player.x, self.player.y = switch.left + 20, switch.top
        self.assertTrue(self.colors.interact_at(switch.left + 10, switch.top - 25, self.level, self.player))
        self.assertEqual(self.player.color, 'yellow')
        self.player.x, self.player.y = 3520, lift.top + self.player.FOOT_OFFSET
        self.player.grounded = True
        self.tick(6)
        self.assertEqual(lift.top, lift.low)
        self.assertAlmostEqual(self.player.bottom, lift.low)
        self.player.enter_level(self.level)
        self.assertEqual(lift.top, lift.low)
        self.assertFalse(switch.active)

    def test_elevator_reverses_midway_and_does_not_carry_airborne_player(self):
        lift = self.level.elevator
        self.level.elevator_switch.active = True
        self.level.update(2, self.player)
        self.assertEqual(lift.top, lift.low + 260)
        y = self.player.y
        self.level.elevator_switch.active = False
        self.level.update(.5, self.player)
        self.assertEqual(lift.top, lift.low + 195)
        self.assertEqual(self.player.y, y)

    def test_small_ground_contours_can_be_walked_without_invisible_walls(self):
        self.player.keys.add(pico2d.SDLK_d)
        self.tick(.7)
        self.assertGreater(self.player.x, 230)
        self.assertLess(self.player.x, 315)

    def test_original_jump_height_and_temporary_green_climbing_platforms(self):
        self.assertEqual(self.level.jump_speed, self.player.JUMP_SPEED)
        vine = self.level.vines[0]
        self.player.x, self.player.y = 570, 78 + self.player.FOOT_OFFSET
        self.player.color = 'green'
        self.assertTrue(self.colors.interact_at(580, 120, self.level, self.player))
        self.assertTrue(vine.active)
        self.assertTrue(all(p in self.level.collision_platforms() for p in vine.leaves()))
        self.player.handle_event(type('Event', (), {
            'type': pico2d.SDL_KEYDOWN, 'key': pico2d.SDLK_SPACE})())
        highest = self.player.bottom
        for _ in range(120):
            self.tick(1/120)
            highest = max(highest, self.player.bottom)
        self.assertLessEqual(highest, 185)
        self.assertTrue(self.player.grounded)
        self.assertAlmostEqual(self.player.bottom, vine.leaves()[0].top, delta=1)

    def test_elevator_destination_allows_exit_to_the_right_ledge(self):
        lift = self.level.elevator
        self.level.elevator_switch.active = True
        lift.top = lift.high
        self.player.x, self.player.y = 3580, lift.high + self.player.FOOT_OFFSET
        self.player.grounded = True
        self.player.keys.add(pico2d.SDLK_d)
        self.player.handle_event(type('Event', (), {
            'type': pico2d.SDL_KEYDOWN, 'key': pico2d.SDLK_SPACE})())
        self.tick(.65)
        self.player.keys.discard(pico2d.SDLK_SPACE)
        self.tick(1.15)
        self.player.keys.clear()
        self.tick(.2)
        self.assertGreater(self.player.x, 3900)
        self.assertTrue(self.player.grounded)
        self.assertAlmostEqual(self.player.bottom, 828, delta=3)


if __name__ == '__main__':
    unittest.main()
