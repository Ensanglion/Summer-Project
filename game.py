import pygame
import random
import csv
from classes import *
from PIL import Image

# General game setup -----------------------------------------------------------

pygame.init()
pygame.mixer.init()  # enables sound

screen_info = pygame.display.Info() # player's screen size
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Catch the Healthy Food")

FPS = 60
FONT = pygame.font.SysFont("arial", 24)
HUD_FONT = pygame.font.SysFont("arial", 48)
MENU_FONT = pygame.font.SysFont("arial", 64)


# Load images
BACKGROUND_IMG = pygame.image.load("new_sprites\\spr_chefs_BG\\spr_chefs_BG_0.png")
BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (WIDTH, HEIGHT))

def load_and_scale_sprite(path, target_width, target_height):
    """Load a sprite and scale it to fit within target dimensions while maintaining aspect ratio"""
    original = pygame.image.load(path)
    orig_width, orig_height = original.get_size()
    
    scale_x = target_width / orig_width
    scale_y = target_height / orig_height
    scale = min(scale_x, scale_y)
    
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)
    
    # scale the sprite
    scaled = pygame.transform.scale(original, (new_width, new_height))
    
    # create a new surface with target dimensions and transparent background
    final_surface = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
    
    # center the scaled sprite on the final surface
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

# Customer sprites
CUSTOMER_SPRITES = [
    load_and_scale_sprite("new_sprites\\spr_shadowman_run3\\spr_shadowman_run3_1.png", 100, 120),
    load_and_scale_sprite("new_sprites\\spr_shadowman_run3\\spr_shadowman_run3_0.png", 100, 120),
]

# Fireball sprite and dimnensions
FIREBALL_SPRITE = load_and_scale_sprite(
    "new_sprites\\spr_kitchen_fire_ball\\spr_kitchen_fire_ball_1.png",
    40, 40
)

# Food warning sprite and dimensions
FOOD_WARNING_SPRITE = pygame.transform.scale(
    pygame.image.load("new_sprites\\spr_chefs_foodnotice\\spr_chefs_foodnotice_0.png"),
    (50, 50) 
)

# scoreboard sprite and dimensions
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

# ensures the text is centered on the screen
def draw_text_centered(win, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    win.blit(rendered, rect)

# literally just creates a button
def draw_button(win, text, font, color, hover_color, rect, mouse_pos, mouse_click):
    is_hovered = rect.collidepoint(mouse_pos)
    pygame.draw.rect(win, hover_color if is_hovered else color, rect, border_radius=12)
    label = font.render(text, True, (255, 255, 255))
    label_rect = label.get_rect(center=rect.center)
    win.blit(label, label_rect)
    return is_hovered and mouse_click[0]
 

# Helper Classes -----------------------------------------------------------

class GIFAnimation:
    def __init__(self, gif_path, target_width, target_height):
        self.frames = []
        self.current_frame = 0
        self.frame_delay = 12  # milliseconds between frames (20 FPS)
        self.last_frame_time = 0
        
        try:
            # open the gif and extract frames
            gif = Image.open(gif_path)
            frame_count = 0
            
            while True:
                # convert PIL image to pygame surface
                frame_surface = pygame.image.fromstring(gif.convert('RGBA').tobytes(), gif.size, 'RGBA')
                
                # scale the frame to target size
                scaled_frame = pygame.transform.scale(frame_surface, (target_width, target_height))
                self.frames.append(scaled_frame)
                
                frame_count += 1
                gif.seek(frame_count)
        except EOFError:
            pass  # end of gif
        except Exception as e:
            print(f"Error loading GIF {gif_path}: {e}")
            # create a fallback surface
            fallback = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 255))
            self.frames.append(fallback)
    
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_frame_time > self.frame_delay and len(self.frames) > 1:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = now
    
    def get_current_frame(self):
        if self.frames:
            return self.frames[self.current_frame]
        return None

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

    # switches between sprites based on the player's state
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
        # slightly below player ground line
        self.y = GROUND_Y + 200  
        # spawn off-screen
        self.x = WIDTH + 50  
        self.speed = 3
        self.sprite_index = 0
        self.last_sprite_switch = pygame.time.get_ticks()
        self.width = 100
        self.height = 120
        self.hitbox = pygame.Rect(self.x, self.y, self.width, self.height)
        self.alive = True

    # moves the customer to the left and switches between sprites
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

# fireball class (only for the ones that are created when food hits the ground) because something didn't work when there was just one class
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

# obstacle fireball class (only for the ones that are moving from side to side)
class ObstacleFireball:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 3
        self.direction = direction  # randomly chooses either "left" or "right"
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

# thrown food logic 
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
# instructions screen 
def show_instructions():
    # Load cabbage dance GIFs (left and right)
    cabbage_gif_left = GIFAnimation("new_sprites\\spr_tenna_dance_cabbage.gif", 300, 300)
    cabbage_gif_right = GIFAnimation("new_sprites\\spr_tenna_dance_cabbage.gif", 300, 300)
    
    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        # Update and draw cabbage dance GIFs (left and right)
        cabbage_gif_left.update()
        cabbage_gif_right.update()
        cabbage_frame_left = cabbage_gif_left.get_current_frame()
        cabbage_frame_right = cabbage_gif_right.get_current_frame()
        if cabbage_frame_left:
            WIN.blit(cabbage_frame_left, (100, HEIGHT//2 - 150))  # Left side of screen
        if cabbage_frame_right:
            WIN.blit(cabbage_frame_right, (WIDTH - 400, HEIGHT//2 - 150))  # Right side of screen
        
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
# about screen 
def show_about():
    try: 
        plot_img = pygame.image.load("data_plot_high_res.png")
        plot_img = pygame.transform.scale(plot_img, (800, 600))
    except pygame.error as e: # debug print
        print(f"Could not load data plot: {e}")
        plot_img = None
    
    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        draw_text_centered(WIN, "About", MENU_FONT, (255, 255, 255), 80)
        
        if plot_img:
            plot_rect = plot_img.get_rect(center=(WIDTH * 0.7, HEIGHT * 0.55))
            WIN.blit(plot_img, plot_rect)
        
        left_text_x = WIDTH * 0.25  
        
        # helper function to draw text on the left side
        def draw_left_text(text, font, color, y):
            rendered = font.render(text, True, color)
            WIN.blit(rendered, (left_text_x - rendered.get_width()//2, y))
        
        def draw_left_text_bold(text, font, color, y):
            bold_font = pygame.font.SysFont("arial", 24, bold=True)
            rendered = bold_font.render(text, True, color)
            WIN.blit(rendered, (left_text_x - rendered.get_width()//2, y))
        
        # Text content on the left
        first_line_x = WIDTH * 0.45  # first line is further to the right to align with the image better
        last_lines_x = WIDTH * 0.225 # last lines closer to the left side
        first_line_text = "The game has different kinds of food with random calories assigned. Using a dataset of foods, we found a linear relation:"
        first_line_rendered = FONT.render(first_line_text, True, (0, 0, 0))
        WIN.blit(first_line_rendered, (first_line_x - first_line_rendered.get_width()//2, 150))
        draw_left_text("", FONT, (0, 0, 0), 180)  # Spacing
        draw_left_text("Linear relation equation:", FONT, (0, 0, 0), 210)
        draw_left_text("Total Fat (g) = 0.0448 × Energy (kCal) - 2.1217", FONT, (0, 0, 0), 240)
        draw_left_text("", FONT, (0, 0, 0), 270)  # Spacing
        draw_left_text("Healthy food is defined as food with less than 20g of fat.", FONT, (0, 0, 0), 300)    
        # last 2 lines are bolded and closer to the left side, split around "and" to avoid background
        last_line1_part1 = "Your goal is to catch healthy food,"
        last_line1_part2 = "then throw it at the customers"
        last_line2_text = "Avoid unhealthy food and fireballs!"   
             
        part1_1 = pygame.font.SysFont("arial", 24, bold=True).render(last_line1_part1, True, (0, 0, 0))
        part1_2 = pygame.font.SysFont("arial", 24, bold=True).render(last_line1_part2, True, (0, 0, 0))
        last_line2_rendered = pygame.font.SysFont("arial", 24, bold=True).render(last_line2_text, True, (0, 0, 0))

        WIN.blit(part1_1, (last_lines_x - part1_1.get_width()//2 - 160, 570))  
        WIN.blit(part1_2, (last_lines_x - part1_2.get_width()//2 + 190, 570)) 
        WIN.blit(last_line2_rendered, (last_lines_x - last_line2_rendered.get_width()//2, 605))  
        
        draw_text_centered(WIN, "ESC to return", FONT, (200, 200, 200), 850)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

# game end screen where the player enters their name to save their score to the leaderboard
def show_game_over_screen(final_score):
    player_name = ""
    input_active = True
    
    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 128), (0, 0, WIDTH, HEIGHT))
        WIN.blit(overlay, (0, 0))
        
        draw_text_centered(WIN, "GAME OVER", MENU_FONT, (255, 255, 255), 200)
        
        draw_text_centered(WIN, f"Your Score: {final_score}", HUD_FONT, (255, 255, 255), 300) # final score
        
        draw_text_centered(WIN, "Enter your name:", FONT, (255, 255, 255), 400)
        
        input_rect = pygame.Rect(WIDTH//2 - 150, 430, 300, 40) # input box
        pygame.draw.rect(WIN, (255, 255, 255), input_rect, 2)
        pygame.draw.rect(WIN, (50, 50, 50), input_rect)
        
        # player input text
        name_surface = FONT.render(player_name, True, (255, 255, 255))
        WIN.blit(name_surface, (input_rect.x + 10, input_rect.y + 10))
        
        draw_text_centered(WIN, "Press ENTER to save score", FONT, (200, 200, 200), 500)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    save_score_to_leaderboard(player_name.strip(), final_score)
                    running = False
                    # Change music back to menu theme
                    try:
                        pygame.mixer.music.load("silly_menu.mp3")
                        pygame.mixer.music.play(-1)
                    except pygame.error as e:
                        print(f"Could not load menu music: {e}")
                    return  # Return to main menu instead of quitting
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode.isprintable() and len(player_name) < 20:
                    player_name += event.unicode

# saves the player's name and score to the leaderboard
def save_score_to_leaderboard(name, score):
    try:
        scores = []
        try:
            with open("leaderboard.csv", newline='', mode='r') as file:
                reader = csv.reader(file)
                # Skip header row 
                header = next(reader, None)
                if header and header[0] == "Name":
                    
                    scores = list(reader)
                else: # for debug purposes, in case the file doesn't have a header
                    if header:
                        scores = [header]
                    scores.extend(list(reader))
        except FileNotFoundError:
            pass
        
        # Add new score
        scores.append([name, str(score)])
        
        # Sort by score (descending) and keep top 5
        scores.sort(key=lambda row: int(row[1]), reverse=True) # Assaf learned what a lambda function is!!!
        scores = scores[:5]
        
        with open("leaderboard.csv", newline='', mode='w') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Score"]) 
            writer.writerows(scores)
            
    except Exception as e:
        print(f"Error saving score: {e}")

# leaderboard screen
def show_leaderboard():
    scores = []
    try:
        with open("leaderboard.csv", newline='') as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header and header[0] == "Name":
                scores = list(reader)
            else:
                if header:
                    scores = [header]
                scores.extend(list(reader))
    except FileNotFoundError:
        pass

    # Load cane dance GIFs (left and right)
    cane_gif_left = GIFAnimation("new_sprites\\spr_tenna_dance_cane.gif", 300, 300)
    cane_gif_right = GIFAnimation("new_sprites\\spr_tenna_dance_cane.gif", 300, 300)

    running = True
    while running:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        # Update and draw cane dance GIFs (left and right)
        cane_gif_left.update()
        cane_gif_right.update()
        cane_frame_left = cane_gif_left.get_current_frame()
        cane_frame_right = cane_gif_right.get_current_frame()
        if cane_frame_left:
            WIN.blit(cane_frame_left, (100, HEIGHT//2 - 150))  # Left side of screen
        if cane_frame_right:
            WIN.blit(cane_frame_right, (WIDTH - 400, HEIGHT//2 - 150))  # Right side of screen
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

# actual game loop
def run_game():
    clock = pygame.time.Clock()
    try:
        pygame.mixer.music.load("game_active.mp3")
        pygame.mixer.music.play(-1) 
    except pygame.error as e: # debug print
        print(f"Could not load music: {e}")

    player = Player()
    score = 0
    timer = 90 
    start_time = pygame.time.get_ticks()

    current_food = None
    food_img = None
    food_x = 0
    food_y = 0
    food_speed = 4
    food_spawn_time = 0
    food_warning_visible = False
    food_warning_x = 0  # track warning x position (used to spawn food later)
    obstacle_warning_visible = False
    obstacle_warning_side = "left" 
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

        WIN.blit(BACKGROUND_IMG, (0, 0))

        hud_x = WIDTH // 2 - 225  
        hud_y = 120  
        scaled_hud = pygame.transform.scale(SCOREBOARD_SPRITE, (450, 220))
        WIN.blit(scaled_hud, (hud_x, hud_y))

        score_label = HUD_FONT.render("SCORE:", True, (255, 255, 255)) 
        score_value = HUD_FONT.render(str(score), True, (255, 255, 255)) 
        
        label_x = hud_x + (450 - score_label.get_width()) // 2
        label_y = hud_y + 60 
        value_x = hud_x + (450 - score_value.get_width()) // 2
        value_y = hud_y + 120 
        
        WIN.blit(score_label, (label_x, label_y))
        WIN.blit(score_value, (value_x, value_y))

        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # update player stun timer
        player.update_stun()

        # player actions
        player.move(keys)
        player.apply_gravity()
        player.update_speed()
        player.update_throw()

        # update timer
        elapsed_time = (now - start_time) // 1000
        time_left = max(0, timer - elapsed_time)
        
        timer_text = HUD_FONT.render(f"TIME: {time_left}", True, (255, 255, 255)) 
        timer_x = hud_x + 20 
        timer_y = hud_y + 20 
        WIN.blit(timer_text, (timer_x, timer_y))

        # throw food if Z pressed
        if keys[pygame.K_z]:
            player.start_throw()

        # spawn food logic with warning sprite
        if current_food is None:
            if not food_warning_visible:
                # set warning position first, then show warning
                food_warning_x = random.randint(0, WIDTH - 50) 
                food_warning_visible = True
                food_spawn_time = now + 1000  # warning visible for 1 sec
            else:
                if now >= food_spawn_time:
                    current_food = Food(path=None, calories=None)
                    food_x = food_warning_x  # use the same x position as warning
                    food_y = -50
                    food_warning_visible = False
        else:
            # move food down
            food_y += food_speed

            # check catch
            food_rect = pygame.Rect(food_x, food_y, 50, 50)
            player_rect = pygame.Rect(player.x, player.y, PLAYER_WIDTH, PLAYER_HEIGHT)
            if food_rect.colliderect(player_rect) and player.state == "normal":
                # add to stack if healthy
                if current_food.is_healthy:
                    if len(player.food_stack) < MAX_FOOD_STACK:
                        player.food_stack.append(current_food)
                        player.update_speed()
                    else:
                        # stack full, food missed (turn into fireball)
                        fireballs.append(Fireball(food_x, GROUND_Y + 40, "left", is_obstacle=False))
                else:   
                    # bad food hit player -> lose stack + stun
                    # only lose points if not already stunned
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
                        x_pos = -40  # spawn off left edge
                        direction = "right"  # move right
                    else:
                        x_pos = WIDTH  # spawn off right edge  
                        direction = "left"  # move left
                    obstacle_fireballs.append(ObstacleFireball(x_pos, y_pos, direction))
                    print(f"Spawned obstacle fireball at ({x_pos}, {y_pos}) moving {direction}")  # Debug
                    obstacle_warning_visible = False
                    last_fireball_spawn = now

        # update fireballs
        for f in fireballs[:]:
            f.update()
            f.draw(WIN)
            # check collision with player
            player_rect = pygame.Rect(player.x, player.y, PLAYER_WIDTH, PLAYER_HEIGHT)
            if f.hitbox.colliderect(player_rect):
                # Player hit by fireball - stun, lose stack, and lose points
                # Only lose points if not already stunned
                if player.state != "stunned":
                    score = max(0, score - 25)
                player.stun()
                fireballs.remove(f)
            elif not f.alive:
                fireballs.remove(f)

        # update obstacle fireballs
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
            elif not of.alive:
                obstacle_fireballs.remove(of)

        if player.state == "throwing" and player.food_stack and not player.threw_this_cycle:
            # Launch all food in stack at once
            stack_size = len(player.food_stack)
            for i, food_to_throw in enumerate(player.food_stack[:]):
                # Spread the food items horizontally so they don't overlap (also makes hitting customers easier)
                x_offset = (i - stack_size//2) * 20 
                thrown_foods.append(ThrownFood(food_to_throw, player.x + PLAYER_WIDTH//2 - 25 + x_offset, player.y))
            
            # Clear the stack after throwing
            player.food_stack.clear()
            player.threw_this_cycle = True
            player.update_speed()

        # Update thrown food
        for tf in thrown_foods[:]:
            tf.update()
            tf.draw(WIN)
            tf_rect = pygame.Rect(tf.x, tf.y, tf.width, tf.height)
            hit_customer = None
            for c in customers:
                if c.hitbox.colliderect(tf_rect):
                    hit_customer = c
                    break
            if hit_customer:
                # calculate points based on total thrown food count
                total_thrown = len(thrown_foods)
                if total_thrown == 1:
                    points = 10
                elif total_thrown == 2:
                    points = 30
                elif total_thrown == 3:
                    points = 50
                elif total_thrown == 4:
                    points = 75
                elif total_thrown >= 5:
                    points = 100
                else:
                    points = total_thrown * 20
                
                score += points
                # remove all thrown food items and the hit customer
                thrown_foods.clear()
                customers.remove(hit_customer)
                break 

            if not tf.alive:
                thrown_foods.remove(tf)

        for i, food in enumerate(player.food_stack):
            img = pygame.image.load(food.path)
            WIN.blit(pygame.transform.scale(img, (40, 40)), (player.x + PLAYER_WIDTH//2 - 20, player.y - (i + 1)*45))

        # Draw player
        WIN.blit(player.get_current_sprite(), (player.x, player.y))

        pygame.display.update()

        # Game over condition
        if time_left <= 0:
            running = False
            # show game over screen and get player name
            show_game_over_screen(score)
            return  # return to main menu instead of quitting

    pygame.quit()

def main_menu():
    try:
        pygame.mixer.music.load("silly_menu.mp3")
        pygame.mixer.music.play(-1) 
    except pygame.error as e:
        print(f"Could not load menu music: {e}")
    
    cabbage_gif_left = GIFAnimation("new_sprites\\spr_tenna_dance_cabbage.gif", 300, 300)
    cabbage_gif_right = GIFAnimation("new_sprites\\spr_tenna_dance_cabbage.gif", 300, 300)
    
    while True:
        WIN.blit(BACKGROUND_IMG, (0, 0))
        
        cabbage_gif_left.update()
        cabbage_gif_right.update()
        cabbage_frame_left = cabbage_gif_left.get_current_frame()
        cabbage_frame_right = cabbage_gif_right.get_current_frame()
        if cabbage_frame_left:
            WIN.blit(cabbage_frame_left, (100, HEIGHT//2 - 150)) 
        if cabbage_frame_right:
            WIN.blit(cabbage_frame_right, (WIDTH - 400, HEIGHT//2 - 150))  
        
        draw_text_centered(WIN, "Deltarune if it was peak", MENU_FONT, (255, 255, 255), 100)

        menu_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 300)
        menu_surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        pygame.draw.rect(menu_surface, (0, 0, 0, 128), (0, 0, 300, 300)) 
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