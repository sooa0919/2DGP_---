"""Preview actual transfer draw calls for all supplied character colors."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.preview_levels as renderer
from tools.preview_tutorial import rectangle
from code.color_system import ColorSystem
from code.player import Player
from code.settings import ROOT, FONT_PATH
from code.temple import TempleBackground
from code.tutorial_level import TutorialLevel


def main():
    output = ROOT / 'previews'
    with patch('pico2d.load_image', side_effect=renderer.Sprite), \
         patch('pico2d.draw_rectangle', side_effect=rectangle):
        level = TutorialLevel()
        background = TempleBackground(level)
        player = Player(level)
        player.enter_level(level)
        colors = ColorSystem()
        frames = []

        def render():
            renderer.canvas = Image.new('RGB', (1152, 648))
            background.draw(0, 0)
            player.draw(0, 0)
            background.draw_overlay(0, player, 0)
            return renderer.canvas.crop((0, 416, 448, 648)).resize((896, 464), Image.Resampling.NEAREST)

        source = level.color_sources[0]
        colors.interact_at(source.x, source.y, level, player)
        for _ in range(8):
            frames.append(render())
            player.interaction.update(.1)
        frames.extend([render()] * 3)
        player.x = 304
        basin = level.water[1]
        colors.interact_at(basin.left, basin.top - 4, level, player)
        for _ in range(8):
            frames.append(render())
            player.interaction.update(.1)
        frames.extend([render()] * 3)
        frames[0].save(output / 'interaction_blue.gif', save_all=True,
                       append_images=frames[1:], duration=100, loop=0)

        font = ImageFont.truetype(str(FONT_PATH), 20)
        previews = []
        for extracting in (True, False):
            sequence = []
            for frame in range(8):
                renderer.canvas = Image.new('RGB', (1152, 648), (26, 29, 37))
                for index, color in enumerate(('blue', 'green', 'yellow')):
                    player.x, player.y = 192 + index * 384, 276
                    player.start_interaction(color, extracting)
                    player.interaction.time = frame / 10
                    player.draw(0)
                    ImageDraw.Draw(renderer.canvas).text((player.x, 440),
                        f'{color}: {"extract" if extracting else "give"}',
                        font=font, anchor='mt', fill='white')
                sequence.append(renderer.canvas.crop((0, 270, 1152, 480)))
            previews.extend(sequence)
        previews[0].save(output / 'interaction_colors.gif', save_all=True,
                         append_images=previews[1:], duration=100, loop=0)
        previews[4].save(output / 'interaction_colors.png')


if __name__ == '__main__':
    main()
