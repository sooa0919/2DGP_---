"""Settings modal using the supplied hand-drawn UI sheet."""
import pico2d

from .settings import FONT_PATH, FONT_BOLD_PATH, IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH


class SettingsMenu:
    TABS = ('게임 설정', '화면 설정', '음향 설정', '조작 설정')
    TAB_Y = (410, 330, 250, 170)
    CLOSE_BOUNDS = (988, 72, 1032, 120)
    RESET_BOUNDS = (928, 72, 972, 120)
    ACTION_BOUNDS = {'save': (686, 142, 782, 184),
                     'title': (790, 142, 886, 184),
                     'quit': (894, 142, 990, 184)}
    SLIDER_LEFT, SLIDER_RIGHT = 714, 1018
    SLIDER_Y = {'bgm': 370, 'sfx': 270}
    INK = (48, 65, 51)

    def __init__(self):
        folder = IMAGE_ROOT / 'ui/current'
        self.images = {name: pico2d.load_image(str(folder / f'{name}.png'))
                       for name in ('menu', 'frame', 'button', 'back', 'reset',
                                    'track', 'fill', 'knob')}
        self.shade = pico2d.load_image(str(IMAGE_ROOT / 'ui/fade_black.png'))
        self.font = pico2d.load_font(str(FONT_PATH), 22)
        self.small = pico2d.load_font(str(FONT_PATH), 16)
        self.heading = pico2d.load_font(str(FONT_BOLD_PATH), 26)
        self.tab = 0
        self.mouse = None
        self.in_game = False
        self.volumes = {'bgm': 80, 'sfx': 80}
        self.dragging = None

    def open(self, in_game=False):
        self.in_game = in_game
        self.mouse = None
        self.dragging = None

    @property
    def action_bounds(self):
        return self.ACTION_BOUNDS if self.in_game else {'quit': self.ACTION_BOUNDS['quit']}

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
            return 'close'
        if event.type not in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN,
                              pico2d.SDL_MOUSEBUTTONUP):
            return None
        self.mouse = event.x, SCREEN_HEIGHT - event.y
        if event.type == pico2d.SDL_MOUSEMOTION and self.dragging:
            self.set_volume(self.dragging, self.mouse[0])
        if event.type == pico2d.SDL_MOUSEBUTTONUP and event.button == pico2d.SDL_BUTTON_LEFT:
            if self.dragging:
                self.set_volume(self.dragging, self.mouse[0])
            self.dragging = None
        if event.type != pico2d.SDL_MOUSEBUTTONDOWN or event.button != pico2d.SDL_BUTTON_LEFT:
            return None
        if self.contains(self.CLOSE_BOUNDS):
            self.dragging = None
            return 'close'
        if self.contains(self.RESET_BOUNDS):
            self.volumes.update(bgm=80, sfx=80)
        for action, bounds in self.action_bounds.items():
            if action != 'save' and self.contains(bounds):
                self.dragging = None
                return action
        for index, y in enumerate(self.TAB_Y):
            if self.contains((100, y - 31, 302, y + 31)):
                self.tab = index
                self.dragging = None
                break
        if self.tab == 2:
            for channel, y in self.SLIDER_Y.items():
                if self.contains((self.SLIDER_LEFT - 15, y - 22, self.SLIDER_RIGHT + 15, y + 22)):
                    self.dragging = channel
                    self.set_volume(channel, self.mouse[0])
                    break
        return None

    def image(self, name, x, y, width, height):
        self.images[name].draw(x, y, width, height)

    def centered(self, font, x, y, text, size, color=None):
        width = sum(size * (.5 if ord(c) < 128 else 1) for c in text)
        font.draw(x - width / 2, y, text, color or self.INK)

    def button(self, bounds, text, disabled=False, selected=False):
        left, bottom, right, top = bounds
        image = self.images['button']
        image.opacify(.38 if disabled else (1 if self.contains(bounds) or selected else .76))
        image.draw((left + right) / 2, (bottom + top) / 2, right - left, top - bottom)
        self.centered(self.small, (left + right) / 2, (bottom + top) / 2, text, 16,
                      (122, 130, 125) if disabled else self.INK)

    def value(self, y, label, value):
        self.font.draw(510, y, label, self.INK)
        self.font.draw(714, y, value, self.INK)

    def slider(self, channel):
        y = self.SLIDER_Y[channel]
        left, right = self.SLIDER_LEFT, self.SLIDER_RIGHT
        fraction = self.volumes[channel] / 100
        self.image('track', (left + right) / 2, y, right - left + 12, 23)
        if fraction > 0:
            fill = self.images['fill']
            width = max(1, round(fill.w * fraction))
            fill.clip_draw(0, 0, width, fill.h, left + (right - left) * fraction / 2,
                           y, (right - left) * fraction, 12)
        self.image('knob', left + (right - left) * fraction, y, 27, 30)
        self.centered(self.small, (left + right) / 2, y - 31,
                      f'{self.volumes[channel]}%', 16)

    def draw(self):
        self.shade.opacify(.65)
        self.shade.draw(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.image('menu', 201, 324, 310, 460)
        self.image('frame', 742, 324, 724, 539)
        for index, y in enumerate(self.TAB_Y):
            self.button((100, y - 31, 302, y + 31), self.TABS[index], selected=index == self.tab)
            if index == self.tab:
                self.small.draw(79, y, '◆', (97, 167, 191))
        self.centered(self.heading, 850, 470, self.TABS[self.tab], 26)
        if self.tab == 0:
            self.value(382, '언어', '한국어')
            self.value(302, '화면 흔들림', '켜짐')
            self.value(222, '피격 연출', '켜짐')
        elif self.tab == 1:
            self.value(382, '화면 모드', '전체 화면')
            self.value(302, '해상도', f'{SCREEN_WIDTH} × {SCREEN_HEIGHT}')
            self.value(222, '픽셀 화면', '유지')
        elif self.tab == 2:
            self.font.draw(510, 370, '배경음악', self.INK)
            self.font.draw(510, 270, '효과음', self.INK)
            for channel in self.SLIDER_Y:
                self.slider(channel)
            self.centered(self.small, 850, 204, '드래그하여 음량 조절', 16)
        else:
            for y, label, value in ((395, '이동', 'A / D'), (352, '점프', 'SPACE'),
                                    (309, '내려가기', 'S'), (266, '색 상호작용', '마우스 왼쪽'),
                                    (223, '설정 / 계속', 'ESC')):
                self.value(y, label, value)
        for action, text in (('save', '저장'), ('title', '타이틀로'), ('quit', '게임 종료')):
            if action in self.action_bounds:
                self.button(self.action_bounds[action], text, disabled=action == 'save')
        for name, bounds in (('back', self.CLOSE_BOUNDS), ('reset', self.RESET_BOUNDS)):
            left, bottom, right, top = bounds
            self.images[name].opacify(1 if self.contains(bounds) else .8)
            self.image(name, (left + right) / 2, (bottom + top) / 2, right - left, top - bottom)
        self.small.draw(704, 100, 'ESC  계속하기', self.INK)
