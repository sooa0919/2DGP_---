"""Open the title menu, then start the tutorial with `python main.py`."""

from time import perf_counter

import pico2d

from code.blockout import ForestBlockout as Background
from code.camera import Camera
from code.collision_debug import CollisionDebug
from code.display import clear_canvas, configure_fullscreen
from code.player import Player
from code.illustrated_level import IllustratedLevel as Level
from code.tutorial import Tutorial
from code.color_system import ColorSystem
from code.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from code.title import TitleScreen
from code.loading import LoadingScreen
from code.settings_menu import SettingsMenu
from code.audio import MusicManager


def scene_position(camera, level):
    effect = getattr(level, 'door_effect', None)
    return camera.view_position(*(effect.shake_offset if effect else (0, 0)))


def main():
    pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
    music = None
    try:
        configure_fullscreen()
        music = MusicManager()
        music.play('title')
        title = TitleScreen(on_click=music.play_click)
        loading = None
        settings_ui = None
        settings_open = False
        collision_debug = CollisionDebug()
        previous = perf_counter()
        running = True
        while running:
            now = perf_counter()
            dt = min(now - previous, 0.05)
            previous = now
            for event in pico2d.get_events():
                collision_debug.handle_event(event, enabled=(
                    title is None and loading is None and not settings_open))
                if event.type == pico2d.SDL_QUIT:
                    running = False
                    break
                elif loading is not None:
                    continue
                elif settings_open:
                    action = settings_ui.handle_event(event)
                    music.set_volume(settings_ui.volumes['bgm'])
                    music.set_effects_volume(settings_ui.volumes['sfx'])
                    if action == 'quit':
                        running = False
                        break
                    if action in ('close', 'title'):
                        settings_open = False
                        if action == 'title':
                            title = TitleScreen(on_click=music.play_click)
                            music.play('title')
                            level = background = player = camera = colors = tutorial = None
                        previous = perf_counter()
                        dt = 0.0
                        break
                elif title is not None:
                    action = title.handle_event(event)
                    if action == 'quit':
                        running = False
                        break
                    if action == 'new':
                        loading = LoadingScreen()
                        break
                    if action == 'settings':
                        if settings_ui is None:
                            settings_ui = SettingsMenu(on_click=music.play_click)
                        settings_ui.open(in_game=False)
                        settings_open = True
                else:
                    if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
                        if settings_ui is None:
                            settings_ui = SettingsMenu(on_click=music.play_click)
                        settings_ui.open(in_game=True)
                        settings_open = True
                        player.keys.clear()
                        colors.left_down = False
                        if tutorial:
                            tutorial.pressed.clear()
                            tutorial.mouse_pos = None
                        continue
                    if tutorial:
                        tutorial.handle_event(event, player)
                        if tutorial.paused:
                            continue
                    view_x, view_y = scene_position(camera, level)
                    colors.handle_event(event, level, player, view_x, view_y)
                    if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_r:
                        camera.snap_to(player.x, player.y)
                    player.handle_event(event)
            if not running:
                break
            if title is not None:
                title.update(dt)
            if loading is not None:
                if loading.needs_level:
                    level = Level()
                    collision_debug.visible = False
                    background = Background(level)
                    player = Player(level)
                    player.enter_level(level)
                    camera = Camera(SCREEN_WIDTH, level.width,
                                    getattr(level, 'height', SCREEN_HEIGHT))
                    colors = ColorSystem()
                    tutorial = Tutorial() if getattr(level, 'is_tutorial', False) else None
                    title = None
                    loading.ready = True
                    previous = perf_counter()
                    dt = 0.0
                loading.update(dt)
                if loading.phase in ('in', 'done'):
                    music.play('tutorial')
                if loading.phase in ('out', 'loading'):
                    clear_canvas()
                    if loading.phase == 'out':
                        title.draw()
                    loading.draw()
                    pico2d.update_canvas()
                    pico2d.delay(0.001)
                    continue
            if title is not None:
                clear_canvas()
                title.draw()
                if settings_open:
                    settings_ui.draw()
                pico2d.update_canvas()
                pico2d.delay(0.001)
                continue
            if not settings_open and loading is None and (not tutorial or not tutorial.paused):
                player.update(dt)
                if hasattr(level, 'update'):
                    level.update(dt, player)
                background.update(dt)
            if tutorial and loading is None and not settings_open:
                tutorial.update(dt, level, player, colors)
            camera.follow(player.x, player.y, dt)
            view_x, view_y = scene_position(camera, level)
            clear_canvas()
            background.draw(view_x, view_y)
            player.draw(view_x, view_y)
            background.draw_overlay(view_x, player, view_y)
            collision_debug.draw(level, player, view_x, view_y)
            if tutorial:
                tutorial.draw(level, player, colors, view_x, view_y)
            if settings_open:
                settings_ui.draw()
            if loading is not None:
                loading.draw()
                if loading.done:
                    loading = None
            pico2d.update_canvas()
            pico2d.delay(0.001)
    finally:
        if music is not None:
            music.close()
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
