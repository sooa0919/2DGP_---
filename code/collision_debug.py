"""Optional overlay of the current physics and interaction bounds."""
import pico2d

from .settings import SCREEN_WIDTH, SCREEN_HEIGHT


class CollisionDebug:
    def __init__(self):
        self.visible = False
        self.key_down = False

    def handle_event(self, event, enabled=True):
        if event.type == pico2d.SDL_WINDOWEVENT:
            if event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
                self.key_down = False
        elif event.type == pico2d.SDL_KEYUP and event.key == pico2d.SDLK_c:
            self.key_down = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_c:
            if enabled and not self.key_down:
                self.visible = not self.visible
            self.key_down = True

    @staticmethod
    def box(item, camera_x, camera_y, color):
        left, right = item.left - camera_x, item.right - camera_x
        bottom, top = item.bottom - camera_y, item.top - camera_y
        if right < 0 or left > SCREEN_WIDTH or top < 0 or bottom > SCREEN_HEIGHT:
            return
        pico2d.draw_rectangle(round(left), round(bottom), round(right), round(top),
                              *color, filled=False)

    def draw(self, level, player, camera_x, camera_y=0):
        if not self.visible:
            return
        for platform in level.collision_platforms():
            self.box(platform, camera_x, camera_y,
                     (100, 255, 110) if platform.one_way else (255, 75, 75))
        # Liquid water has no solid collider but still detects immersion.
        for water in level.water:
            if water.has_blue:
                for part in getattr(water, 'frozen_platforms', (water,)):
                    self.box(part, camera_x, camera_y, (70, 130, 255))
        for target in list(getattr(level, 'devices', ())) + list(getattr(level, 'color_sources', ())):
            self.box(target, camera_x, camera_y, (255, 220, 70))
        self.box(player, camera_x, camera_y, (70, 240, 255))
