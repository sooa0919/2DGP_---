"""Render stage-one collision, waterfall frames and elevator travel headlessly."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import preview_levels as renderer
from tools.preview_tutorial import rectangle
from code.illustrated_level import IllustratedLevel
from code.blockout import ForestBlockout
from code.player import Player
from code.camera import Camera


def main():
    out = Path('previews/stage1')
    out.mkdir(exist_ok=True)
    with patch('pico2d.load_image', side_effect=renderer.Sprite), \
            patch('pico2d.draw_rectangle', side_effect=rectangle):
        level = IllustratedLevel()
        bg = ForestBlockout(level)
        player = Player(level)
        player.enter_level(level)

        def render(x=0, y=0, collisions=False):
            renderer.canvas = Image.new('RGB', (1152, 648))
            bg.draw(x, y)
            player.draw(x, y)
            bg.draw_overlay(x, player, y)
            if collisions:
                draw = ImageDraw.Draw(renderer.canvas)
                for p in level.collision_platforms():
                    if p.right < x or p.left > x + 1152:
                        continue
                    draw.rectangle((p.left-x, 648-p.top+y, p.right-x, 648-p.bottom+y),
                                   outline=(255, 60, 80), width=1)
            return renderer.canvas.copy()

        render().save(out / 'start_gray.png')
        render(collisions=True).save(out / 'start_collision.png')
        render(1900, 100, collisions=True).save(out / 'middle_collision.png')
        render(2944, 360, collisions=True).save(out / 'end_collision.png')
        render(2944, 200).save(out / 'gray_map_colored_sources.png')
        level.vines[0].active = True
        render().save(out / 'temporary_green_vine.png')
        level.vines[0].active = False
        level.water[0].has_blue = True
        for i in range(3):
            level.water[0].animation_time = i * .22
            render().save(out / f'water_{i+1}.png')
        player.x, player.y = 347, 310
        render().save(out / 'inside_transparent_water.png')
        player.x, player.y = level.spawn[0], level.spawn[1] + player.FOOT_OFFSET
        fall_frames = []
        for i in range(9):
            level.water[0].animation_time = (i % 3) * .22
            fall_frames.append(render())
        fall_frames[0].save(out / 'waterfall.gif', append_images=fall_frames[1:],
                            save_all=True, duration=220, loop=0)
        player.x = 3520
        player.y = level.elevator.top + player.FOOT_OFFSET
        player.grounded = True
        render(2944).save(out / 'elevator_down.png')
        level.elevator_switch.active = True
        frames = []
        for _ in range(52):
            level.update(.1, player)
            camera_y = min(360, max(0, player.y - 324))
            frames.append(render(2944, camera_y))
        frames[-1].save(out / 'elevator_up.png')
        level.elevator_switch.active = False
        for _ in range(52):
            level.update(.1, player)
            camera_y = min(360, max(0, player.y - 324))
            frames.append(render(2944, camera_y))
        frames[0].save(out / 'elevator.gif', append_images=frames[1:],
                        save_all=True, duration=100, loop=0)
        player.enter_level(level)
        player.x = 3060
        floor = max(p.top for p in level.platforms if p.left <= player.x < p.right and p.top < 700)
        player.y = floor + player.FOOT_OFFSET
        camera = Camera(1152, level.width, level.height)
        camera.snap_to(player.x, player.y)
        closed = render(*camera.view_position())
        frames = [closed.resize((864, 486), Image.Resampling.LANCZOS) for _ in range(6)]
        level.door_switch.active = True
        for i in range(112):
            level.update(1 / 30, player)
            camera.follow(*level.camera_target(player), 1 / 30)
            shot = render(*camera.view_position(*level.door_effect.shake_offset))
            frames.append(shot.resize((864, 486), Image.Resampling.LANCZOS))
            if i == 23:
                shot.save(out / 'door_open_dust.png')
            if i == 41:
                shot.save(out / 'door_half_open.png')
        frames[0].save(out / 'door_opening.gif', append_images=frames[1:],
                        save_all=True, duration=33, loop=0)


if __name__ == '__main__':
    main()
