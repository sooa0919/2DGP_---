"""Run the jungle side-scrolling scene with `python main.py`."""

from time import perf_counter

import pico2d

from code.background import Background
from code.camera import Camera
from code.player import Player
from code.settings import SCREEN_HEIGHT, SCREEN_WIDTH, WORLD_WIDTH


def main():
    pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
    try:
        background = Background()
        player = Player()
        camera = Camera(SCREEN_WIDTH, WORLD_WIDTH)
        previous = perf_counter()
        running = True
        while running:
            now = perf_counter()
            dt = min(now - previous, 0.05)
            previous = now
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT or (
                    event.type == pico2d.SDL_KEYDOWN
                    and event.key == pico2d.SDLK_ESCAPE
                ):
                    running = False
                else:
                    player.handle_event(event)
            if not running:
                break
            player.update(dt)
            camera.follow(player.x)
            pico2d.clear_canvas()
            background.draw(camera.x)
            player.draw(camera.x)
            pico2d.update_canvas()
            pico2d.delay(0.001)
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
