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
    out.mkdir(exist_ok=True)
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
                tutorial.update(0, level, player, colors)
                tutorial.draw(level, player, colors, camera_x, camera_y)
            return renderer.canvas.copy()

        def place(x, floor):
            player.x, player.y = x, floor + player.FOOT_OFFSET
            player.grounded = True
            player.velocity_y = 0

        render(0).save(out / 'tutorial_start.png')
        source = level.color_sources[0]
        colors.interact_at(source.x, source.y, level, player)
        place(288, 96)
        colors.interact_at(321, 132, level, player)
        render(0).save(out / 'tutorial_water.png')

        player.enter_level(level)
        level.progress = 1
        player.color = 'green'
        place(808, 96)
        colors.interact_at(808, 132, level, player)
        place(808, 336)
        render(600).save(out / 'tutorial_green.png')

        player.enter_level(level)
        level.progress = 6
        level.vines[3].active = True
        place(3240, 480)
        drop = level.droplets[0]
        for i, part in enumerate(level.droplets):
            part.top = 96 + (560 - 96 - i * 220) % 880
            part.bottom = part.top - 80
        colors.interact_at(drop.left + 1, player.y, level, player)
        place(3440, 560)
        level.update(0, player)
        render(2944, 200).save(out / 'tutorial_frozen_water.png')
        player.color = 'yellow'
        place(3696, 600)
        colors.interact_at(3713, 636, level, player)
        render(2944, 200).save(out / 'tutorial_yellow.png')
        place(4040, 96)
        level.update(0, player)
        render(level.width - 1152).save(out / 'tutorial_exit.png')

        player.enter_level(level)
        rates = bg.scroll_rates
        bg.scroll_rates = (1,) * 5
        overview = Image.new('RGB', (level.width, level.height))
        for bottom in range(0, level.height, 648):
            camera_y = min(bottom, level.height - 648)
            height = min(648, level.height - bottom)
            for left in range(0, level.width, 1152):
                camera_x = min(left, level.width - 1152)
                width = min(1152, level.width - left)
                shot = render(camera_x, camera_y, show_ui=False)
                top = 648 - (bottom - camera_y) - height
                overview.paste(shot.crop((left-camera_x, top, left-camera_x+width, top+height)),
                               (left, level.height-bottom-height))
        overview.resize((2048,504), Image.Resampling.NEAREST).save(out / 'tutorial_overview.png')
        bg.scroll_rates = rates

        player.enter_level(level)
        level.progress = 6
        level.vines[3].active = True
        place(3240,480)
        drop = level.droplets[0]
        for i, part in enumerate(level.droplets):
            part.top = 96 + (600 - 96 - i * 220) % 880
            part.bottom = part.top - 80
        frames=[]
        for frame in range(36):
            if frame in (10,24):
                y=max(drop.bottom+1,min(player.y,drop.top-1))
                colors.interact_at(drop.left+1,y,level,player)
            player.update(.1)
            level.update(.1,player)
            frames.append(render(2944,200))
        frames[0].save(out / 'tutorial_falling_water.gif',save_all=True,
                       append_images=frames[1:],duration=100,loop=0)


if __name__ == '__main__':
    main()
