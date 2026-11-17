"""Run the ruined-temple tutorial with `python main.py`."""

from time import perf_counter

import pico2d

from code.temple import TempleBackground as Background
from code.camera import Camera
from code.display import clear_canvas, configure_fullscreen
from code.player import Player
from code.tutorial_level import TutorialLevel as Level
from code.tutorial import Tutorial
from code.color_system import ColorSystem
from code.settings import SCREEN_HEIGHT, SCREEN_WIDTH


def main():
    pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
    try:
        configure_fullscreen()
        level = Level()
        background = Background(level)
        player = Player(level)
        player.enter_level(level)
        camera = Camera(SCREEN_WIDTH, level.width)
        colors = ColorSystem()
        tutorial = Tutorial() if getattr(level, 'is_tutorial', False) else None
        previous = perf_counter()
        running = True
        while running:
            now = perf_counter()
            dt = min(now - previous, 0.05)
            previous = now
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    running = False
                else:
                    if tutorial:
                        tutorial.handle_event(event, player)
                        if tutorial.paused:
                            continue
                    colors.handle_event(event, level, player, camera.x)
                    player.handle_event(event)
            if not running:
                break
            if not tutorial or not tutorial.paused:
                player.update(dt)
                background.update(dt)
            if tutorial:
                tutorial.update(dt, level, player, colors)
            camera.follow(player.x)
            clear_canvas()
            background.draw(camera.x)
            player.draw(camera.x)
            background.draw_overlay(camera.x, player)
            if tutorial:
                tutorial.draw(level, player, colors, camera.x)
            pico2d.update_canvas()
            pico2d.delay(0.001)
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
