import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.settings import SCREEN_HEIGHT
from code.title import TitleScreen


class TitleTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', return_value=Mock(h=887)):
            self.title = TitleScreen()

    def point(self, name, event_type=pico2d.SDL_MOUSEBUTTONDOWN,
              button=pico2d.SDL_BUTTON_LEFT):
        left, bottom, right, top = self.title.bounds(name)
        return Event(type=event_type, button=button,
                     x=(left + right) / 2, y=SCREEN_HEIGHT - (bottom + top) / 2)

    def test_menu_flow_requires_two_separate_clicks(self):
        self.assertEqual(self.title.buttons, ('start', 'settings', 'quit'))
        self.assertIsNone(self.title.handle_event(self.point('start')))
        self.assertEqual(self.title.buttons, ('new', 'load'))
        self.assertIsNone(self.title.handle_event(self.point('new', pico2d.SDL_MOUSEBUTTONUP)))
        self.assertIsNone(self.title.handle_event(self.point('load')))
        self.assertEqual(self.title.handle_event(self.point('new')), 'new')

    def test_hover_uses_lower_frame_and_clears_outside(self):
        self.title.handle_event(self.point('settings', pico2d.SDL_MOUSEMOTION))
        self.assertEqual(self.title.hovered, 'settings')
        self.title.draw()
        calls = self.title.sheet.clip_draw.call_args_list
        self.assertEqual(calls[0].args[1], 887 - 230 - 175)
        self.assertEqual(calls[1].args[1], 887 - 437 - 175)
        self.title.handle_event(Event(type=pico2d.SDL_MOUSEMOTION, x=-1, y=-1))
        self.assertIsNone(self.title.hovered)

    def test_only_left_click_activates_and_escape_returns_to_main(self):
        self.assertIsNone(self.title.handle_event(self.point('start', button=pico2d.SDL_BUTTON_RIGHT)))
        self.assertEqual(self.title.menu, 'main')
        self.assertEqual(self.title.handle_event(self.point('settings')), 'settings')
        self.assertEqual(self.title.handle_event(self.point('quit')), 'quit')
        self.title.handle_event(self.point('start'))
        self.title.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_ESCAPE))
        self.assertEqual(self.title.buttons, ('start', 'settings', 'quit'))

    def test_main_defers_level_creation_until_new_game(self):
        import main
        with patch.multiple(main.pico2d, open_canvas=Mock(), close_canvas=Mock(),
                            get_events=Mock(return_value=[Event(type=pico2d.SDL_QUIT)])), \
             patch.object(main, 'configure_fullscreen'), \
             patch.object(main, 'TitleScreen'), patch.object(main, 'Level') as level:
            main.main()
        level.assert_not_called()


if __name__ == '__main__':
    unittest.main()
