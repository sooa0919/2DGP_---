"""Modal settings preview assembled from the supplied CHROMA UI kit."""
import pico2d

from .settings import FONT_PATH, FONT_BOLD_PATH, IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH


class SettingsMenu:
    TABS = ('게임 설정', '화면 설정', '음향 설정', '조작 설정')
    TAB_Y = (456, 378, 300, 222)
    CLOSE_BOUNDS = (775, 58, 940, 112)
    ACTION_BOUNDS = {
        'save': (205, 58, 370, 112),
        'title': (395, 58, 560, 112),
        'quit': (585, 58, 750, 112),
    }

    def __init__(self):
        folder = IMAGE_ROOT / 'ui/CHROMA_UI'
        names = ('01_숲유적_배경', '02_설정창_프레임', '03_제목_장식',
                 'slider_기본', 'checkbox_체크', 'toggle_켜짐',
                 'icon_소리', 'icon_모니터', 'icon_게임패드', 'icon_설정',
                 'button_돌아가기_기본', 'button_돌아가기_호버')
        self.images = {name: pico2d.load_image(str(folder / f'{name}.png')) for name in names}
        self.tabs = [pico2d.load_image(str(folder / f'tab_{name.replace(" ", "")}.png'))
                     for name in self.TABS]
        self.shade = pico2d.load_image(str(IMAGE_ROOT / 'ui/fade_black.png'))
        self.actions = pico2d.load_image(str(folder / '저장_게임종료_타이틀로_.webp'))
        font = str(FONT_PATH)
        self.font = pico2d.load_font(font, 22)
        self.small = pico2d.load_font(font, 16)
        self.heading = pico2d.load_font(str(FONT_BOLD_PATH), 28)
        self.tab = 0
        self.mouse = None
        self.in_game = False

    def open(self, in_game=False):
        self.in_game = in_game
        self.mouse = None

    @property
    def action_bounds(self):
        return self.ACTION_BOUNDS if self.in_game else {'quit': self.ACTION_BOUNDS['quit']}

    def contains(self, bounds):
        if self.mouse is None:
            return False
        x, y = self.mouse
        left, bottom, right, top = bounds
        return left <= x < right and bottom <= y < top

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            return 'close'
        if event.type in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN,
                          pico2d.SDL_MOUSEBUTTONUP):
            self.mouse = event.x, SCREEN_HEIGHT - event.y
            if event.type == pico2d.SDL_MOUSEBUTTONDOWN and event.button == pico2d.SDL_BUTTON_LEFT:
                if self.contains(self.CLOSE_BOUNDS):
                    return 'close'
                for action, bounds in self.action_bounds.items():
                    if action != 'save' and self.contains(bounds):
                        return action
                for index, y in enumerate(self.TAB_Y):
                    if self.contains((190, y - 31, 407, y + 31)):
                        self.tab = index
                        break
        return None

    def image(self, name, x, y, width, height):
        self.images[name].draw(x, y, width, height)

    def line(self, y):
        pico2d.draw_rectangle(438, y, 924, y + 1, 101, 117, 150, filled=True)

    def label(self, x, y, text):
        self.font.draw(x, y, text, (235, 238, 248))

    def value(self, y, label, value):
        self.label(448, y, label)
        self.small.draw(737, y, value, (180, 204, 235))

    def check(self, y, label):
        self.label(448, y, label)
        self.image('checkbox_체크', 867, y, 34, 31)

    def draw(self):
        self.shade.opacify(.68)
        self.shade.draw(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.image('01_숲유적_배경', 576, 324, 815, 536)
        self.shade.opacify(.34)
        self.shade.draw(576, 324, 812, 530)
        self.image('02_설정창_프레임', 576, 324, 860, 584)
        self.image('03_제목_장식', 576, 582, 330, 61)
        self.heading.draw(547, 554, '설정', (246, 240, 224))
        # A quiet content surface keeps the kit's forest artwork visible around it.
        self.shade.opacify(.30)
        self.shade.draw(682, 320, 508, 354)
        for index, (tab, y) in enumerate(zip(self.tabs, self.TAB_Y)):
            selected = index == self.tab
            hovered = self.contains((190, y - 31, 407, y + 31))
            tab.opacify(1.0 if selected or hovered else .58)
            tab.draw(298, y, 217, 62)
            if selected:
                pico2d.draw_rectangle(192, y - 29, 404, y + 29, 138, 211, 255)
        icons = ('icon_설정', 'icon_모니터', 'icon_소리', 'icon_게임패드')
        self.image(icons[self.tab], 465, 466, 36, 36)
        self.label(498, 466, self.TABS[self.tab])
        self.line(438)
        if self.tab == 0:
            self.value(399, '언어', '한국어')
            self.line(371)
            self.check(333, '화면 흔들림')
            self.check(276, '피격 연출')
        elif self.tab == 1:
            self.value(399, '화면 모드', '전체 화면')
            self.value(345, '게임 해상도', f'{SCREEN_WIDTH} × {SCREEN_HEIGHT}')
            self.line(316)
            self.label(448, 273, '픽셀 화면 유지')
            self.image('toggle_켜짐', 864, 273, 58, 44)
        elif self.tab == 2:
            self.label(448, 396, '배경음악 (BGM)')
            self.image('slider_기본', 673, 352, 309, 56)
            self.small.draw(858, 352, '80%', (210, 228, 247))
            self.label(448, 282, '효과음 (SFX)')
            self.image('slider_기본', 673, 238, 309, 56)
            self.small.draw(858, 238, '80%', (210, 228, 247))
        else:
            for y, label, value in ((400, '이동', 'A / D'), (352, '점프', 'SPACE'),
                                    (304, '발판 내려가기', 'S'), (256, '색 상호작용', '마우스 왼쪽'),
                                    (208, '설정 / 계속하기', 'ESC')):
                self.value(y, label, value)
        self.small.draw(444, 159, '설정 변경 기능은 준비 중입니다.', (159, 179, 208))
        self.small.draw(266, 124, 'ESC  ·  닫기 / 계속하기', (190, 208, 229))
        for action, row in (('save', 2), ('title', 1), ('quit', 0)):
            if action not in self.action_bounds:
                continue
            bounds = self.action_bounds[action]
            # Sheet columns: normal, hover, selected, disabled.
            column = 3 if action == 'save' else int(self.contains(bounds))
            source_x = (24, 374, 729, 1079)[column]
            source_top = 285 + row * 210
            left, bottom, right, top = bounds
            self.actions.clip_draw(source_x, self.actions.h - source_top - 150,
                                   350, 150, (left + right) / 2, (bottom + top) / 2,
                                   right - left, top - bottom)
        state = '호버' if self.contains(self.CLOSE_BOUNDS) else '기본'
        self.image(f'button_돌아가기_{state}', 857, 85, 165, 54)
