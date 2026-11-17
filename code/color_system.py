"""One blue color shared between the character and the clicked water pool."""
import pico2d

from .settings import SCREEN_HEIGHT, SCREEN_WIDTH


class ColorSystem:
    INTERACTION_RADIUS = 110

    def __init__(self):
        self.left_down = False

    def handle_event(self, event, level, player, camera_x):
        if event.type == pico2d.SDL_MOUSEBUTTONUP and event.button == pico2d.SDL_BUTTON_LEFT:
            self.left_down = False
        elif event.type == pico2d.SDL_WINDOWEVENT and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
            self.left_down = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_r:
            player.enter_level(level)
            self.left_down = False
        elif event.type == pico2d.SDL_MOUSEBUTTONDOWN and event.button == pico2d.SDL_BUTTON_LEFT:
            if not self.left_down:
                # SDL logical-size rendering already maps mouse events to the game view.
                if 0 <= event.x < SCREEN_WIDTH and 0 <= event.y < SCREEN_HEIGHT:
                    self.interact_at(event.x + camera_x, SCREEN_HEIGHT - event.y, level, player)
            self.left_down = True

    def interact_at(self, x, y, level, player):
        if (player.x - x) ** 2 + (player.y - y) ** 2 > self.INTERACTION_RADIUS ** 2:
            return False
        pool = next((w for w in level.water
                     if w.left <= x < w.right and w.bottom <= y <= w.top), None)
        if pool is None or player.has_blue == pool.has_blue:
            return False
        player.has_blue, pool.has_blue = pool.has_blue, player.has_blue
        pool.animation_time = 0.0
        if pool.solid:
            player.resolve_solid_water(pool)
        return True
