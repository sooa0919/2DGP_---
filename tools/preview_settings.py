"""Render the current settings design and its working volume sliders."""
import sys
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace as Event

from PIL import Image
import pico2d

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.preview_levels as renderer
from tools.preview_tutorial import Font, rectangle
from code.settings import ROOT
from code.settings_menu import SettingsMenu
from code.title import TitleScreen
from code.temple import TempleBackground
from code.tutorial_level import TutorialLevel
from code.player import Player


def main():
    with patch('pico2d.load_image', side_effect=renderer.Sprite), \
         patch('pico2d.load_font', side_effect=Font), \
         patch('pico2d.draw_rectangle', side_effect=rectangle):
        settings, title = SettingsMenu(), TitleScreen()
        settings.open(in_game=False)
        for tab in range(4):
            renderer.canvas = Image.new('RGB', (1152, 648))
            title.draw()
            settings.tab = tab
            settings.draw()
            renderer.canvas.save(ROOT / f'previews/settings_title_{tab}.png')
        settings.tab = 2
        settings.handle_event(Event(type=pico2d.SDL_MOUSEBUTTONDOWN,
                                    button=1, x=714, y=648-370))
        frames = []
        for value in list(range(0, 101, 5)) + list(range(95, -1, -5)):
            x = settings.SLIDER_LEFT + (settings.SLIDER_RIGHT-settings.SLIDER_LEFT) * value/100
            settings.handle_event(Event(type=pico2d.SDL_MOUSEMOTION, x=x, y=648-370))
            renderer.canvas = Image.new('RGB', (1152, 648))
            title.draw()
            settings.draw()
            frames.append(renderer.canvas.copy())
        settings.handle_event(Event(type=pico2d.SDL_MOUSEBUTTONUP, button=1, x=714, y=648-370))
        frames[0].save(ROOT / 'previews/settings_slider.gif', save_all=True,
                       append_images=frames[1:], duration=70, loop=0)
        level = TutorialLevel()
        background, player = TempleBackground(level), Player(level)
        player.enter_level(level)
        renderer.canvas = Image.new('RGB', (1152, 648))
        background.draw(0, 0)
        player.draw(0)
        background.draw_overlay(0, player, 0)
        settings.tab = 0
        settings.open(in_game=True)
        settings.draw()
        renderer.canvas.save(ROOT / 'previews/settings_play.png')


if __name__ == '__main__':
    main()
