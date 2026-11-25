"""Forest backdrop and the supplied, fully assembled stage illustration."""
import pico2d
from .display import load_pixel_image

from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .diamond import DiamondRenderer
from .stage_art import StageArt
from .door_effect import DoorEffectRenderer


class ForestBlockout:
    def __init__(self, level):
        self.level = level
        folder = IMAGE_ROOT / 'background/grayscale/background3_jungle2'
        self.layers = [load_pixel_image(str(folder / f'plx-{i}.png')) for i in range(1, 6)]
        folder = IMAGE_ROOT / 'background/background_layer/background3_jungle2'
        self.color_layers = [load_pixel_image(str(folder / f'plx-{i}.png')) for i in range(1, 6)]
        self.colored = False
        self.palette_key_down = False
        self.diamonds = DiamondRenderer()
        self.stage = StageArt(level)
        self.door_effect = DoorEffectRenderer()
        self.time = 0.0
        self.scroll_rates = (0, .12, .24, .4, .6)

    def update(self, dt):
        self.time += dt

    def handle_event(self, event, enabled=True):
        if event.type == pico2d.SDL_WINDOWEVENT:
            if event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
                self.palette_key_down = False
        elif event.type == pico2d.SDL_KEYUP and event.key == pico2d.SDLK_v:
            self.palette_key_down = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_v:
            if enabled and not self.palette_key_down:
                self.colored = not self.colored
            self.palette_key_down = True

    def draw(self, camera_x, camera_y=0):
        height = max(SCREEN_HEIGHT, self.level.height)
        width = round(height * SCREEN_WIDTH / SCREEN_HEIGHT)
        self.stage.colored = self.colored
        for layer, rate in zip(self.color_layers if self.colored else self.layers, self.scroll_rates):
            offset = round(camera_x * rate) % width
            for start in (-offset, width - offset):
                layer.draw(start + width / 2, height / 2 - camera_y, width, height)
        self.stage.draw_objects(camera_x, camera_y)
        self.diamonds.draw(self.level.color_sources, camera_x, camera_y)
        self.stage.draw_devices(camera_x, camera_y, include_water=False)
        self.stage.draw_terrain(camera_x, camera_y)

    def draw_overlay(self, camera_x, player, camera_y=0):
        self.stage.draw_water(camera_x, camera_y)
        self.door_effect.draw(self.level.door_effect, camera_x, camera_y)
