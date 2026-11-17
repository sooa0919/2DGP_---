import pico2d

from .settings import GROUND_HEIGHT, IMAGE_ROOT, SCREEN_HEIGHT, WORLD_WIDTH


class Player:
    SIZE = 64
    DRAW_SIZE = 72
    SPEED = 240.0
    GRAVITY = 1500.0
    JUMP_SPEED = 560.0
    FAST_FALL_GRAVITY = 3000.0
    ANIMATION_FPS = {"idle": 8.0, "run": 10.0}
    MOVEMENT_KEYS = (pico2d.SDLK_SPACE, pico2d.SDLK_a, pico2d.SDLK_s, pico2d.SDLK_d)

    def __init__(self, level=None):
        self.level = level
        self.images = {
            state: pico2d.load_image(
                str(IMAGE_ROOT / "character" / state / f"{state}_blue.png")
            )
            for state in ("idle", "run")
        }
        self.gray_images = {
            "idle": pico2d.load_image(str(IMAGE_ROOT / "character" / "idle" / "idle_gray.png")),
            "run": pico2d.load_image(str(IMAGE_ROOT / "background" / "grayscale" / "character" / "run.png")),
        }
        self.has_blue = True
        self.x = 200.0
        self.y = GROUND_HEIGHT + self.DRAW_SIZE / 2
        self.keys = set()
        self.state = "idle"
        self.frame = 0.0
        self.facing = 1
        self.velocity_y = 0.0
        self.grounded = True

    def handle_event(self, event):
        if event.type == pico2d.SDL_WINDOWEVENT:
            if event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
                self.keys.clear()
        elif event.type == pico2d.SDL_KEYDOWN and event.key in self.MOVEMENT_KEYS:
            if event.key == pico2d.SDLK_SPACE and event.key not in self.keys and self.grounded:
                self.velocity_y = self.JUMP_SPEED
                self.grounded = False
            self.keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self.keys.discard(event.key)

    def update(self, dt):
        dx = int(pico2d.SDLK_d in self.keys) - int(pico2d.SDLK_a in self.keys)
        old_x = self.x
        if self.level is not None:
            remaining = dt
            while remaining > 1e-9:
                step = min(remaining, 1 / 120)
                self._move_on_platforms(step, dx)
                remaining -= step
            self._animate(dt, dx, old_x)
            return
        self.x += dx * self.SPEED * dt
        if not self.grounded:
            gravity = (self.FAST_FALL_GRAVITY if pico2d.SDLK_s in self.keys
                       else self.GRAVITY)
            self.y += self.velocity_y * dt - 0.5 * gravity * dt * dt
            self.velocity_y -= gravity * dt
        half = self.DRAW_SIZE / 2
        self.x = max(half, min(self.x, WORLD_WIDTH - half))
        if self.y <= GROUND_HEIGHT + half:
            self.y = GROUND_HEIGHT + half
            self.velocity_y = 0.0
            self.grounded = True
        elif self.y > SCREEN_HEIGHT - half:
            self.y = SCREEN_HEIGHT - half
            self.velocity_y = min(0.0, self.velocity_y)
        self._animate(dt, dx, old_x)

    def enter_level(self, level):
        self.level = level
        level.reset_water()
        self.has_blue = True
        self.x, floor = level.spawn
        self.y = floor + self.DRAW_SIZE / 2
        self.velocity_y = 0.0
        self.grounded = True
        self.state, self.frame = "idle", 0.0
        self.keys.clear()

    @property
    def in_water(self):
        return self.level is not None and any(
            pool.has_blue and pool.left < self.x < pool.right
            and self.y - self.DRAW_SIZE / 2 < pool.top
            and self.y + self.DRAW_SIZE / 2 > pool.bottom
            for pool in self.level.water)

    def _move_on_platforms(self, dt, dx):
        half = self.DRAW_SIZE / 2
        solids = self.level.collision_platforms()
        old_x = self.x
        speed = self.SPEED * (0.7 if self.in_water else 1.0)
        self.x = max(half, min(self.x + dx * speed * dt, self.level.width - half))
        for p in solids:
            if self.y + half <= p.bottom + 0.01 or self.y - half >= p.top - 0.01:
                continue
            if self.x + half > p.left and self.x - half < p.right:
                if dx > 0 and old_x + half <= p.left + 0.01:
                    self.x = min(self.x, p.left - half)
                elif dx < 0 and old_x - half >= p.right - 0.01:
                    self.x = max(self.x, p.right + half)
        old_bottom, old_top = self.y - half, self.y + half
        gravity = self.FAST_FALL_GRAVITY if pico2d.SDLK_s in self.keys else self.GRAVITY
        self.y += self.velocity_y * dt - gravity * dt * dt / 2
        self.velocity_y -= gravity * dt
        self.grounded = False
        for p in solids:
            if self.x + half <= p.left or self.x - half >= p.right:
                continue
            if self.velocity_y <= 0 and old_bottom >= p.top - 0.01 and self.y - half <= p.top:
                self.y = p.top + half
                self.velocity_y = 0.0
                self.grounded = True
            elif self.velocity_y > 0 and old_top <= p.bottom + 0.01 and self.y + half >= p.bottom:
                self.y = p.bottom - half
                self.velocity_y = 0.0
        if self.y > SCREEN_HEIGHT - half:
            self.y = SCREEN_HEIGHT - half
            self.velocity_y = min(0.0, self.velocity_y)
        if self.y + half < -96:
            held_keys = self.keys.copy()
            self.enter_level(self.level)
            self.keys = held_keys

    def _animate(self, dt, dx, old_x):
        if dx:
            self.facing = 1 if dx > 0 else -1
        state = "run" if self.x != old_x or not self.grounded else "idle"
        if state != self.state:
            self.state, self.frame = state, 0.0
        image = self.current_images[self.state]
        count = (image.w // self.SIZE) * (image.h // self.SIZE)
        self.frame = (self.frame + self.ANIMATION_FPS[self.state] * dt) % count

    def draw(self, camera_x):
        image = self.current_images[self.state]
        columns = image.w // self.SIZE
        row, column = divmod(int(self.frame), columns)
        # Updated run sprites face right; idle sprites face left.
        flip = (self.facing < 0) if self.state == "run" else (self.facing > 0)
        image.clip_composite_draw(
            column * self.SIZE, image.h - (row + 1) * self.SIZE,
            self.SIZE, self.SIZE, 0, "h" if flip else "",
            round(self.x - camera_x), round(self.y), self.DRAW_SIZE, self.DRAW_SIZE,
        )

    @property
    def current_images(self):
        return self.images if self.has_blue else self.gray_images

    def resolve_solid_water(self, pool):
        half = self.DRAW_SIZE / 2
        if (self.x + half > pool.left and self.x - half < pool.right
                and self.y - half < pool.top and self.y + half > pool.bottom):
            self.y = pool.top + half
            self.velocity_y = 0.0
            self.grounded = True
