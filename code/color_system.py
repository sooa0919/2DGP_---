"""A single convertible color shared by the player and compatible devices."""
import pico2d

from .settings import SCREEN_HEIGHT, SCREEN_WIDTH


class ColorSystem:
    INTERACTION_RADIUS = 140

    def __init__(self):
        self.left_down = False
        self.last_transfer = None
        self.transfer_serial = 0
        self.notice = ''

    @staticmethod
    def stored_color(target):
        if hasattr(target, 'stored_color'):
            return target.stored_color
        return 'blue' if target.has_blue else None

    @classmethod
    def can_exchange(cls, target, player):
        stored = cls.stored_color(target)
        required = getattr(target, 'required_color', 'blue')
        return (player.color is None and stored is not None) or (
            player.color == required and stored is None)

    def target_at(self, x, y, level, player):
        """Share exact validation between hover feedback and actual clicks."""
        if (player.x - x) ** 2 + (player.y - y) ** 2 > self.INTERACTION_RADIUS ** 2:
            return None
        targets = (list(getattr(level, 'color_sources', [])) + level.water
                   + list(getattr(level, 'devices', [])))
        return next((w for w in targets
                     if w.left <= x < w.right and w.bottom <= y <= w.top
                     and (not hasattr(w, 'contains_point') or w.contains_point(x, y))
                     and getattr(w, 'unlock_stage', 0) <= getattr(level, 'progress', 99)
                     and self.can_exchange(w, player)), None)

    def handle_event(self, event, level, player, camera_x, camera_y=0):
        if event.type == pico2d.SDL_MOUSEBUTTONUP and event.button == pico2d.SDL_BUTTON_LEFT:
            self.left_down = False
        elif event.type == pico2d.SDL_WINDOWEVENT and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
            self.left_down = False
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_r:
            player.enter_level(level)
            self.left_down = False
            self.last_transfer = None
            self.transfer_serial = 0
            self.notice = ''
        elif event.type == pico2d.SDL_KEYDOWN and event.key in (pico2d.SDLK_1, pico2d.SDLK_2, pico2d.SDLK_3):
            if player.color is not None:
                player.color = {pico2d.SDLK_1: 'blue', pico2d.SDLK_2: 'green', pico2d.SDLK_3: 'yellow'}[event.key]
                self.notice = ''
            else:
                self.notice = '색을 먼저 회수하세요.'
        elif event.type == pico2d.SDL_MOUSEBUTTONDOWN and event.button == pico2d.SDL_BUTTON_LEFT:
            if not self.left_down:
                # SDL logical-size rendering already maps mouse events to the game view.
                if 0 <= event.x < SCREEN_WIDTH and 0 <= event.y < SCREEN_HEIGHT:
                    self.interact_at(event.x + camera_x, SCREEN_HEIGHT - event.y + camera_y,
                                     level, player)
            self.left_down = True

    def interact_at(self, x, y, level, player):
        pool = self.target_at(x, y, level, player)
        if pool is None:
            if (player.x - x) ** 2 + (player.y - y) ** 2 <= self.INTERACTION_RADIUS ** 2:
                candidates = list(getattr(level, 'color_sources', [])) + level.water + list(getattr(level, 'devices', []))
                hit = next((w for w in candidates if w.left <= x < w.right and w.bottom <= y <= w.top
                            and (not hasattr(w, 'contains_point') or w.contains_point(x, y))), None)
                if hit is not None:
                    if getattr(hit, 'unlock_stage', 0) > getattr(level, 'progress', 99):
                        self.notice = '앞 구간을 먼저 통과하세요.'
                    elif self.stored_color(hit) is not None and player.color is not None:
                        self.notice = '보유한 색을 먼저 부여하세요.'
                    else:
                        self.notice = {'blue': '파랑', 'green': '초록', 'yellow': '노랑'}[
                            getattr(hit, 'required_color', 'blue')] + '이 필요한 장치예요.'
            return False
        extracting = self.stored_color(pool) is not None
        color = self.stored_color(pool) if extracting else player.color
        if hasattr(pool, 'active'):
            pool.active = not extracting
        else:
            pool.has_blue = not extracting
        player.color = color if extracting else None
        pool.animation_time = 0.0
        is_source = any(pool is source for source in getattr(level, 'color_sources', []))
        if pool in getattr(level, 'droplets', []) and pool.solid:
            for part in level.droplets:
                if part.color_owner is pool.color_owner:
                    player.resolve_solid_water(part)
        elif not is_source and pool in level.water and pool.solid:
            for part in level.water:
                if part.color_owner is pool.color_owner:
                    player.resolve_solid_water(part)
        self.transfer_serial += 1
        action = ('extract' if extracting else 'deposit') if is_source else (
            'reclaim' if extracting else 'give')
        self.last_transfer = (color, action)
        self.notice = ''
        return True
