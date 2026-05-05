import pygame
import os
import sys
import time
import random


# Temporary fix for script and bundled executable
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)


pygame.font.init()
pygame.mixer.init()




WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Pirates")

# Colors
color_WHITE = (255, 255, 255)
color_BLACK = (0, 0, 0)
color_RED = (255, 0, 0)
color_BLUE = (0, 0, 255)
color_YELLOW = (255, 255, 0)
color_GREEN = (0, 255, 0)

# Spaceships SPrites
BLUE_SPACESHIP = pygame.image.load(resource_path(os.path.join('assets', 'pixel_ship_blue_small.png')))
GREEN_SPACESHIP = pygame.image.load(resource_path(os.path.join('assets', 'pixel_ship_green_small.png')))
RED_SPACESHIP = pygame.image.load(resource_path(os.path.join('assets', 'pixel_ship_red_small.png')))
YELLOW_SPACESHIP = pygame.image.load(resource_path(os.path.join('assets', 'pixel_ship_yellow.png')))

# Laser Sprites
BLUE_LASER = pygame.image.load(resource_path(os.path.join('assets', 'pixel_laser_blue.png')))
GREEN_LASER = pygame.image.load(resource_path(os.path.join('assets', 'pixel_laser_green.png')))
RED_LASER = pygame.image.load(resource_path(os.path.join('assets', 'pixel_laser_red.png')))
YELLOW_LASER = pygame.image.load(resource_path(os.path.join('assets', 'pixel_laser_yellow.png')))

# Background Image
BACKGROUND_IMG = pygame.transform.scale(pygame.image.load(resource_path(os.path.join('assets', 'space.png'))), (WIDTH, HEIGHT))

# SOUNDS
BULLET_HIT_SOUND = pygame.mixer.Sound(resource_path(os.path.join('assets', 'Grenade+1.mp3')))
BULLET_FIRE_SOUND = pygame.mixer.Sound(resource_path(os.path.join('assets', 'Gun+Silencer.mp3')))
pygame.mixer.music.load(resource_path(os.path.join('assets', 'background_music.mp3')))
pygame.mixer.music.set_volume(0.3) 

FRAMESPERSEC = 60


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, object):
        return collide(object, self)

class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cooldown_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def laser_movement(self, velocity, object):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(object):
                object.health -= 10
                self.lasers.remove(laser)
                BULLET_HIT_SOUND.play()


    def cooldown(self):
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1

    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1
            BULLET_FIRE_SOUND.play()

    def get_width(self):
        return self.ship_img.get_width()
    
    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACESHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def laser_movement(self, velocity, objects):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else: 
                for object in objects:
                    if laser.collision(object):
                        objects.remove(object)
                        self.lasers.remove(laser)
                        BULLET_HIT_SOUND.play()
                        break

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, color_RED, (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, color_GREEN, (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health / self.max_health), 10))

class EnemyShip(Ship):
    COLOR_MAP = {
        "blue": (BLUE_SPACESHIP, BLUE_LASER), 
        "green": (GREEN_SPACESHIP, GREEN_LASER),
        "red": (RED_SPACESHIP, RED_LASER),
    }
    
    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, velocity):
        self.y += velocity

    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x - 25, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1
            BULLET_FIRE_SOUND.play()


def collide(object1, object2):
    offset_x = int(object2.x - object1.x)
    offset_y = int(object2.y - object1.y)
    return object1.mask.overlap(object2.mask, (offset_x, offset_y)) != None

def main():
    run = True
    level = 0
    lives = 5
    main_font = pygame.font.SysFont("Bookman Old Style", 50)
    lost_player_font = pygame.font.SysFont("Courier", 60)

    enemies = []
    wave_length = 5
    fire_chance = 240
    enemy_velocity = 1
    laser_velocity = 4
    PLAYER_VELOCITY = 5


    player = Player(300, 630)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window():
        WIN.blit(BACKGROUND_IMG, (0,0))
        # Drawing text
        lives_label = main_font.render(f"Lives: {lives}", 1, color_WHITE)
        level_label = main_font.render(f"Level: {level}", 1, color_WHITE)

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

        for enemy in enemies:
            enemy.draw(WIN)
            
        player.draw(WIN)

        if lost:
            lost_label= lost_player_font.render("You Lost!", 1, color_WHITE)
            WIN.blit(lost_label, (WIDTH//2 - lost_label.get_width()//2, 350))

        pygame.display.update()

    while run:
        clock.tick(FRAMESPERSEC)
        redraw_window()


        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FRAMESPERSEC * 5:
                run = False
            else:
                continue


        if len(enemies) == 0:
            level += 1
            wave_length += 2

            if level % 3 == 0:
                enemy_velocity += 1

            laser_velocity += 0.5

            if fire_chance > 60:
                fire_chance -= 20

            spawn_height = -1500 - (wave_length * 50)

            for i in range(wave_length):
                enemy = EnemyShip(random.randrange(50, WIDTH-100), random.randrange(spawn_height, -100), random.choice(["blue", "green", "red"]))
                enemies.append(enemy)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x - PLAYER_VELOCITY > 0:
            player.x -= PLAYER_VELOCITY
        if keys[pygame.K_d] and player.x + PLAYER_VELOCITY + player.get_width() < WIDTH:
            player.x += PLAYER_VELOCITY
        if keys[pygame.K_w] and player.y - PLAYER_VELOCITY > 0:
            player.y -= PLAYER_VELOCITY
        if keys[pygame.K_s] and player.y + PLAYER_VELOCITY + player.get_height() + 15 < HEIGHT:
            player.y += PLAYER_VELOCITY
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_velocity)
            enemy.laser_movement(laser_velocity, player)

            if enemy.y >= 0 and random.randrange(0, int(fire_chance)) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
                BULLET_HIT_SOUND.play()
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)


        player.laser_movement( - laser_velocity, enemies)


def main_menu():
    title_font = pygame.font.SysFont("Courier", 70)
    subtitle_font = pygame.font.SysFont("Verdana", 30)
    clock = pygame.time.Clock()
    run = True
    excluded_keys = (pygame.K_PRINTSCREEN, pygame.K_NUMLOCK, pygame.K_SCROLLOCK, pygame.K_ESCAPE, pygame.K_LSUPER, pygame.K_RSUPER, pygame.K_LSHIFT, pygame.K_RSHIFT)
    while run:
        clock.tick(FRAMESPERSEC)
        WIN.blit(BACKGROUND_IMG, (0, 0))
        title_label = title_font.render("Space Pirates", 1, color_WHITE)
        subtitle_label = subtitle_font.render("Press the mouse or any keys to begin...", 1, color_WHITE)
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 200))
        WIN.blit(subtitle_label, (WIDTH/2 - subtitle_label.get_width()/2, 400))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key not in excluded_keys):
                main()
    pygame.quit()
    sys.exit()

pygame.mixer.music.play(-1)

main_menu()         