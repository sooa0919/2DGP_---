"""Compact controls, color selection and guidance for the new puzzle route."""
import pico2d

from .settings import FONT_PATH, SCREEN_WIDTH, SCREEN_HEIGHT


HINTS = (
    '앞의 파랑 보석을 좌클릭하고, 물에 부여해 길을 통과하세요.',
    '물에서 색을 회수한 뒤 2번으로 초록 전환 · 첫 덩굴을 켜고 위로 올라가세요.',
    '첫 발판에서 색을 회수하고 점프로 길을 건넌 뒤, 얇은 발판에서 S로 내려가세요.',
    '초록을 앞의 덩굴 1에 부여하고 첫 번째 쉼터로 올라가세요.',
    '색을 회수해 덩굴 2를 켠 뒤 다음 쉼터로 건너가세요.',
    '색을 회수해 덩굴 3을 켜고 높은 쉼터까지 올라가세요.',
    '빈손으로 낙수의 파랑을 빼면 멈춥니다. 타이밍을 맞춰 고체 발판을 밟으세요.',
    '낙수에서 얻은 색을 3번으로 노랑 전환 · 등불을 켜고 아래 문으로 나가세요.',
)


class Tutorial:
    def __init__(self):
        self.font = pico2d.load_font(str(FONT_PATH), 18)
        self.small = pico2d.load_font(str(FONT_PATH), 15)
        self.reset()

    def reset(self):
        self.pressed = set()
        self.mouse_pos = None
        self.paused = False
        self.complete = False
        self.message = None

    def handle_event(self, event, player):
        if event.type in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN, pico2d.SDL_MOUSEBUTTONUP):
            self.mouse_pos = (event.x, SCREEN_HEIGHT - event.y)
        elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_r:
            self.reset()

    def update(self, dt, level, player, colors):
        self.complete = level.complete

    def draw(self, level, player, colors, camera_x, camera_y=0):
        pico2d.draw_rectangle(14, 14, SCREEN_WIDTH - 14, 85, 14, 18, 22, 225, filled=True)
        hint = '튜토리얼 완료!  R: 다시 시작  /  ESC: 메뉴' if self.complete else HINTS[level.progress]
        self.font.draw(28, 66, hint, (239, 241, 239))
        self.small.draw(28, 35, 'A/D 이동   SPACE 점프   S 얇은 발판 내려가기   좌클릭 부여/회수   R 초기화',
                        (202, 210, 216))
        for index, (color, label, rgb) in enumerate((('blue', '1 파랑', (68, 170, 235)),
                                                     ('green', '2 초록', (75, 195, 110)),
                                                     ('yellow', '3 노랑', (245, 212, 90)))):
            x = SCREEN_WIDTH - 312 + index * 96
            selected = player.color == color
            pico2d.draw_rectangle(x, SCREEN_HEIGHT - 48, x + 88, SCREEN_HEIGHT - 15,
                                  *(rgb if selected else (61, 66, 70)), filled=True)
            self.small.draw(x + 10, SCREEN_HEIGHT - 31, label, (245, 245, 240))
        self.small.draw(28, SCREEN_HEIGHT - 30,
                        colors.notice or ('보유 색 없음' if player.color is None else '보유 색: ' +
                        {'blue': '파랑', 'green': '초록', 'yellow': '노랑'}[player.color]), (245, 245, 240))
        if self.mouse_pos:
            x, y = self.mouse_pos
            target = colors.target_at(x + camera_x, y + camera_y, level, player)
            if target:
                self.small.draw(min(x + 18, SCREEN_WIDTH - 130), min(y + 22, SCREEN_HEIGHT - 65),
                                '좌클릭 부여/회수', (255, 245, 195))
