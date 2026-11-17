"""Render game draw calls, including Galmuri UI, without a native window."""
import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.preview_levels as renderer
from code.tutorial_level import TutorialLevel
from code.temple import TempleBackground
from code.player import Player
from code.color_system import ColorSystem
from code.tutorial import Tutorial


class Font:
    def __init__(self, path, size):
        self.font = ImageFont.truetype(path, size)

    def draw(self, x, y, text, color):
        ImageDraw.Draw(renderer.canvas).text((round(x), round(648-y)), text,
                                             font=self.font, fill=color, anchor='lm')


def rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
    draw = ImageDraw.Draw(renderer.canvas)
    draw.rectangle((int(x1), int(648-y2), int(x2), int(648-y1)),
                   fill=(r,g,b) if filled else None, outline=(r,g,b))


def main():
    out = Path('previews')
    with patch('pico2d.load_image', side_effect=renderer.Sprite), \
         patch('pico2d.load_font', side_effect=Font), \
         patch('pico2d.draw_rectangle', side_effect=rectangle):
        level = TutorialLevel()
        bg = TempleBackground(level)
        player = Player(level)
        player.enter_level(level)
        colors, tutorial = ColorSystem(), Tutorial()

        def render(camera, show_ui=True):
            renderer.canvas = Image.new('RGB', (1152,648))
            bg.draw(camera)
            player.draw(camera)
            bg.draw_overlay(camera, player)
            if show_ui:
                tutorial.draw(level, player, colors, camera)
            return renderer.canvas.copy()

        render(0).save(out / 'tutorial_start.png')
        tutorial.moved = tutorial.jumped = tutorial.fell = True
        player.x = 704
        tutorial.mouse_pos = (736, 200)
        render(0).save(out / 'tutorial_hover.png')
        colors.interact_at(736, 200, level, player)
        tutorial.update(.1, level, player, colors)
        render(0).save(out / 'tutorial_blue.png')
        frames = []
        for _ in range(16):
            bg.update(.08)
            tutorial.time += .08
            frames.append(render(0))
        frames[0].save(out/'tutorial_waterfall.gif', save_all=True,
                       append_images=frames[1:], duration=80, loop=0)
        overview = Image.new('RGB', (level.width, 648))
        tutorial.message = None
        for left in range(0, level.width, 1152):
            camera = min(left, level.width - 1152)
            shot = render(camera, show_ui=False)
            width = min(1152, level.width-left)
            overview.paste(shot.crop((left-camera, 0, left-camera+width, 648)), (left,0))
        overview.resize((2048,324)).save(out/'tutorial_overview.png')


if __name__ == '__main__':
    main()
