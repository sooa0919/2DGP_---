import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.settings import SCREEN_HEIGHT
from code.title import TitleScreen


class TitleTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', side_effect=lambda path: Mock(h=529)):
            self.title = TitleScreen()

    def point(self, name, event_type=pico2d.SDL_MOUSEBUTTONDOWN,
              button=pico2d.SDL_BUTTON_LEFT):
        left, bottom, right, top = self.title.bounds(name)
        return Event(type=event_type, button=button,
                     x=(left + right) / 2, y=SCREEN_HEIGHT - (bottom + top) / 2)

    def test_click_sound_only_plays_for_enabled_buttons_on_left_press(self):
        click = self.title.on_click = Mock()
        self.title.handle_event(self.point('settings', pico2d.SDL_MOUSEMOTION))
        self.title.handle_event(self.point('settings', button=pico2d.SDL_BUTTON_RIGHT))
        self.title.handle_event(Event(type=pico2d.SDL_MOUSEBUTTONDOWN, button=1, x=0, y=0))
        click.assert_not_called()
        self.title.handle_event(self.point('start'))
        self.title.handle_event(self.point('new', pico2d.SDL_MOUSEBUTTONUP))
        self.title.handle_event(self.point('load'))
        click.assert_called_once()
        self.title.handle_event(self.point('new'))
        self.assertEqual(click.call_count, 2)

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
        self.assertEqual(calls[0].args[1], 529 - 210 - 120)
        self.assertEqual(calls[1].args[1], 529 - 330 - 170)
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
             patch.object(main, 'TitleScreen'), patch.object(main, 'MusicManager'), \
             patch.object(main, 'Level') as level:
            main.main()
        level.assert_not_called()

    def test_new_png_background_and_buttons_are_loaded_directly(self):
        from code.settings import IMAGE_ROOT, SCREEN_WIDTH
        with patch('pico2d.load_image', return_value=Mock(h=529)) as load:
            title = TitleScreen()
        self.assertEqual([c.args[0] for c in load.call_args_list],
                         [str(IMAGE_ROOT / 'ui/title.png'), str(IMAGE_ROOT / 'ui/title_button.png')])
        title.update(10)
        title.draw()
        title.background.draw.assert_called_with(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                                  SCREEN_WIDTH, SCREEN_HEIGHT)


if __name__ == '__main__':
    unittest.main()
