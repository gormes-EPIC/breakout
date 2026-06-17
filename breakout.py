import pygame
import sys
import math
import random

pygame.init()
pygame.joystick.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FPS = 60

BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GRAY       = (120, 120, 130)
DARK_GRAY  = (20, 20, 30)
CYAN       = (0, 220, 255)
YELLOW     = (255, 230, 0)

PADDLE_COLOR    = (0, 200, 255)
PADDLE_SHINE    = (160, 245, 255)
BALL_COLOR      = (255, 255, 255)
BALL_SHINE      = (200, 200, 255)

BRICK_ROWS = 7
BRICK_COLS = 14
BRICK_W    = 65
BRICK_H    = 22
BRICK_PAD  = 4
BRICK_TOP  = 60
BRICK_LEFT = (SCREEN_WIDTH - (BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD)) // 2

BRICK_SPEC = [
    ((200,  50, 220), 70),   # purple
    ((220,  50,  50), 60),   # red
    ((230, 130,  30), 50),   # orange
    ((230, 190,  30), 40),   # amber
    ((200, 220,  30), 30),   # yellow-green
    (( 50, 200,  80), 20),   # green
    (( 50, 100, 230), 10),   # blue
]

PADDLE_W = 120
PADDLE_H = 12
PADDLE_SPEED = 9
BALL_RADIUS = 8
BALL_BASE_SPEED = 5.5


class Paddle:
    def __init__(self):
        self.w = PADDLE_W
        self.h = PADDLE_H
        self.x = float((SCREEN_WIDTH - self.w) // 2)
        self.y = SCREEN_HEIGHT - 48
        self.rect = pygame.Rect(int(self.x), self.y, self.w, self.h)

    def move(self, direction: float):
        self.x += direction * PADDLE_SPEED
        self.x = max(0.0, min(float(SCREEN_WIDTH - self.w), self.x))
        self.rect.x = int(self.x)

    def draw(self, surface):
        pygame.draw.rect(surface, PADDLE_COLOR, self.rect, border_radius=6)
        shine = pygame.Rect(self.rect.x + 5, self.rect.y + 2, self.rect.w - 10, 4)
        pygame.draw.rect(surface, PADDLE_SHINE, shine, border_radius=2)


class Ball:
    def __init__(self, paddle: Paddle):
        self.r = BALL_RADIUS
        self.reset(paddle)

    def reset(self, paddle: Paddle):
        self.x = float(paddle.rect.centerx)
        self.y = float(paddle.y - self.r - 1)
        self.dx = 0.0
        self.dy = 0.0
        self.attached = True

    def launch(self, level: int):
        if not self.attached:
            return
        speed = BALL_BASE_SPEED + (level - 1) * 0.4
        angle = math.radians(random.uniform(-40, 40))
        self.dx = speed * math.sin(angle)
        self.dy = -speed * math.cos(angle)
        self.attached = False

    def update(self, paddle: Paddle) -> bool:
        if self.attached:
            self.x = float(paddle.rect.centerx)
            self.y = float(paddle.y - self.r - 1)
            return True

        self.x += self.dx
        self.y += self.dy

        if self.x - self.r <= 0:
            self.x = float(self.r)
            self.dx = abs(self.dx)
        elif self.x + self.r >= SCREEN_WIDTH:
            self.x = float(SCREEN_WIDTH - self.r)
            self.dx = -abs(self.dx)

        if self.y - self.r <= 0:
            self.y = float(self.r)
            self.dy = abs(self.dy)

        return self.y < SCREEN_HEIGHT + 40

    def rect(self):
        return pygame.Rect(int(self.x) - self.r, int(self.y) - self.r, self.r * 2, self.r * 2)

    def speed(self) -> float:
        return math.hypot(self.dx, self.dy)

    def draw(self, surface):
        pygame.draw.circle(surface, BALL_COLOR, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surface, BALL_SHINE,
                           (int(self.x) - 2, int(self.y) - 2), max(1, self.r // 3))


class Brick:
    def __init__(self, x, y, color, points, hits=1):
        self.rect   = pygame.Rect(x, y, BRICK_W, BRICK_H)
        self.color  = color
        self.points = points
        self.hits   = hits
        self.max_hits = hits
        self.active = True

    def hit(self) -> bool:
        self.hits -= 1
        if self.hits <= 0:
            self.active = False
            return True
        return False

    def draw(self, surface):
        if not self.active:
            return
        frac = self.hits / self.max_hits
        c = tuple(max(40, int(ch * frac)) for ch in self.color)
        pygame.draw.rect(surface, c, self.rect, border_radius=4)
        edge = tuple(min(255, ch + 60) for ch in c)
        pygame.draw.rect(surface, edge, self.rect, 1, border_radius=4)
        shine_r = pygame.Rect(self.rect.x + 4, self.rect.y + 2, self.rect.w - 8, 4)
        shine_c = tuple(min(255, ch + 90) for ch in c)
        pygame.draw.rect(surface, shine_c, shine_r, border_radius=2)


class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.color = color
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5.5)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.life = random.randint(18, 36)
        self.max_life = self.life
        self.size = random.randint(2, 5)

    def update(self) -> bool:
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.12
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        frac = self.life / self.max_life
        size = max(1, int(self.size * frac))
        alpha = int(255 * frac)
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        r, g, b = self.color[:3]
        pygame.draw.circle(s, (r, g, b, alpha), (size, size), size)
        surface.blit(s, (int(self.x) - size, int(self.y) - size))


class Game:
    MAX_LEVEL = 3

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Breakout")
        self.clock = pygame.time.Clock()

        self.font_xl  = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_lg  = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_md  = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_sm  = pygame.font.SysFont("Arial", 18)

        self.joystick: pygame.joystick.JoystickType | None = None
        self._connect_joystick()

        self._new_game()

    # ------------------------------------------------------------------ setup

    def _connect_joystick(self):
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller: {self.joystick.get_name()}")
        else:
            self.joystick = None
            print("No controller found — using arrow keys + Space.")

    def _new_game(self):
        self.score     = 0
        self.lives     = 3
        self.level     = 1
        self.state     = "playing"   # playing | paused | dead | won | gameover
        self.particles: list[Particle] = []
        self._new_level()

    def _new_level(self):
        self.paddle = Paddle()
        self.ball   = Ball(self.paddle)
        self.bricks = self._make_bricks()

    def _make_bricks(self):
        bricks = []
        for row in range(BRICK_ROWS):
            color, pts = BRICK_SPEC[row % len(BRICK_SPEC)]
            # rows 0-1 get 2 hits on level 2+, all rows get 2 hits on level 3
            hits = 1
            if self.level == 2 and row < 2:
                hits = 2
            elif self.level >= 3:
                hits = 2
            for col in range(BRICK_COLS):
                x = BRICK_LEFT + col * (BRICK_W + BRICK_PAD)
                y = BRICK_TOP  + row * (BRICK_H  + BRICK_PAD)
                bricks.append(Brick(x, y, color, pts * self.level, hits))
        return bricks

    # ------------------------------------------------------------------ input

    def _input(self) -> tuple[float, bool, bool]:
        """Returns (direction -1..1, launch_pressed, pause_pressed)."""
        direction = 0.0
        launch    = False
        pause     = False

        if self.joystick:
            ax = self.joystick.get_axis(0)
            if abs(ax) > 0.08:
                direction = ax
            if self.joystick.get_numhats() > 0:
                hx, _ = self.joystick.get_hat(0)
                if hx:
                    direction = float(hx)
            # Cross=0, Circle=1, Square=2, Triangle=3  — any face button launches
            for btn in (0, 1, 2, 3):
                if self.joystick.get_button(btn):
                    launch = True

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: direction = -1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: direction =  1.0
        if keys[pygame.K_SPACE]: launch = True

        return direction, launch, pause

    # ---------------------------------------------------------------- physics

    def _collide_paddle(self):
        br = self.ball.rect()
        if self.ball.dy <= 0:
            return
        if not br.colliderect(self.paddle.rect):
            return
        # angle based on hit position across paddle
        rel = (self.ball.x - self.paddle.x) / self.paddle.w   # 0..1
        angle = math.radians((rel - 0.5) * 130)
        spd = self.ball.speed()
        self.ball.dx = spd * math.sin(angle)
        self.ball.dy = -abs(spd * math.cos(angle))
        # push ball out of paddle
        self.ball.y = float(self.paddle.y - self.ball.r - 1)

    def _collide_bricks(self):
        br = self.ball.rect()
        for brick in self.bricks:
            if not brick.active:
                continue
            if not br.colliderect(brick.rect):
                continue

            # resolve direction
            ol = br.right  - brick.rect.left
            or_ = brick.rect.right  - br.left
            ot = br.bottom - brick.rect.top
            ob = brick.rect.bottom - br.top
            mn = min(ol, or_, ot, ob)
            if mn in (ot, ob):
                self.ball.dy *= -1
            else:
                self.ball.dx *= -1

            destroyed = brick.hit()
            if destroyed:
                self.score += brick.points
                for _ in range(14):
                    self.particles.append(Particle(
                        brick.rect.centerx, brick.rect.centery, brick.color))
            break   # one brick per frame keeps physics clean

    # ----------------------------------------------------------------- update

    def _update(self):
        direction, launch, _ = self._input()
        self.paddle.move(direction)

        if launch:
            self.ball.launch(self.level)

        alive = self.ball.update(self.paddle)
        if not alive:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "gameover"
                return
            self.ball.reset(self.paddle)

        self._collide_paddle()
        self._collide_bricks()

        self.particles = [p for p in self.particles if p.update()]

        # Gentle top-speed cap so it never becomes unplayable
        max_spd = BALL_BASE_SPEED + (self.level - 1) * 0.4 + 1.5
        if not self.ball.attached and self.ball.speed() < max_spd:
            self.ball.dx *= 1.0003
            self.ball.dy *= 1.0003

        if all(not b.active for b in self.bricks):
            if self.level < self.MAX_LEVEL:
                self.level += 1
                self._new_level()
            else:
                self.state = "won"

    # ------------------------------------------------------------------ draw

    def _draw_bg(self):
        self.screen.fill(DARK_GRAY)
        for x in range(0, SCREEN_WIDTH, 48):
            pygame.draw.line(self.screen, (22, 22, 32), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 48):
            pygame.draw.line(self.screen, (22, 22, 32), (0, y), (SCREEN_WIDTH, y))

    def _draw_hud(self):
        pygame.draw.line(self.screen, (45, 45, 65), (0, 44), (SCREEN_WIDTH, 44), 2)

        score_s = self.font_md.render(f"SCORE  {self.score}", True, WHITE)
        self.screen.blit(score_s, (16, 12))

        # lives as small balls
        lives_s = self.font_md.render("LIVES", True, GRAY)
        self.screen.blit(lives_s, (SCREEN_WIDTH // 2 - 80, 12))
        for i in range(self.lives):
            pygame.draw.circle(self.screen, CYAN,
                               (SCREEN_WIDTH // 2 + 10 + i * 22, 22), 8)

        lvl_s = self.font_md.render(f"LEVEL {self.level}", True, YELLOW)
        self.screen.blit(lvl_s, (SCREEN_WIDTH - lvl_s.get_width() - 16, 12))

    def _draw_overlay(self, title, sub, hint):
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        self.screen.blit(veil, (0, 0))

        cy = SCREEN_HEIGHT // 2
        t = self.font_xl.render(title, True, CYAN)
        self.screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, cy - 80))

        if sub:
            s = self.font_lg.render(sub, True, WHITE)
            self.screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, cy - 10))

        h = self.font_sm.render(hint, True, GRAY)
        self.screen.blit(h, (SCREEN_WIDTH // 2 - h.get_width() // 2, cy + 50))

    def _draw_launch_hint(self):
        txt = self.font_sm.render("Press  X / Space  to launch", True, GRAY)
        self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                                self.paddle.y - 30))

    # ------------------------------------------------------------------- loop

    def run(self):
        while True:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_p and self.state == "playing":
                        self.state = "paused"
                    elif event.key == pygame.K_p and self.state == "paused":
                        self.state = "playing"
                    if event.key == pygame.K_r and self.state in ("gameover", "won"):
                        self._new_game()

                if event.type == pygame.JOYBUTTONDOWN:
                    # Options button (index 9 on DS4/DualSense) = pause toggle
                    if event.button == 9:
                        if self.state == "playing":   self.state = "paused"
                        elif self.state == "paused":  self.state = "playing"
                    # Any face button restarts from gameover/won
                    if event.button in (0, 1, 2, 3) and self.state in ("gameover", "won"):
                        self._new_game()

                if event.type == pygame.JOYDEVICEADDED:
                    self._connect_joystick()
                if event.type == pygame.JOYDEVICEREMOVED:
                    self.joystick = None
                    print("Controller disconnected.")

            if self.state == "playing":
                self._update()

            # -- render --
            self._draw_bg()
            for b in self.bricks:   b.draw(self.screen)
            for p in self.particles: p.draw(self.screen)
            self.paddle.draw(self.screen)
            self.ball.draw(self.screen)
            self._draw_hud()

            if self.ball.attached and self.state == "playing":
                self._draw_launch_hint()

            if self.state == "paused":
                self._draw_overlay("PAUSED", "",
                                   "P  or  Options  to resume")
            elif self.state == "gameover":
                self._draw_overlay("GAME OVER",
                                   f"Final Score:  {self.score}",
                                   "R  or  face button  to restart")
            elif self.state == "won":
                self._draw_overlay("YOU WIN!",
                                   f"Final Score:  {self.score}",
                                   "R  or  face button  to play again")

            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
