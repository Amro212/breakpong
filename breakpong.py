import pygame
import sys
import random
import time

pygame.init()

# --------------------
# Screen Setup
# --------------------
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BreakPong - Spin & Power-Ups")

# --------------------
# Colors & Palettes
# --------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TITLE_COLOR = (255, 200, 0)

COLOR_PALETTE = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 100, 255),
    (255, 255, 100),
    (255, 150, 200),
    (200, 150, 255),
    (255, 120, 0),
    (0, 200, 200),
    (200, 100, 50),
]

BUTTON_COLOR = (0, 150, 255)
BUTTON_HOVER_COLOR = (0, 200, 255)

# --------------------
# Fonts
# --------------------
# Load the pixel font
try:
    title_font = pygame.font.Font('assets/Retro.ttf', 50)
    menu_font = pygame.font.Font('assets/Retro.ttf', 32)
    help_font = pygame.font.Font('assets/Retro.ttf', 19)
    score_font = pygame.font.Font('assets/Retro.ttf', 30)
    small_menu_font = pygame.font.Font('assets/Retro.ttf', 24)  # Smaller font for certain buttons
except:
    print("Could not load pixel font. Using system font as fallback.")
    title_font = pygame.font.SysFont(None, 72)
    menu_font = pygame.font.SysFont(None, 48)
    help_font = pygame.font.SysFont(None, 32)
    score_font = pygame.font.SysFont(None, 36)
    small_menu_font = pygame.font.SysFont(None, 28)  # Smaller font for certain buttons

# --------------------
# Game Constants
# --------------------
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 10
BALL_SPEED = 4
PADDLE_SPEED = 5

# Two rows of bricks: top (y=0) and bottom (y=HEIGHT - BRICK_HEIGHT).
BRICK_COLUMNS = 8
BRICK_WIDTH = 60
BRICK_HEIGHT = 20

# --------------------
# States
# --------------------
STATE_INTRO = "INTRO"
STATE_MENU = "MENU"
STATE_HELP = "HELP"
STATE_SETTINGS = "SETTINGS"
STATE_INITIAL_COUNTDOWN = "INITIAL_COUNTDOWN"
STATE_GAME = "GAME"
STATE_GRACE = "GRACE"
STATE_GAME_OVER = "GAME_OVER"

# --------------------
# Global Variables
# --------------------
current_state = STATE_INTRO
score_left = 0
score_right = 0
timer_start = None
game_winner = None
winning_score = 5

intro_start_time = pygame.time.get_ticks()

# We'll store the current vertical speed of each paddle to apply spin.
paddle_left_speed = 0
paddle_right_speed = 0

# Duration (in milliseconds) that a paddle remains enlarged after collecting a power-up
POWERUP_DURATION = 5000  

# Track when each paddle returns to normal size
paddle_left_end_power_time = 0
paddle_right_end_power_time = 0

# Original paddle height
BASE_PADDLE_HEIGHT = PADDLE_HEIGHT

# --------------------
# Button Rects
# --------------------
button_width = 200
button_height = 50
spacing = 10

start_button_rect = pygame.Rect(
    (WIDTH // 2 - button_width // 2),
    (HEIGHT // 2 - button_height // 2) - (button_height + spacing),
    button_width,
    button_height
)
help_button_rect = pygame.Rect(
    (WIDTH // 2 - button_width // 2),
    (HEIGHT // 2 - button_height // 2),
    button_width,
    button_height
)
settings_button_rect = pygame.Rect(
    (WIDTH // 2 - button_width // 2),
    (HEIGHT // 2 - button_height // 2) + (button_height + spacing),
    button_width,
    button_height
)
exit_button_rect = pygame.Rect(WIDTH - 110, 10, 100, 40)

# Winning score buttons in settings
win_score_5_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 80, 40)
win_score_10_rect = pygame.Rect(WIDTH // 2 - 40, HEIGHT // 2, 80, 40)
win_score_15_rect = pygame.Rect(WIDTH // 2 + 70, HEIGHT // 2, 80, 40)

# Game over menu button
menu_button_rect = pygame.Rect(
    (WIDTH // 2 - button_width // 2),
    HEIGHT // 2 + 40,
    button_width,
    button_height
)

# --------------------
# Particle Class (Intro)
# --------------------
class Particle:
    def __init__(self):
        self.size = random.randint(4, 8)
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-100, 100)
        self.color = random.choice(COLOR_PALETTE)
        self.lifetime = random.uniform(1.5, 3.0)
        self.age = 0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt

    def is_dead(self):
        return self.age >= self.lifetime

    def draw(self, surface):
        alpha = max(0, 255 - int((self.age / self.lifetime) * 255))
        srf = pygame.Surface((self.size, self.size))
        srf.fill(self.color)
        srf.set_alpha(alpha)
        surface.blit(srf, (self.x, self.y))

particles = []

# --------------------
# PowerUp Class
# --- NEW: PowerUps ---
# --------------------
# Remove the PowerUp class since we don't need it anymore
# Keep track of power-ups in a global list
power_ups = []

# --------------------
# Paddles & Ball
# --------------------
paddle_left = pygame.Rect(20, HEIGHT // 2 - PADDLE_HEIGHT // 2, 10, PADDLE_HEIGHT)
paddle_right = pygame.Rect(WIDTH - 30, HEIGHT // 2 - PADDLE_HEIGHT // 2, 10, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)
ball_dx = BALL_SPEED
ball_dy = BALL_SPEED

bricks = []
last_hit = None

# --------------------
# Visual Helpers
# --------------------
def draw_gradient_background(surface, color_top, color_bottom):
    h = surface.get_height()
    w = surface.get_width()
    for y in range(h):
        ratio = y / float(h)
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

def draw_button(rect, text, font=None):
    mx, my = pygame.mouse.get_pos()
    color = BUTTON_HOVER_COLOR if rect.collidepoint(mx, my) else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=8)
    txt_surface = (font or menu_font).render(text, True, WHITE)
    txt_rect = txt_surface.get_rect(center=rect.center)
    screen.blit(txt_surface, txt_rect)

def check_button_click(rect):
    mx, my = pygame.mouse.get_pos()
    return rect.collidepoint(mx, my)

def render_text_centered(text, font_obj, color, y):
    txt_surface = font_obj.render(text, True, color)
    txt_rect = txt_surface.get_rect(center=(WIDTH // 2, y))
    screen.blit(txt_surface, txt_rect)

def draw_menu_overlay(alpha):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(alpha)
    overlay.fill((40, 0, 70))

    title_surf = title_font.render("BreakPong", True, TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    overlay.blit(title_surf, title_rect)

    def temp_button(rect, label):
        pygame.draw.rect(overlay, BUTTON_COLOR, rect, border_radius=8)
        btn_text = menu_font.render(label, True, WHITE)
        btn_rect = btn_text.get_rect(center=rect.center)
        overlay.blit(btn_text, btn_rect)

    temp_button(start_button_rect, "START")
    temp_button(help_button_rect, "HELP")
    temp_button(settings_button_rect, "SETTINGS")

    screen.blit(overlay, (0, 0))

# --------------------
# Brick Creation
# --------------------
def create_bricks():
    """
    Two rows:
      - Top row at y=0
      - Bottom row at y=HEIGHT - BRICK_HEIGHT
    """
    global bricks
    bricks = []

    start_x = (WIDTH - (BRICK_COLUMNS * BRICK_WIDTH)) // 2

    # Top row
    top_y = 0
    for col in range(BRICK_COLUMNS):
        x = start_x + col * BRICK_WIDTH
        color = random.choice(COLOR_PALETTE)
        rect = pygame.Rect(x, top_y, BRICK_WIDTH, BRICK_HEIGHT)
        bricks.append((rect, color))

    # Bottom row
    bottom_y = HEIGHT - BRICK_HEIGHT
    for col in range(BRICK_COLUMNS):
        x = start_x + col * BRICK_WIDTH
        color = random.choice(COLOR_PALETTE)
        rect = pygame.Rect(x, bottom_y, BRICK_WIDTH, BRICK_HEIGHT)
        bricks.append((rect, color))

def reset_ball():
    global ball, ball_dx, ball_dy
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_dx = BALL_SPEED if ball_dx < 0 else -BALL_SPEED
    ball_dy = BALL_SPEED

def reset_paddles():
    paddle_left.y = HEIGHT // 2 - paddle_left.height // 2
    paddle_right.y = HEIGHT // 2 - paddle_right.height // 2

def check_for_winner():
    global current_state, game_winner
    if score_left >= winning_score:
        game_winner = "LEFT"
        current_state = STATE_GAME_OVER
    elif score_right >= winning_score:
        game_winner = "RIGHT"
        current_state = STATE_GAME_OVER

# --------------------
# Main Loop
# --------------------
clock = pygame.time.Clock()
running = True

create_bricks()  # top & bottom
while running:
    dt = clock.get_time() / 1000.0
    clock.tick(60)

    # --------------------
    # Event Handling
    # --------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # If not in INTRO/MENU/GAME_OVER, the EXIT button can return to MENU
        if current_state not in (STATE_INTRO, STATE_MENU, STATE_GAME_OVER) and event.type == pygame.MOUSEBUTTONDOWN:
            if check_button_click(exit_button_rect):
                current_state = STATE_MENU

        # Intro skip
        if current_state == STATE_INTRO and event.type == pygame.KEYDOWN:
            current_state = STATE_MENU

        # Menu button clicks
        if current_state == STATE_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if check_button_click(start_button_rect):
                    score_left = 0
                    score_right = 0
                    # Reset paddle sizes in case they were enlarged
                    paddle_left.height = PADDLE_HEIGHT
                    paddle_right.height = PADDLE_HEIGHT
                    reset_paddles()
                    reset_ball()
                    create_bricks()
                    power_ups.clear()
                    timer_start = pygame.time.get_ticks()
                    current_state = STATE_INITIAL_COUNTDOWN
                elif check_button_click(help_button_rect):
                    current_state = STATE_HELP
                elif check_button_click(settings_button_rect):
                    current_state = STATE_SETTINGS

        elif current_state == STATE_HELP:
            if event.type == pygame.KEYDOWN:
                current_state = STATE_MENU

        elif current_state == STATE_SETTINGS:
            if event.type == pygame.KEYDOWN:
                current_state = STATE_MENU
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if check_button_click(win_score_5_rect):
                    winning_score = 5
                elif check_button_click(win_score_10_rect):
                    winning_score = 10
                elif check_button_click(win_score_15_rect):
                    winning_score = 15

        elif current_state in (STATE_INITIAL_COUNTDOWN, STATE_GAME, STATE_GRACE):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                current_state = STATE_MENU

        elif current_state == STATE_GAME_OVER:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if check_button_click(menu_button_rect):
                    current_state = STATE_MENU

    # --------------------
    # State-Specific Logic
    # --------------------
    # --- Update paddle sizes if a power-up effect expired ---
    current_time = pygame.time.get_ticks()
    if current_time >= paddle_left_end_power_time:
        paddle_left.height = PADDLE_HEIGHT
    if current_time >= paddle_right_end_power_time:
        paddle_right.height = PADDLE_HEIGHT

    # Movement keys for spin tracking:
    # We'll set the paddle_*_speed so we can adjust ball_dy upon collision.
    paddle_left_speed = 0
    paddle_right_speed = 0

    if current_state == STATE_GAME:
        keys = pygame.key.get_pressed()
        # Left paddle
        if keys[pygame.K_w] and paddle_left.top > 0:
            paddle_left.y -= PADDLE_SPEED
            paddle_left_speed = -PADDLE_SPEED
        elif keys[pygame.K_s] and paddle_left.bottom < HEIGHT:
            paddle_left.y += PADDLE_SPEED
            paddle_left_speed = PADDLE_SPEED

        # Right paddle
        if keys[pygame.K_UP] and paddle_right.top > 0:
            paddle_right.y -= PADDLE_SPEED
            paddle_right_speed = -PADDLE_SPEED
        elif keys[pygame.K_DOWN] and paddle_right.bottom < HEIGHT:
            paddle_right.y += PADDLE_SPEED
            paddle_right_speed = PADDLE_SPEED

    # --------------------
    # Drawing / Updates per State
    # --------------------
    if current_state == STATE_INTRO:
        screen.fill(BLACK)
        # Particle logic
        for _ in range(3):
            particles.append(Particle())
        for p in particles[:]:
            p.update(dt)
            p.draw(screen)
            if p.is_dead():
                particles.remove(p)

        elapsed = pygame.time.get_ticks() - intro_start_time
        if elapsed < 2000:
            alpha = int((elapsed / 2000) * 255)
        elif elapsed < 3000:
            alpha = 255
        elif elapsed < 4000:
            alpha = int(255 - ((elapsed - 3000) / 1000) * 255)
        else:
            current_state = STATE_MENU
            continue

        logo_surface = title_font.render("BreakPong", True, TITLE_COLOR).convert_alpha()
        credits_surface = help_font.render("A Retro Mashup", True, WHITE).convert_alpha()
        by_surface = help_font.render("By: @amro212", True, WHITE).convert_alpha()
        logo_surface.set_alpha(alpha)
        credits_surface.set_alpha(alpha)
        by_surface.set_alpha(alpha)
        logo_rect = logo_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        credits_rect = credits_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        by_rect = by_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        screen.blit(logo_surface, logo_rect)
        screen.blit(credits_surface, credits_rect)
        screen.blit(by_surface, by_rect)

        if elapsed > 3000:
            overlay_alpha = int(((elapsed - 3000) / 1000) * 255)
            draw_menu_overlay(overlay_alpha)

    elif current_state == STATE_MENU:
        draw_gradient_background(screen, (40, 0, 70), (0, 0, 0))
        render_text_centered("BreakPong", title_font, TITLE_COLOR, HEIGHT // 4)
        draw_button(start_button_rect, "START")
        draw_button(help_button_rect, "HELP")
        draw_button(settings_button_rect, "SETTINGS")

    elif current_state == STATE_HELP:
        screen.fill(BLACK)
        render_text_centered("HELP", title_font, TITLE_COLOR, 60)
        lines = [
            "Controls:",
            "  Left Paddle: W/S",
            "  Right Paddle: Up/Down",
            "",
            "Angle/Spin:",
            "  Moving the paddle up or down at impact adds spin!",
            "",
            "Power-Ups:",
            "  Breaking a brick may drop a power-up that",
            "  temporarily enlarges your paddle if collected.",
            "",
            "(Press any key to return)"
        ]
        y_offset = 120
        for line in lines:
            render_text_centered(line, help_font, WHITE, y_offset)
            y_offset += 35
        draw_button(exit_button_rect, "EXIT")

    elif current_state == STATE_SETTINGS:
        screen.fill(BLACK)
        render_text_centered("SETTINGS", title_font, TITLE_COLOR, 60)
        lines = [
            "Select a winning score:",
            "First player to reach this score wins!",
            ""
        ]
        y_offset = 150
        for line in lines:
            render_text_centered(line, help_font, WHITE, y_offset)
            y_offset += 40

        draw_button(win_score_5_rect, "5")
        draw_button(win_score_10_rect, "10")
        draw_button(win_score_15_rect, "15")

        current_setting_text = f"Current Winning Score: {winning_score}"
        render_text_centered(current_setting_text, help_font, WHITE, HEIGHT - 40)

        draw_button(exit_button_rect, "EXIT")

    elif current_state == STATE_INITIAL_COUNTDOWN:
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, paddle_left)
        pygame.draw.rect(screen, WHITE, paddle_right)
        pygame.draw.ellipse(screen, WHITE, ball)
        for (brick_rect, brick_color) in bricks:
            pygame.draw.rect(screen, brick_color, brick_rect)

        # Score
        score_text = score_font.render(f"{score_left} : {score_right}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 35))
        screen.blit(score_text, score_rect)

        elapsed = pygame.time.get_ticks() - timer_start
        if elapsed < 1000:
            countdown_str = "3"
        elif elapsed < 2000:
            countdown_str = "2"
        elif elapsed < 3000:
            countdown_str = "1"
        elif elapsed < 3500:
            countdown_str = "GO!"
        else:
            current_state = STATE_GAME
            countdown_str = ""

        if countdown_str:
            c_text = title_font.render(countdown_str, True, TITLE_COLOR)
            c_rect = c_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(c_text, c_rect)

        draw_button(exit_button_rect, "EXIT")

    elif current_state == STATE_GAME:
        # --- Paddle movement logic was done above ---
        # Move the ball
        ball.x += ball_dx
        ball.y += ball_dy

        # Collide with top/bottom edges
        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball_dy = -ball_dy

        # --- NEW: Spin logic ---
        # Check collisions with paddles
        if ball.colliderect(paddle_left):
            MAX_SPEED = 6
            ball_dx = abs(ball_dx)
            last_hit = "left"
            # Add spin while maintaining constant speed
            ball_dy += paddle_left_speed * 0.1  # Reduced multiplier
            ball_dy += (paddle_left.centery - ball.centery) * 0.05  # Angle adjustment
            ball.x += 5  # Move the ball slightly away from the paddle

            # Normalize the speed
            speed = (ball_dx * ball_dx + ball_dy * ball_dy) ** 0.5
            if speed > MAX_SPEED:
                ball_dx = (ball_dx / speed) * MAX_SPEED
                ball_dy = (ball_dy / speed) * MAX_SPEED

        if ball.colliderect(paddle_right):
            ball_dx = -abs(ball_dx)
            last_hit = "right"
            # Add spin while maintaining constant speed
            ball_dy += paddle_right_speed * 0.1  # Reduced multiplier
            ball_dy += (paddle_right.centery - ball.centery) * 0.05  # Angle adjustment
            ball.x -= 5  # Move the ball slightly away from the paddle

            # Normalize the speed
            speed = (ball_dx * ball_dx + ball_dy * ball_dy) ** 0.5
            if speed > MAX_SPEED:
                ball_dx = (ball_dx / speed) * MAX_SPEED
                ball_dy = (ball_dy / speed) * MAX_SPEED

        # Lost round
        if ball.left <= 0:
            # Right scores
            score_right += 1
            reset_ball()
            reset_paddles()
            timer_start = pygame.time.get_ticks()
            current_state = STATE_GRACE
            check_for_winner()
        elif ball.right >= WIDTH:
            # Left scores
            score_left += 1
            reset_ball()
            reset_paddles()
            timer_start = pygame.time.get_ticks()
            current_state = STATE_GRACE
            check_for_winner()

        # Collide with bricks
        # If a brick is destroyed, give power-up to the player who hit it
        for i, (brick_rect, brick_color) in enumerate(bricks):
            if ball.colliderect(brick_rect):
                del bricks[i]
                ball_dy = -ball_dy
                # 20% chance to get a power-up
                if random.random() < 0.2:
                    # Give power-up to the last player who hit the ball
                    if last_hit == "left":
                        paddle_left.height = int(paddle_left.height * 1.5)
                        paddle_left.centery = paddle_left.centery
                        paddle_left_end_power_time = pygame.time.get_ticks() + POWERUP_DURATION
                    elif last_hit == "right":
                        paddle_right.height = int(paddle_right.height * 1.5)
                        paddle_right.centery = paddle_right.centery
                        paddle_right_end_power_time = pygame.time.get_ticks() + POWERUP_DURATION                        
                break

        # Draw everything
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, paddle_left)
        pygame.draw.rect(screen, WHITE, paddle_right)
        pygame.draw.ellipse(screen, WHITE, ball)

        for (brick_rect, brick_color) in bricks:
            pygame.draw.rect(screen, brick_color, brick_rect)

        # Score
        score_text = score_font.render(f"{score_left} : {score_right}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 35))
        screen.blit(score_text, score_rect)

        draw_button(exit_button_rect, "EXIT")

    elif current_state == STATE_GRACE:
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, paddle_left)
        pygame.draw.rect(screen, WHITE, paddle_right)
        pygame.draw.ellipse(screen, WHITE, ball)
        for (brick_rect, brick_color) in bricks:
            pygame.draw.rect(screen, brick_color, brick_rect)

        score_text = score_font.render(f"{score_left} : {score_right}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 35))
        screen.blit(score_text, score_rect)

        if pygame.time.get_ticks() - timer_start >= 1000:
            if current_state == STATE_GRACE:
                current_state = STATE_GAME
                create_bricks()  # to regenerate blocks after each round

        draw_button(exit_button_rect, "EXIT")

    elif current_state == STATE_GAME_OVER:
        screen.fill(BLACK)
        if game_winner:
            text = f"{game_winner} PLAYER WINS!"
        else:
            text = "No Winner"
        render_text_centered(text, title_font, TITLE_COLOR, HEIGHT // 2 - 30)
        draw_button(menu_button_rect, "BACK TO MENU", small_menu_font)

    pygame.display.flip()

pygame.quit()
sys.exit()
