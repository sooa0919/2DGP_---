import unittest
from types import SimpleNamespace as Event
from unittest.mock import patch

import pico2d

from code.collision_debug import CollisionDebug
from code.level import Platform


class CollisionDebugTests(unittest.TestCase):
    def test_c_toggles_once_per_press_and_keyup_works_while_menu_is_open(self):
        debug = CollisionDebug()
        down = Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_c)
        up = Event(type=pico2d.SDL_KEYUP, key=pico2d.SDLK_c)
        self.assertFalse(debug.visible)
        debug.handle_event(down)
        debug.handle_event(down)
        self.assertTrue(debug.visible)
        debug.handle_event(up, enabled=False)
        debug.handle_event(down)
        self.assertFalse(debug.visible)
        debug.handle_event(up)
        debug.handle_event(down, enabled=False)
        self.assertFalse(debug.visible)

    def test_hidden_overlay_draws_nothing(self):
        with patch('pico2d.draw_rectangle') as draw:
            CollisionDebug().draw(None, None, 0)
            draw.assert_not_called()

    def test_overlay_follows_camera_and_reads_current_moving_platforms(self):
        debug = CollisionDebug()
        debug.visible = True
        platform = Platform(400, 200, 500, 212, one_way=True)
        player = Platform(420, 212, 480, 280)
        level = Event(collision_platforms=lambda: [platform], water=[], devices=[], color_sources=[])
        with patch('pico2d.draw_rectangle') as draw:
            debug.draw(level, player, 300, 100)
            self.assertEqual(draw.call_args_list[0].args[:4], (100, 100, 200, 112))
            self.assertEqual(draw.call_args_list[-1].args[:4], (120, 112, 180, 180))
            platform = Platform(400, 300, 500, 312, one_way=True)
            debug.draw(level, player, 300, 100)
            self.assertEqual(draw.call_args_list[-2].args[:4], (100, 200, 200, 212))


if __name__ == '__main__':
    unittest.main()
