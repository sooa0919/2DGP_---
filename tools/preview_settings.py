"""Render the kit-based settings modal over title and gameplay scenes."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image

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
