import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.settings_menu import SettingsMenu


class SettingsMenuTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', return_value=Mock(w=538, h=1086)), \
             patch('pico2d.load_font', return_value=Mock()):
            self.menu = SettingsMenu()
        self.menu.open(in_game=True)

    def click(self, x, y, button=pico2d.SDL_BUTTON_LEFT):
        return self.menu.handle_event(Event(type=pico2d.SDL_MOUSEBUTTONDOWN,
                                            x=x + self.menu.panel_offset, y=648-y, button=button))

    def click_bounds(self, bounds, button=pico2d.SDL_BUTTON_LEFT):
        left, bottom, right, top = bounds
        return self.click((left + right) / 2, (bottom + top) / 2, button)

    def show_settings(self):
        self.click_bounds(self.menu.ACTION_BOUNDS['settings'])

    def test_settings_opens_panel_and_back_returns_to_menu_before_escape_closes(self):
        self.assertFalse(self.menu.panel_open)
        self.show_settings()
        self.assertTrue(self.menu.panel_open)
        for index, bounds in enumerate(self.menu.TAB_BOUNDS):
            self.click_bounds(bounds)
            self.assertEqual(self.menu.tab, index)
        self.click_bounds(self.menu.TAB_BOUNDS[0], pico2d.SDL_BUTTON_RIGHT)
        self.assertEqual(self.menu.tab, 1)
        self.assertIsNone(self.click(10, 10))
        self.assertIsNone(self.click_bounds(self.menu.CLOSE_BOUNDS))
        self.assertFalse(self.menu.panel_open)
        self.assertEqual(self.menu.handle_event(Event(type=pico2d.SDL_KEYDOWN,
                                                      key=pico2d.SDLK_ESCAPE)), 'close')

    def test_centered_menu_is_replaced_by_panel_and_hidden_actions_are_inactive(self):
        self.assertEqual(201 + self.menu.panel_offset, 576)
        self.show_settings()
        self.assertEqual(742 + self.menu.panel_offset, 576)
        self.assertEqual(self.menu.action_bounds, {})
        self.assertIsNone(self.click_bounds(self.menu.ACTION_BOUNDS['quit']))
        self.menu.images['menu'] = Mock()
        self.menu.draw()
        self.menu.images['menu'].draw.assert_not_called()
        self.click_bounds(self.menu.CLOSE_BOUNDS)
        self.assertEqual(201 + self.menu.panel_offset, 576)
        self.assertEqual(tuple(self.menu.action_bounds), ('settings', 'save', 'title', 'quit'))

    def test_settings_pages_draw_and_reopening_retains_volume(self):
        self.show_settings()
        self.menu.tab = 0
        self.assertIsNone(self.click(832, 370))
        self.assertEqual(self.menu.volumes['bgm'], 50)
        self.assertEqual(self.menu.tab, 0)
        self.assertIsNone(self.click(280, 85))
        self.menu.open(in_game=True)
        self.assertIsNone(self.menu.mouse)
        self.assertIsNone(self.menu.dragging)
        self.assertFalse(self.menu.panel_open)
        self.assertEqual(self.menu.volumes['bgm'], 50)
        with patch('pico2d.draw_rectangle'):
            self.menu.panel_open = True
            for self.menu.tab in range(2):
                self.menu.draw()

    def test_title_and_quit_buttons_return_actions_only_on_left_click(self):
        self.menu.open(in_game=False)
        self.assertTrue(self.menu.panel_open)
        self.assertEqual(self.menu.action_bounds, {})
        self.assertIsNone(self.click(480, 85))
        self.assertIsNone(self.click(280, 85))
        self.assertIsNone(self.click_bounds(self.menu.ACTION_BOUNDS['quit']))
        self.menu.open(in_game=True)
        self.assertEqual(tuple(self.menu.action_bounds), ('settings', 'save', 'title', 'quit'))
        self.assertEqual(self.click_bounds(self.menu.ACTION_BOUNDS['title']), 'title')
        self.assertEqual(self.click_bounds(self.menu.ACTION_BOUNDS['quit']), 'quit')
        self.assertIsNone(self.click_bounds(self.menu.ACTION_BOUNDS['title'], pico2d.SDL_BUTTON_RIGHT))
        self.assertIsNone(self.click_bounds(self.menu.ACTION_BOUNDS['quit'], pico2d.SDL_BUTTON_RIGHT))

    def test_slider_drag_clamps_releases_and_keeps_channels_independent(self):
        self.show_settings()
        self.menu.tab = 0
        self.click(714, 370)
        self.assertEqual(self.menu.volumes, {'bgm': 0, 'sfx': 80})
        self.menu.handle_event(Event(type=pico2d.SDL_MOUSEMOTION, x=1400, y=10))
        self.assertEqual(self.menu.volumes['bgm'], 100)
        self.menu.handle_event(Event(type=pico2d.SDL_MOUSEBUTTONUP, button=1,
                                     x=832 + self.menu.panel_offset, y=10))
        self.assertEqual(self.menu.volumes['bgm'], 50)
        self.menu.handle_event(Event(type=pico2d.SDL_MOUSEMOTION, x=-50, y=10))
        self.assertEqual(self.menu.volumes['bgm'], 50)
        self.click(950, 270)
        self.menu.handle_event(Event(type=pico2d.SDL_MOUSEMOTION, x=-20, y=10))
        self.assertEqual(self.menu.volumes, {'bgm': 50, 'sfx': 0})
        self.menu.handle_event(Event(type=pico2d.SDL_WINDOWEVENT,
                                     event=pico2d.SDL_WINDOWEVENT_FOCUS_LOST))
        self.assertIsNone(self.menu.dragging)
        self.click_bounds(self.menu.RESET_BOUNDS)
        self.assertEqual(self.menu.volumes, {'bgm': 80, 'sfx': 80})

    def test_slider_ignores_other_tabs_and_right_click_and_escape_cancels_drag(self):
        self.click(714, 370)
        self.assertEqual(self.menu.volumes['bgm'], 80)
        self.show_settings()
        self.menu.tab = 0
        self.click(714, 370, pico2d.SDL_BUTTON_RIGHT)
        self.assertIsNone(self.menu.dragging)
        self.click(714, 370)
        self.assertEqual(self.menu.dragging, 'bgm')
        self.menu.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_ESCAPE))
        self.assertIsNone(self.menu.dragging)
        self.assertFalse(self.menu.panel_open)

    def test_hidden_panel_and_control_tab_cannot_change_sound_and_menu_labels_are_restored(self):
        self.click(714, 370)
        self.assertEqual(self.menu.volumes['bgm'], 80)
        self.show_settings()
        self.click_bounds(self.menu.TAB_BOUNDS[1])
        self.click(714, 370)
        self.assertEqual(self.menu.volumes['bgm'], 80)
        self.menu.small.reset_mock()
        self.menu.panel_open = False
        self.menu.draw()
        labels = [call.args[2] for call in self.menu.small.draw.call_args_list if call.args[3] == (255, 255, 255)]
        self.assertEqual(labels, ['설정', '저장', '타이틀로', '종료'])

    def test_title_settings_shows_centered_panel_directly_and_returns_to_title(self):
        self.menu.open(in_game=False)
        self.menu.tab = 0
        self.menu.images['menu'] = Mock()
        self.menu.draw()
        self.menu.images['menu'].draw.assert_not_called()
        labels = [call.args[2] for call in self.menu.small.draw.call_args_list]
        self.assertIn('사운드', labels)
        self.assertIn('조작', labels)
        self.assertNotIn('기본값', labels)
        self.assertNotIn('되돌아가기', labels)
        self.click(714, 370)
        self.assertEqual(self.menu.volumes['bgm'], 0)
        self.menu.handle_event(Event(type=pico2d.SDL_MOUSEBUTTONUP, button=1, x=548, y=278))
        self.click(950, 270)
        self.assertEqual(self.menu.volumes['sfx'], 100)
        self.assertEqual(self.click(1010, 96), 'close')
        self.menu.open(in_game=False)
        self.assertEqual(self.menu.handle_event(Event(type=pico2d.SDL_KEYDOWN,
                                                      key=pico2d.SDLK_ESCAPE)), 'close')

    def test_return_to_title_allows_fresh_game_and_quit_closes_canvas(self):
        import main
        click = Event(type=pico2d.SDL_MOUSEBUTTONDOWN, button=1, x=180, y=278)
        esc = Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_ESCAPE)
        frames = iter([[click], [esc], [click], [click], [esc], [click]])
        menu = Mock(volumes={'bgm': 37, 'sfx': 80}, handle_event=Mock(side_effect=['title', 'quit']))
        music = Mock()
        title = Mock(return_value=Mock(handle_event=Mock(return_value='new')))
        factory = Mock(return_value=Event(width=1792, height=672, is_tutorial=False))
        close = Mock()
        with patch.multiple(main, configure_fullscreen=Mock(), clear_canvas=Mock(),
                            TitleScreen=title, SettingsMenu=Mock(return_value=menu),
                            MusicManager=Mock(return_value=music),
                            LoadingScreen=Mock(return_value=Mock(needs_level=True, phase='done', done=True)),
                            Level=factory, Player=Mock(return_value=Mock()),
                            Background=Mock(return_value=Mock()), Camera=Mock(return_value=Mock(x=0, y=0)),
                            ColorSystem=Mock(return_value=Mock())), \
             patch.multiple(pico2d, open_canvas=Mock(), close_canvas=close,
                            update_canvas=Mock(), delay=Mock(), get_events=lambda: next(frames)):
            main.main()
        self.assertEqual(title.call_count, 2)
        self.assertEqual(factory.call_count, 2)
        self.assertEqual([call.args[0] for call in music.play.call_args_list],
                         ['title', 'tutorial', 'title', 'tutorial'])
        self.assertTrue(all(call.args == (37,) for call in music.set_volume.call_args_list))
        self.assertEqual(music.set_volume.call_count, 2)
        music.close.assert_called_once()
        close.assert_called_once()

    def test_main_opens_from_title_and_play_and_pauses_input_and_updates(self):
        import main
        click = Event(type=pico2d.SDL_MOUSEBUTTONDOWN, button=1, x=180, y=278)
        esc = Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_ESCAPE)
        move = Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_d)
        frames = iter([[click], [move], [esc], [click], [esc], [move], [esc],
                       [Event(type=pico2d.SDL_QUIT)]])
        menu = Mock(volumes={'bgm': 80, 'sfx': 80}, handle_event=Mock(side_effect=[None, 'close', None, 'close']))
        player, background, colors = Mock(), Mock(), Mock()
        with patch.multiple(main, configure_fullscreen=Mock(), clear_canvas=Mock(),
                            TitleScreen=Mock(return_value=Mock(handle_event=Mock(side_effect=['settings', 'new']))),
                            SettingsMenu=Mock(return_value=menu), MusicManager=Mock(),
                            LoadingScreen=Mock(return_value=Mock(needs_level=True, phase='done', done=True)),
                            Level=Mock(return_value=Event(width=1792, height=672, is_tutorial=False)),
                            Player=Mock(return_value=player), Background=Mock(return_value=background),
                            Camera=Mock(return_value=Mock(x=0, y=0)), ColorSystem=Mock(return_value=colors)), \
             patch.multiple(pico2d, open_canvas=Mock(), close_canvas=Mock(),
                            update_canvas=Mock(), delay=Mock(), get_events=lambda: next(frames)):
            main.main()
        self.assertEqual(menu.open.call_count, 2)
        self.assertEqual([call.kwargs for call in menu.open.call_args_list],
                         [{'in_game': False}, {'in_game': True}])
        self.assertEqual(menu.draw.call_count, 4)
        player.handle_event.assert_not_called()
        colors.handle_event.assert_not_called()
        player.update.assert_called_once_with(0.0)
        background.update.assert_called_once_with(0.0)
        player.keys.clear.assert_called_once()
