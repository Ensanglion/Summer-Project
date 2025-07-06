import pygame
import random
import time
import csv
from classes import *

# General game setup -----------------------------------------------------------

pygame.init()
pygame.mixer.init()  # Initialize the mixer for audio
WIDTH, HEIGHT = 1440, 900
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Catch the Healthy Food")

FPS = 60
FONT = pygame.font.SysFont("arial", 24)
HUD_FONT = pygame.font.SysFont("arial", 48)  # Twice the size for HUD text
MENU_FONT = pygame.font.SysFont("arial", 64)


# Load images
BACKGROUND_IMG = pygame.image.load("new_sprites\\spr_chefs_BG\\spr_chefs_BG_0.png")
BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (WIDTH, HEIGHT))

def load_and_scale_sprite(path, target_width, target_height):
    """Load a sprite and scale it to fit within target dimensions while maintaining aspect ratio"""
    original = pygame.image.load(path)
    orig_width, orig_height = original.get_size()
    
    # Calculate scale to fit within target dimensions
    scale_x = target_width / orig_width
    scale_y = target_height / orig_height
    scale = min(scale_x, scale_y)  # Use the smaller scale to maintain aspect ratio
    
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)
    
    # Scale the sprite
    scaled = pygame.transform.scale(original, (new_width, new_height))
    
    # Create a new surface with target dimensions and transparent background
    final_surface = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
    
    # Center the scaled sprite on the final surface
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    final_surface.blit(scaled, (x_offset, y_offset))
    
    return final_surface

# Player sprites
PLAYER_WIDTH, PLAYER_HEIGHT = 70, 120
PLAYER_SPRITES = {
    "idle": load_and_scale_sprite("new_sprites\\spr_kris_chef_default.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "walk_left": load_and_scale_sprite("new_sprites\\spr_kris_chef_walk\\spr_kris_chef_walk_0.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "walk_right": load_and_scale_sprite("new_sprites\\spr_kris_chef_walk\\spr_kris_chef_walk_1.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "jump": load_and_scale_sprite("new_sprites\\spr_kris_chef_jump.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "hit": load_and_scale_sprite("new_sprites\\spr_chefs_kris_stun\\spr_chefs_kris_stun_0.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "stunned": load_and_scale_sprite("new_sprites\\spr_chefs_kris_stun\\spr_chefs_kris_stun_1.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "throw_start": load_and_scale_sprite("new_sprites\\spr_chefs_kris_throw\\spr_chefs_kris_throw_0.png", PLAYER_WIDTH, PLAYER_HEIGHT),
    "throw": load_and_scale_sprite("new_sprites\\spr_chefs_kris_throw\\spr_chefs_kris_throw_1.png", PLAYER_WIDTH, PLAYER_HEIGHT),
}

CUSTOMER_SPRITES = [
    load_and_scale_sprite("new_sprites\\spr_shadowman_run3\\spr_shadowman_run3_1.png", 100, 120),
    load_and_scale_sprite("new_sprites\\spr_shadowman_run3\\spr_shadowman_run3_0.png", 100, 120),
]
FIREBALL_SPRITE = load_and_scale_sprite(
    "new_sprites\\spr_kitchen_fire_ball\\spr_kitchen_fire_ball_1.png",
    40, 40
)
FOOD_WARNING_SPRITE = pygame.transform.scale(
    pygame.image.load("new_sprites\\spr_chefs_foodnotice\\spr_chefs_foodnotice_0.png"),
    (50, 50)  # Even smaller size for the warning
)
SCOREBOARD_SPRITE = pygame.transform.scale(
    pygame.image.load("new_sprites\\spr_chefs_hudscreen.png"), (250, 120)
)


# Constants
GROUND_Y = HEIGHT - PLAYER_HEIGHT - 250
PLAYER_START_X = WIDTH // 2
MAX_FOOD_STACK = 5
STUN_DURATION = 1
FIREBALL_SPAWN_INTERVAL = 5000
CUSTOMER_SPAWN_INTERVAL = 1600 
MISSED_FOOD_FIREBALL_DURATION = 1500

# Helper functions -----------------------------------------------------------

def draw_text_centered(win, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    win.blit(rendered, rect)

def draw_button(win, text, font, color, hover_color, rect, mouse_pos, mouse_click):
    is_hovered = rect.collidepoint(mouse_pos)
    pygame.draw.rect(win, hover_color if is_hovered else color, rect, border_radius=12)
    label = font.render(text, True, (255, 255, 255))
    label_rect = label.get_rect(center=rect.center)
    win.blit(label, label_rect)
    return is_hovered and mouse_click[0]
 

# Helper Classes -----------------------------------------------------------

class Player:
    def __init__(self):
        self.x = PLAYER_START_X
        self.y = GROUND_Y
        self.vel_y = 0
        self.gravity = 0.8
        self.jump_strength = -15
        self.on_ground = True
        self.base_speed = 8
        self.speed = self.base_speed
        self.direction = "idle"
        self.state = "normal"
        self.throw_anim_time = 0
        self.threw_this_cycle = False
        self.stun_time = 0
        self.food_stack = []

    def update_speed(self):
        penalty = min(len(self.food_stack) * 0.1, 0.5)
        self.speed = self.base_speed * (1 - penalty)

    def move(self, keys):
        if self.state in ["hit", "stunned", "throw_start", "throwing"]:
            return
        moving = False
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
            self.direction = "left"
            moving = True
        if keys[pygame.K_RIGHT] and self.x < WIDTH - PLAYER_WIDTH:
            self.x += self.speed
            self.direction = "right"
            moving = True
        if not moving:
            self.direction = "idle"
        if keys[pygame.K_x] and self.on_ground:
            self.vel_y = self.jump_strength
            self.on_ground = False

    def apply_gravity(self):
        self.vel_y += self.gravity
        self.y += self.vel_y
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

    def start_throw(self):
        if self.state == "normal" and len(self.food_stack) > 0:
            self.state = "throw_start"
            self.throw_anim_time = pygame.time.get_ticks()

    def update_throw(self):
        now = pygame.time.get_ticks()
        if self.state == "throw_start" and now - self.throw_anim_time > 150:
            self.state = "throwing"
        elif self.state == "throwing" and now - self.throw_anim_time > 300:
            self.state = "normal"
            self.threw_this_cycle = False  # Reset flag when throwing ends


    def get_current_sprite(self):
        if self.state == "hit":
            return PLAYER_SPRITES["hit"]
        elif self.state == "stunned":
            return PLAYER_SPRITES["stunned"]
        elif self.state == "throw_start":
            return PLAYER_SPRITES["throw_start"]
        elif self.state == "throwing":
            return PLAYER_SPRITES["throw"]
        elif not self.on_ground:
            return PLAYER_SPRITES["jump"]
        else:
            if self.direction == "left":
                return PLAYER_SPRITES["walk_left"]
            elif self.direction == "right":
                return PLAYER_SPRITES["walk_right"]
            else:
                return PLAYER_SPRITES["idle"]

    def stun(self):
        self.state = "stunned"
        self.stun_time = pygame.time.get_ticks()
        self.food_stack.clear()
        self.update_speed()

    def update_stun(self):
        if self.state == "stunned":
            if pygame.time.get_ticks() - self.stun_time > STUN_DURATION * 1000:
                self.state = "normal"


class Customer:
    def __init__(self):
        self.y = GROUND_Y + 200  # slightly below player ground line
        self.x = WIDTH + 50  # spawn off right edge
        self.speed = 3
        self.sprite_index = 0
        self.last_sprite_switch = pygame.time.get_ticks()
        self.width = 100
        self.height = 120
        self.hitbox = pygame.Rect(self.x, self.y, self.width, self.height)
        self.alive = True

    def update(self):
        self.x -= self.speed
        now = pygame.time.get_ticks()
        if now - self.last_sprite_switch > 300:
            self.sprite_index = 1 - self.sprite_index
            self.last_sprite_switch = now
        self.hitbox.topleft = (self.x, self.y)
        if self.x < -self.width:
            self.alive = False

    def draw(self, win):
        sprite = CUSTOMER_SPRITES[self.sprite_index]
        win.blit(sprite, (self.x, self.y))


class Fireball:
    def __init__(self, x, y, direction, is_obstacle=True):
        self.x = x
        self.y = y
        self.speed = 4  # Slower speed for obstacle fireballs
        self.direction = direction  # either "left" or "right"
        self.width = 40
        self.height = 40
        self.hitbox = pygame.Rect(self.x + 10, self.y + 10, 20, 20)
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.is_obstacle = is_obstacle
        self.visible = True  # For blinking effect

    def update(self):
        if self.is_obstacle:
            # Moving obstacle fireballs
            if self.direction == "left":
                self.x -= self.speed
            else:
                self.x += self.speed
            self.hitbox.topleft = (self.x, self.y)

            # Remove if off screen
            if self.x < -self.width or self.x > WIDTH + self.width:
                self.alive = False
        else:
            # Static penalty fireballs - stay in place for 2 seconds with blinking
            self.hitbox.topleft = (self.x, self.y)
            current_time = pygame.time.get_ticks()
            time_alive = current_time - self.spawn_time
            
            if time_alive > 2000:  # 2 seconds total
                self.alive = False
            elif time_alive > 1200:  # Start blinking at 1.2 seconds
                # Blink every 100ms (10 times per second)
                self.visible = (time_alive // 100) % 2 == 0

    def draw(self, win):
        if self.visible:
            win.blit(FIREBALL_SPRITE, (self.x, self.y))


class ObstacleFireball:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 3
        self.direction = direction  # either "left" or "right"
        self.width = 40
        self.height = 40
        self.hitbox = pygame.Rect(self.x + 10, self.y + 10, 20, 20)
        self.alive = True

    def update(self):
        if self.direction == "left":
            self.x -= self.speed
        else:
            self.x += self.speed
        self.hitbox.topleft = (self.x + 10, self.y + 10)

        if self.x < -self.width or self.x > WIDTH + self.width:
            self.alive = False

    def draw(self, win):
        win.blit(FIREBALL_SPRITE, (self.x, self.y))


class ThrownFood:
    def __init__(self, food, x, y):
        self.food = food
        self.x = x
        self.y = y
        self.speed = 10
        self.width = 50
        self.height = 50
        self.hitbox = pygame.Rect(self.x, self.y, self.width, self.height)
        self.alive = True

    def update(self):
        self.y += self.speed
        self.hitbox.topleft = (self.x, self.y)
        if self.y > HEIGHT + self.height:
            self.alive = False

    def draw(self, win):
        img = pygame.image.load(self.food.path)
        win.blit(pygame.transform.scale(img, (self.width, self.height)), (self.x, self.y))


# All game parts (menu, game, controls, about, leaderboard) ---------------------------------------------

def show_instructions():
    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        draw_text_centered(WIN, "Instructions", MENU_FONT, (255, 255, 255), 100)
        draw_text_centered(WIN, "Move using arrow keys: ← → ", FONT, (255, 255, 255), 200)
        draw_text_centered(WIN, "Press X to jump", FONT, (255, 255, 255), 250)
        draw_text_centered(WIN, "Press Z to throw stacked healthy food", FONT, (255, 255, 255), 300)
        draw_text_centered(WIN, "Avoid fireballs and unhealthy food", FONT, (255, 255, 255), 370)
        draw_text_centered(WIN, "ESC to return", FONT, (200, 200, 200), 450)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

def show_about():
    # Load the data plot image
    try:
        plot_img = pygame.image.load("data_plot_high_res.png")
        # Scale the plot to maintain quality while fitting on screen
        plot_img = pygame.transform.scale(plot_img, (800, 600))
    except pygame.error as e:
        print(f"Could not load data plot: {e}")
        plot_img = None
    
    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        # Draw title at the top
        draw_text_centered(WIN, "About", MENU_FONT, (255, 255, 255), 80)
        
        # Draw the data plot on the right side
        if plot_img:
            plot_rect = plot_img.get_rect(center=(WIDTH * 0.7, HEIGHT * 0.55))
            WIN.blit(plot_img, plot_rect)
        
        # Draw text on the left side
        left_text_x = WIDTH * 0.25  # 25% from left edge
        
        # Helper function to draw left-aligned text
        def draw_left_text(text, font, color, y):
            rendered = font.render(text, True, color)
            WIN.blit(rendered, (left_text_x - rendered.get_width()//2, y))
        
        # Text content on the left
        # First line positioned further right
        first_line_x = WIDTH * 0.45  # 45% from left edge for first line only
        first_line_text = "The game has different kinds of food with random calories assigned. Using a dataset of foods, we found a linear relation:"
        first_line_rendered = FONT.render(first_line_text, True, (0, 0, 0))
        WIN.blit(first_line_rendered, (first_line_x - first_line_rendered.get_width()//2, 150))
        draw_left_text("", FONT, (0, 0, 0), 180)  # Spacing
        draw_left_text("Linear relation equation:", FONT, (0, 0, 0), 210)
        draw_left_text("Total Fat (g) = 0.0448 × Energy (kCal) - 2.1217", FONT, (0, 0, 0), 240)
        draw_left_text("", FONT, (0, 0, 0), 270)  # Spacing
        draw_left_text("Healthy food is defined as food with less than 20g of fat.", FONT, (0, 0, 0), 300)
        draw_left_text("Your goal is to catch healthy food and throw it at the customers.", FONT, (0, 0, 0), 615)
        draw_left_text("Avoid unhealthy food and fireballs!", FONT, (0, 0, 0), 645)
        
        # Return instruction at bottom
        draw_text_centered(WIN, "ESC to return", FONT, (200, 200, 200), 850)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

def show_game_over_screen(final_score):
    """Show game over screen and get player name for leaderboard"""
    player_name = ""
    input_active = True
    
    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 128), (0, 0, WIDTH, HEIGHT))
        WIN.blit(overlay, (0, 0))
        
        # Draw game over title
        draw_text_centered(WIN, "GAME OVER", MENU_FONT, (255, 255, 255), 200)
        
        # Draw final score
        draw_text_centered(WIN, f"Your Score: {final_score}", HUD_FONT, (255, 255, 255), 300)
        
        # Draw input prompt
        draw_text_centered(WIN, "Enter your name:", FONT, (255, 255, 255), 400)
        
        # Draw input box
        input_rect = pygame.Rect(WIDTH//2 - 150, 430, 300, 40)
        pygame.draw.rect(WIN, (255, 255, 255), input_rect, 2)
        pygame.draw.rect(WIN, (50, 50, 50), input_rect)
        
        # Draw player name text
        name_surface = FONT.render(player_name, True, (255, 255, 255))
        WIN.blit(name_surface, (input_rect.x + 10, input_rect.y + 10))
        
        # Draw instruction
        draw_text_centered(WIN, "Press ENTER to save score", FONT, (200, 200, 200), 500)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    # Save score to leaderboard
                    save_score_to_leaderboard(player_name.strip(), final_score)
                    running = False
                    # Change music back to menu theme
                    try:
                        pygame.mixer.music.load("silly_menu.mp3")
                        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                    except pygame.error as e:
                        print(f"Could not load menu music: {e}")
                    return  # Return to main menu instead of quitting
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode.isprintable() and len(player_name) < 20:
                    player_name += event.unicode

def save_score_to_leaderboard(name, score):
    """Save player name and score to leaderboard.csv"""
    try:
        # Read existing scores
        scores = []
        try:
            with open("leaderboard.csv", newline='', mode='r') as file:
                reader = csv.reader(file)
                # Skip header row if it exists
                header = next(reader, None)
                if header and header[0] == "Name":
                    # File has header, read all data rows
                    scores = list(reader)
                else:
                    # No header, treat first row as data
                    if header:
                        scores = [header]
                    scores.extend(list(reader))
        except FileNotFoundError:
            pass
        
        # Add new score
        scores.append([name, str(score)])
        
        # Sort by score (descending) and keep top 10
        scores.sort(key=lambda row: int(row[1]), reverse=True)
        scores = scores[:10]
        
        # Write back to file with header
        with open("leaderboard.csv", newline='', mode='w') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Score"])  # Write header
            writer.writerows(scores)
            
    except Exception as e:
        print(f"Error saving score: {e}")

def show_leaderboard():
    scores = []
    try:
        with open("leaderboard.csv", newline='') as file:
            reader = csv.reader(file)
            # Skip header row if it exists
            header = next(reader, None)
            if header and header[0] == "Name":
                # File has header, read all data rows
                scores = list(reader)
            else:
                # No header, treat first row as data
                if header:
                    scores = [header]
                scores.extend(list(reader))
    except FileNotFoundError:
        pass

    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        draw_text_centered(WIN, "Leaderboard", MENU_FONT, (255, 255, 255), 80)
        
        if scores:
            for i, (name, score) in enumerate(scores):
                draw_text_centered(WIN, f"{i+1}. {name}: {score}", FONT, (255, 255, 255), 160 + i*50)
        else:
            draw_text_centered(WIN, "No scores yet!", FONT, (255, 255, 255), 200)
            
        draw_text_centered(WIN, "ESC to return", FONT, (200, 200, 200), 500)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False


def run_game():
    clock = pygame.time.Clock()

    # Load and play background music
    try:
        pygame.mixer.music.load("game_active.mp3")
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        print("Music loaded and playing!")
    except pygame.error as e:
        print(f"Could not load music: {e}")
    player = Player()
    score = 0
    timer = 90  # seconds
    start_time = pygame.time.get_ticks()

    current_food = None
    food_img = None
    food_x = 0
    food_y = 0
    food_speed = 4
    food_spawn_time = 0
    food_warning_visible = False
    food_warning_x = 0  # Track warning x position
    obstacle_warning_visible = False
    obstacle_warning_side = "left"  # Track which side obstacle will spawn
    obstacle_warning_time = 0

    customers = []
    fireballs = []
    obstacle_fireballs = []
    thrown_foods = []

    last_customer_spawn = 0
    last_fireball_spawn = 0

    running = True

    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        # Background
        WIN.blit(BACKGROUND_IMG, (0, 0))

        # Draw HUD sprite in center (after background, before other elements)
        hud_x = WIDTH // 2 - 225  # Move slightly to the left
        hud_y = 120  # Move lower
        # Scale the HUD sprite to be larger (250x120 -> 450x220)
        scaled_hud = pygame.transform.scale(SCOREBOARD_SPRITE, (450, 220))
        WIN.blit(scaled_hud, (hud_x, hud_y))

        # Draw score text on HUD
        score_label = HUD_FONT.render("SCORE:", True, (255, 255, 255))  # White text
        score_value = HUD_FONT.render(str(score), True, (255, 255, 255))  # White text
        
        # Center text on scaled HUD sprite (450 width)
        label_x = hud_x + (450 - score_label.get_width()) // 2
        label_y = hud_y + 60  # Moved lower to avoid overlap with timer
        value_x = hud_x + (450 - score_value.get_width()) // 2
        value_y = hud_y + 120  # Moved lower to avoid overlap with timer
        
        WIN.blit(score_label, (label_x, label_y))
        WIN.blit(score_value, (value_x, value_y))

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # Update player stun timer
        player.update_stun()

        # Player actions
        player.move(keys)
        player.apply_gravity()
        player.update_speed()
        player.update_throw()

        # Update timer
        elapsed_time = (now - start_time) // 1000
        time_left = max(0, timer - elapsed_time)
        
        # Draw timer text in top-left corner of HUD
        timer_text = HUD_FONT.render(f"TIME: {time_left}", True, (255, 255, 255))  # White text
        timer_x = hud_x + 20  # 20px from left edge of HUD
        timer_y = hud_y + 20  # 20px from top edge of HUD
        WIN.blit(timer_text, (timer_x, timer_y))

        # Throw food if Z pressed and allowed
        if keys[pygame.K_z]:
            player.start_throw()

        # Spawn food logic with warning sprite
        if current_food is None:
            if not food_warning_visible:
                # Set warning position first, then show warning
                food_warning_x = random.randint(0, WIDTH - 50)  # Account for warning sprite width
                food_warning_visible = True
                food_spawn_time = now + 1000  # 1 second warning
            else:
                if now >= food_spawn_time:
                    current_food = Food(path=None, calories=None)
                    food_x = food_warning_x  # Use the same x position as warning
                    food_y = -50
                    food_warning_visible = False
        else:
            # Move food down
            food_y += food_speed

            # Check catch
            food_rect = pygame.Rect(food_x, food_y, 50, 50)
            player_rect = pygame.Rect(player.x, player.y, PLAYER_WIDTH, PLAYER_HEIGHT)
            if food_rect.colliderect(player_rect) and player.state == "normal":
                # Add to stack if healthy
                if current_food.is_healthy:
                    if len(player.food_stack) < MAX_FOOD_STACK:
                        player.food_stack.append(current_food)
                        player.update_speed()
                    else:
                        # Stack full, food missed (turn into fireball)
                        fireballs.append(Fireball(food_x, GROUND_Y + 40, "left", is_obstacle=False))
                else:   
                    # Bad food hit player -> lose stack + stun
                    # Only lose points if not already stunned
                    if player.state != "stunned":
                        score = max(0, score - 25)
                    player.stun()
                current_food = None

            # Check if food hits the ground
            if food_y >= GROUND_Y:
                # Food hit the ground -> turn into fireball
                fireballs.append(Fireball(food_x, GROUND_Y + 40, "left", is_obstacle=False))
                current_food = None

        # Draw food warning if visible
        if food_warning_visible:
            WIN.blit(FOOD_WARNING_SPRITE, (food_warning_x, 50))

        # Draw obstacle warning if visible
        if obstacle_warning_visible:
            if obstacle_warning_side == "left":
                WIN.blit(FOOD_WARNING_SPRITE, (20, GROUND_Y + 20))  # Left side warning
            else:
                WIN.blit(FOOD_WARNING_SPRITE, (WIDTH - 100, GROUND_Y + 20))  # Right side warning

        # Draw current food
        if current_food:
            food_img = pygame.image.load(current_food.path)
            WIN.blit(pygame.transform.scale(food_img, (50, 50)), (food_x, food_y))
            calorie_text = FONT.render(f"{int(current_food.calories)} calories", True, (0, 0, 0))
            WIN.blit(calorie_text, (food_x + 5, food_y - 25))

        # Spawn customers every CUSTOMER_SPAWN_INTERVAL
        if now - last_customer_spawn > CUSTOMER_SPAWN_INTERVAL:
            customers.append(Customer())
            last_customer_spawn = now

        # Update and draw customers
        for c in customers[:]:
            c.update()
            c.draw(WIN)
            if not c.alive:
                customers.remove(c)

        # Spawn obstacle fireballs every FIREBALL_SPAWN_INTERVAL
        if now - last_fireball_spawn > FIREBALL_SPAWN_INTERVAL:
            if not obstacle_warning_visible:
                # Show warning first
                obstacle_warning_side = random.choice(["left", "right"])
                obstacle_warning_visible = True
                obstacle_warning_time = now + 1000  # 1 second warning
            else:
                if now >= obstacle_warning_time:
                    # Spawn the obstacle fireball
                    side = obstacle_warning_side
                    y_pos = GROUND_Y + 40
                    if side == "left":
                        x_pos = -40  # Spawn off left edge
                        direction = "right"  # Move right
                    else:
                        x_pos = WIDTH  # Spawn off right edge  
                        direction = "left"  # Move left
                    obstacle_fireballs.append(ObstacleFireball(x_pos, y_pos, direction))
                    print(f"Spawned obstacle fireball at ({x_pos}, {y_pos}) moving {direction}")  # Debug
                    obstacle_warning_visible = False
                    last_fireball_spawn = now

        # Update and draw fireballs
        for f in fireballs[:]:
            f.update()
            f.draw(WIN)
            # Check collision with player
            player_rect = pygame.Rect(player.x, player.y, PLAYER_WIDTH, PLAYER_HEIGHT)
            if f.hitbox.colliderect(player_rect):
                # Player hit by fireball - stun, lose stack, and lose points
                # Only lose points if not already stunned
                if player.state != "stunned":
                    score = max(0, score - 25)
                player.stun()
                fireballs.remove(f)
            # Remove fireballs that are no longer alive
            elif not f.alive:
                fireballs.remove(f)

        # Update and draw obstacle fireballs
        for of in obstacle_fireballs[:]:
            of.update()
            of.draw(WIN)
            # Check collision with player
            player_rect = pygame.Rect(player.x, player.y, PLAYER_WIDTH, PLAYER_HEIGHT)
            if of.hitbox.colliderect(player_rect):
                # Player hit by obstacle fireball - stun, lose stack, and lose points
                # Only lose points if not already stunned
                if player.state != "stunned":
                    score = max(0, score - 25)
                player.stun()
                obstacle_fireballs.remove(of)
            # Remove obstacle fireballs that are no longer alive
            elif not of.alive:
                obstacle_fireballs.remove(of)

        # Throw food mechanic: when player enters throwing state, launch food
        if player.state == "throwing" and player.food_stack and not player.threw_this_cycle:
            # Launch all food in stack at once
            stack_size = len(player.food_stack)
            for i, food_to_throw in enumerate(player.food_stack[:]):
                # Spread the food items horizontally so they don't overlap
                x_offset = (i - stack_size//2) * 20  # 20px spacing between items
                thrown_foods.append(ThrownFood(food_to_throw, player.x + PLAYER_WIDTH//2 - 25 + x_offset, player.y))
            
            # Clear the stack after throwing
            player.food_stack.clear()
            player.threw_this_cycle = True
            player.update_speed()

        # Update thrown food
        for tf in thrown_foods[:]:
            tf.update()
            tf.draw(WIN)
            # Check collision with customers
            tf_rect = pygame.Rect(tf.x, tf.y, tf.width, tf.height)
            hit_customer = None
            for c in customers:
                if c.hitbox.colliderect(tf_rect):
                    hit_customer = c
                    break
            if hit_customer:
                # Calculate points based on total thrown food count
                total_thrown = len(thrown_foods)
                if total_thrown == 1:
                    points = 20
                elif total_thrown == 2:
                    points = 30
                elif total_thrown == 3:
                    points = 50
                elif total_thrown == 4:
                    points = 70
                elif total_thrown >= 5:
                    points = 100
                else:
                    points = total_thrown * 20
                
                score += points
                # Remove all thrown food items and the hit customer
                thrown_foods.clear()
                customers.remove(hit_customer)
                break  # Exit the loop since we've handled the collision

            if not tf.alive:
                thrown_foods.remove(tf)

        # Draw player stack (food images above player)
        for i, food in enumerate(player.food_stack):
            img = pygame.image.load(food.path)
            # Stack food above player's head, 10px apart
            WIN.blit(pygame.transform.scale(img, (40, 40)), (player.x + PLAYER_WIDTH//2 - 20, player.y - (i + 1)*45))

        # Draw player
        WIN.blit(player.get_current_sprite(), (player.x, player.y))

        pygame.display.update()

        # Game over condition
        if time_left <= 0:
            running = False
            # Show game over screen and get player name
            show_game_over_screen(score)
            return  # Return to main menu instead of quitting

    pygame.quit()

def main_menu():
    # Load and play menu music
    try:
        pygame.mixer.music.load("silly_menu.mp3")
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    except pygame.error as e:
        print(f"Could not load menu music: {e}")
    
    while True:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        draw_text_centered(WIN, "Catch the Healthy Food", MENU_FONT, (255, 255, 255), 100)

        # Create semi-transparent black square for menu options
        menu_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 300)
        menu_surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        pygame.draw.rect(menu_surface, (0, 0, 0, 128), (0, 0, 300, 300))  # Semi-transparent black
        WIN.blit(menu_surface, menu_rect)

        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()

        # Menu options positioned within the semi-transparent square
        options = [
            ("Play", HEIGHT//2 - 20),
            ("Instructions", HEIGHT//2 + 30),
            ("About", HEIGHT//2 + 80),
            ("Leaderboard", HEIGHT//2 + 130),
            ("Quit", HEIGHT//2 + 180)
        ]

        for option_text, y_pos in options:
            text_surface = FONT.render(option_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(WIDTH//2, y_pos))
            
            # Check if mouse is hovering over this option
            if text_rect.collidepoint(mouse_pos):
                # Highlight the text when hovering
                pygame.draw.rect(WIN, (255, 255, 255, 50), text_rect.inflate(20, 10))
                if mouse_click[0]:  # Left click
                    pygame.time.delay(200)
                    if option_text == "Play":
                        run_game()
                    elif option_text == "Instructions":
                        show_instructions()
                    elif option_text == "About":
                        show_about()
                    elif option_text == "Leaderboard":
                        show_leaderboard()
                    elif option_text == "Quit":
                        pygame.quit()
                        exit()
            
            WIN.blit(text_surface, text_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()


if __name__ == "__main__":
    main_menu()

