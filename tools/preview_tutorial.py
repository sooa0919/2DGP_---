"""Render the revised tile-only tutorial without opening a window."""
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
from code.camera import Camera


class Font:
    def __init__(self, path, size):
        self.font = ImageFont.truetype(path, size)

    def draw(self, x, y, text, color):
        ImageDraw.Draw(renderer.canvas).text((round(x), round(648-y)), text,
                                             font=self.font, fill=color, anchor='lm')


def rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
    ImageDraw.Draw(renderer.canvas).rectangle(
        (int(x1), int(648-y2), int(x2), int(648-y1)),
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

        def render(camera_x, camera_y=0, show_ui=True):
            renderer.canvas = Image.new('RGB', (1152,648))
            bg.draw(camera_x, camera_y)
            player.draw(camera_x, camera_y)
            bg.draw_overlay(camera_x, player, camera_y)
            if show_ui:
                tutorial.draw(level, player, colors, camera_x, camera_y)
            return renderer.canvas.copy()

        render(0).save(out / 'tutorial_start.png')
        overview = Image.new('RGB', (level.width, level.height))
        for bottom in range(0, level.height, 648):
            camera_y = min(bottom, level.height - 648)
            height = min(648, level.height - bottom)
            source_top = 648 - (bottom - camera_y) - height
            for left in range(0, level.width, 1152):
                camera_x = min(left, level.width - 1152)
                shot = render(camera_x, camera_y, show_ui=False)
                width = min(1152, level.width-left)
                overview.paste(shot.crop((left-camera_x, source_top,
                                          left-camera_x+width, source_top+height)),
                               (left, level.height-bottom-height))
        overview.save(out / 'tutorial_overview.png')
        source = level.color_sources[0]
        colors.interact_at(source.x, source.y, level, player)
        render(0, show_ui=False).save(out / 'tutorial_diamond_extract.png')
        player.x = 304
        basin = level.water[1]
        colors.interact_at(basin.left, basin.top - 4, level, player)
        player.x, player.y = 416, player.FOOT_OFFSET
        frames = []
        for _ in range(20):
            bg.update(.1)
            frames.append(render(0, show_ui=False))
        frames[0].save(out / 'tutorial_diamond_waterfall.gif', save_all=True,
                       append_images=frames[1:], duration=100, loop=0)
        frames[0].save(out / 'tutorial_water.png')
        level.reset()
        player.x, player.y = level.end_x + 32, level.end_y + player.FOOT_OFFSET
        camera = Camera(1152, level.width, level.height)
        camera.follow(player.x, player.y)
        render(camera.x, camera.y, show_ui=False).save(out / 'tutorial_exit.png')


if __name__ == '__main__':
    main()
