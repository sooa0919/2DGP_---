"""Settings modal using the supplied hand-drawn UI sheet."""
import pico2d

from .settings import FONT_PATH, IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH


class SettingsMenu:
    TABS = ('사운드', '조작')
    TAB_Y = (370, 270)
    TAB_BOUNDS = ((504, 341, 634, 399), (504, 241, 634, 299))
    CLOSE_BOUNDS = (988, 72, 1032, 120)
    RESET_BOUNDS = (928, 72, 972, 120)
    ACTION_BOUNDS = {'settings': (100, 379, 302, 441),
                     'save': (100, 299, 302, 361),
                     'title': (100, 219, 302, 281),
                     'quit': (100, 139, 302, 201)}
    SLIDER_LEFT, SLIDER_RIGHT = 714, 1018
    SLIDER_Y = {'bgm': 370, 'sfx': 270}
    INK = (48, 65, 51)

    def __init__(self):
        folder = IMAGE_ROOT / 'ui/current'
        self.images = {name: pico2d.load_image(str(folder / f'{name}.png'))
                       for name in ('menu', 'frame', 'button', 'back', 'reset',
                                    'track', 'fill', 'knob')}
        self.shade = pico2d.load_image(str(IMAGE_ROOT / 'ui/fade_black.png'))
        self.small = pico2d.load_font(str(FONT_PATH), 16)
        self.tab = 0
        self.panel_open = False
        self.mouse = None
        self.in_game = False
        self.volumes = {'bgm': 80, 'sfx': 80}
        self.dragging = None

    def open(self, in_game=False):
        self.in_game = in_game
        self.mouse = None
        self.dragging = None
        self.panel_open = not in_game

    @property
    def panel_offset(self):
        return 0 if self.in_game else -166

    @property
    def action_bounds(self):
        return self.ACTION_BOUNDS if self.in_game else {}

    def contains(self, bounds):
        if self.mouse is None:
            return False
        x, y = self.mouse
        left, bottom, right, top = bounds
        return left <= x < right and bottom <= y < top

    def set_volume(self, channel, x):
        value = (x - self.SLIDER_LEFT) / (self.SLIDER_RIGHT - self.SLIDER_LEFT)
        self.volumes[channel] = round(100 * max(0, min(1, value)))

    def handle_event(self, event):
        if event.type == pico2d.SDL_WINDOWEVENT and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
            self.dragging = None
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            self.dragging = None
            if self.panel_open and self.in_game:
                self.panel_open = False
                return None
            return 'close'
        if event.type not in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN,
                              pico2d.SDL_MOUSEBUTTONUP):
            return None
        self.mouse = event.x - self.panel_offset, SCREEN_HEIGHT - event.y
        if event.type == pico2d.SDL_MOUSEMOTION and self.dragging:
            self.set_volume(self.dragging, self.mouse[0])
        if event.type == pico2d.SDL_MOUSEBUTTONUP and event.button == pico2d.SDL_BUTTON_LEFT:
            if self.dragging:
                self.set_volume(self.dragging, self.mouse[0])
            self.dragging = None
        if event.type != pico2d.SDL_MOUSEBUTTONDOWN or event.button != pico2d.SDL_BUTTON_LEFT:
            return None
        if self.panel_open and self.contains(self.CLOSE_BOUNDS):
            self.dragging = None
            self.panel_open = False
            return None if self.in_game else 'close'
        if self.panel_open and self.contains(self.RESET_BOUNDS):
            self.volumes.update(bgm=80, sfx=80)
        for action, bounds in self.action_bounds.items():
            if self.contains(bounds):
                self.dragging = None
                if action == 'settings':
                    self.panel_open = True
                elif action != 'save':
                    return action
                return None
        if not self.panel_open:
            return None
        for index, bounds in enumerate(self.TAB_BOUNDS):
            if self.contains(bounds):
                self.tab = index
                self.dragging = None
                break
        if self.tab == 0:
            for channel, y in self.SLIDER_Y.items():
                if self.contains((self.SLIDER_LEFT - 15, y - 22, self.SLIDER_RIGHT + 15, y + 22)):
                    self.dragging = channel
                    self.set_volume(channel, self.mouse[0])
                    break
        return None

    def image(self, name, x, y, width, height):
        self.images[name].draw(x + self.panel_offset, y, width, height)

    def centered(self, font, x, y, text, size, color=None):
        width = sum(size * (.5 if ord(c) < 128 else 1) for c in text)
        font.draw(x + self.panel_offset - width / 2, y, text, color or self.INK)

    def button(self, bounds, text, disabled=False, selected=False):
        left, bottom, right, top = bounds
        image = self.images['button']
        image.opacify(.38 if disabled else (1 if self.contains(bounds) or selected else .76))
        image.draw((left + right) / 2 + self.panel_offset, (bottom + top) / 2,
                   right - left, top - bottom)
        self.centered(self.small, (left + right) / 2, (bottom + top) / 2, text, 16,
                      (122, 130, 125) if disabled else self.INK)

    def value(self, y, label, value):
        self.small.draw(714 + self.panel_offset, y, label, self.INK)
        self.small.draw(880 + self.panel_offset, y, value, self.INK)

    def slider(self, channel):
        y = self.SLIDER_Y[channel]
        left, right = self.SLIDER_LEFT, self.SLIDER_RIGHT
        fraction = self.volumes[channel] / 100
        self.image('track', (left + right) / 2, y, right - left + 12, 23)
        if fraction > 0:
            fill = self.images['fill']
            width = max(1, round(fill.w * fraction))
            fill.clip_draw(0, 0, width, fill.h, left + self.panel_offset + (right - left) * fraction / 2,
                           y, (right - left) * fraction, 12)
        self.image('knob', left + (right - left) * fraction, y, 27, 30)
        self.centered(self.small, (left + right) / 2, y - 31,
                      f'{self.volumes[channel]}%', 16)

    def draw(self):
        self.shade.opacify(.65)
        self.shade.draw(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.in_game:
            self.image('menu', 201, 324, 310, 460)
            labels = {'settings': '설정', 'save': '저장', 'title': '타이틀로', 'quit': '종료'}
            for action, bounds in self.ACTION_BOUNDS.items():
                self.button(bounds, labels[action], disabled=action == 'save',
                            selected=action == 'settings' and self.panel_open)
        if not self.panel_open:
            return
        self.image('frame', 742, 324, 724, 539)
        for index, bounds in enumerate(self.TAB_BOUNDS):
            self.button(bounds, self.TABS[index], selected=index == self.tab)
        if self.tab == 0:
            self.small.draw(714 + self.panel_offset, 408, 'BGM', self.INK)
            self.small.draw(714 + self.panel_offset, 308, '효과음', self.INK)
            for channel in self.SLIDER_Y:
                self.slider(channel)
        else:
            for y, label, value in ((395, '이동', 'A / D'), (352, '점프', 'SPACE'),
                                    (309, '내려가기', 'S'), (266, '색 상호작용', '마우스 왼쪽'),
                                    (223, '설정 / 계속', 'ESC')):
                self.value(y, label, value)
        for name, bounds in (('back', self.CLOSE_BOUNDS), ('reset', self.RESET_BOUNDS)):
            left, bottom, right, top = bounds
            self.images[name].opacify(1 if self.contains(bounds) else .8)
            self.image(name, (left + right) / 2, (bottom + top) / 2, right - left, top - bottom)
