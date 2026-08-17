import pygame
import random
import sys
import math

# Инициализация Pygame
pygame.init()

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Неси Чекушку: Физика и Осколки")

clock = pygame.time.Clock()
FPS = 60

# Цвета
NIGHT_TOP = (10, 10, 30)
NIGHT_BOTTOM = (30, 40, 70)
OBSTACLE_COLOR = (236, 240, 241)
SCORE_COLOR = (255, 255, 255)
MOON_COLOR = (255, 255, 220)

# Файлы картинок
CHEKUSKA_IMAGE = "chekuska.png"
PLAYER_IMAGE = "player.png"
FPV_DRONE_IMAGE = "fpvdron.png"
EXPLOSION_IMAGE = "explosion.png"  # Картинка взрыва

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.radius = random.uniform(1.0, 2.5)
        self.alpha = random.randint(50, 255)
        self.fade_speed = random.uniform(2, 6) * random.choice([-1, 1])

    def update(self):
        self.alpha += self.fade_speed
        if self.alpha >= 255:
            self.alpha = 255
            self.fade_speed *= -1
        elif self.alpha <= 50:
            self.alpha = 50
            self.fade_speed *= -1

    def draw(self, surface):
        color = (int(self.alpha), int(self.alpha), int(self.alpha))
        pygame.draw.circle(surface, color, (self.x, self.y), self.radius)

class Shard:
    def __init__(self, x, y, custom_color=None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-7, 7)
        self.vy = random.uniform(-10, -2)
        self.color = custom_color if custom_color else random.choice([(255, 255, 100), (200, 200, 200), (255, 255, 255), (255, 215, 0)])
        self.size = random.randint(4, 10)
        self.angle = random.randint(0, 360)
        self.rot_speed = random.uniform(-15, 15)

    def update(self):
        self.vy += 0.4
        self.x += self.vx
        self.y += self.vy
        self.angle += self.rot_speed

    def draw(self, surface):
        shard_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        shard_surf.fill(self.color)
        rotated_shard = pygame.transform.rotate(shard_surf, self.angle)
        surface.blit(rotated_shard, (self.x - rotated_shard.get_width()//2, self.y - rotated_shard.get_height()//2))

class Chekuska:
    def __init__(self):
        try:
            raw_img = pygame.image.load(CHEKUSKA_IMAGE).convert_alpha()
            orig_w, orig_h = raw_img.get_size()
            new_w = 45 
            new_h = int(orig_h * (new_w / orig_w))
            self.image = pygame.transform.smoothscale(raw_img, (new_w, new_h))
        except:
            self.image = pygame.Surface((40, 75))
            self.image.fill((255, 255, 0))
            
        self.rect = self.image.get_rect()
        self.target_y = SCREEN_HEIGHT - 120
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT + 150)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Player:
    def __init__(self):
        self.radius = 32
        try:
            raw_img = pygame.image.load(PLAYER_IMAGE).convert_alpha()
            orig_w, orig_h = raw_img.get_size()
            new_w = self.radius * 2
            new_h = int(orig_h * (new_w / orig_w))
            self.image = pygame.transform.smoothscale(raw_img, (new_w, new_h))
        except:
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 50, 50), (self.radius, self.radius), self.radius)
            
        self.pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.vel = pygame.math.Vector2(0, 0)
        self.rect = self.image.get_rect()
        self.alpha = 0
        self.visible = False

    def update(self):
        if not self.visible: return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        new_pos = pygame.math.Vector2(mouse_x, mouse_y)
        if new_pos.y > SCREEN_HEIGHT - 170:
            new_pos.y = SCREEN_HEIGHT - 170
        self.vel = new_pos - self.pos 
        self.pos = new_pos
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface):
        if self.visible:
            if self.alpha < 255:
                self.alpha += 15
                self.image.set_alpha(min(self.alpha, 255))
            surface.blit(self.image, self.rect)

class Obstacle:
    def __init__(self, x, y, radius, vx=0, vy=0):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.radius = radius
        self.mass = radius

    def draw(self, surface):
        pygame.draw.circle(surface, OBSTACLE_COLOR, (int(self.pos.x), int(self.pos.y)), self.radius)

class FPVDrone:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(random.uniform(-0.5, 0.5), 1.2)
        self.radius = 22
        self.mass = 15
        self.exploded = False
        self.explosion_timer = 12  # 12 кадров = 0.2 секунды
        
        try:
            raw_img = pygame.image.load(FPV_DRONE_IMAGE).convert_alpha()
            self.image = pygame.transform.smoothscale(raw_img, (self.radius * 2, self.radius * 2))
        except:
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 60, 0), (self.radius, self.radius), self.radius)

        try:
            self.raw_explosion_img = pygame.image.load(EXPLOSION_IMAGE).convert_alpha()
        except:
            self.raw_explosion_img = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(self.raw_explosion_img, (255, 100, 0), (30, 30), 30)

    def update(self, world_scroll_speed):
        if not self.exploded:
            self.pos += self.vel
            self.pos.y += world_scroll_speed * 0.5
        else:
            self.explosion_timer -= 1

    def draw(self, surface):
        if not self.exploded:
            surface.blit(self.image, self.image.get_rect(center=(int(self.pos.x), int(self.pos.y))))
        else:
            progress = 12 - self.explosion_timer  # от 0 до 12
            current_size = int(15 + progress * 6)
            scaled_exp = pygame.transform.smoothscale(self.raw_explosion_img, (current_size * 2, current_size * 2))
            alpha_val = max(0, 255 - int(progress * (255 / 12)))
            scaled_exp.set_alpha(alpha_val)
            surface.blit(scaled_exp, scaled_exp.get_rect(center=(int(self.pos.x), int(self.pos.y))))

def resolve_collisions(obstacles, drones, player, shards_list):
    for i in range(len(obstacles)):
        for j in range(i + 1, len(obstacles)):
            o1 = obstacles[i]
            o2 = obstacles[j]
            dist_vec = o1.pos - o2.pos
            dist = dist_vec.length()
            min_dist = o1.radius + o2.radius
            
            if 0 < dist < min_dist:
                overlap = min_dist - dist
                normal = dist_vec.normalize()
                total_mass = o1.mass + o2.mass
                
                o1.pos += normal * (overlap * (o2.mass / total_mass))
                o2.pos -= normal * (overlap * (o1.mass / total_mass))
                
                rel_vel = o1.vel - o2.vel
                if rel_vel.dot(normal) < 0:
                    restitution = 0.5
                    impulse = -(1 + restitution) * rel_vel.dot(normal) / (1/o1.mass + 1/o2.mass)
                    o1.vel += normal * (impulse / o1.mass)
                    o2.vel -= normal * (impulse / o2.mass)

    for drone in drones:
        if drone.exploded: continue
        for obs in obstacles:
            dist_vec = obs.pos - drone.pos
            dist = dist_vec.length()
            if dist < drone.radius + obs.radius:
                drone.exploded = True
                obs.vel = (obs.pos - drone.pos).normalize() * 12
                for _ in range(10):
                    shards_list.append(Shard(drone.pos.x, drone.pos.y, random.choice([(255, 140, 0), (255, 60, 0), (255, 255, 0)])))

    if player.visible:
        for obs in obstacles:
            dist_vec = obs.pos - player.pos
            dist = dist_vec.length()
            min_dist = obs.radius + player.radius
            if 0 < dist < min_dist:
                overlap = min_dist - dist
                normal = dist_vec.normalize()
                obs.pos += normal * overlap
                obs.vel = player.vel * 0.9 + normal * 4

        for drone in drones:
            if drone.exploded: continue
            dist_vec = drone.pos - player.pos
            dist = dist_vec.length()
            min_dist = drone.radius + player.radius
            if 0 < dist < min_dist:
                overlap = min_dist - dist
                normal = dist_vec.normalize()
                drone.pos += normal * overlap
                drone.vel = player.vel * 0.5 + normal * 3

def spawn_formation(y_pos):
    obstacles = []
    drones = []
    types = ['pyramid', 'block', 'side_walls', 'scatter', 'drone_wave']
    choice = random.choice(types)
    r = 15
    if choice == 'pyramid':
        for row in range(5):
            for col in range(row + 1):
                x = SCREEN_WIDTH//2 - (row * r) + (col * r * 2)
                y = y_pos - (row * r * 2.2)
                obstacles.append(Obstacle(x, y, r))
    elif choice == 'block':
        for row in range(4):
            for col in range(5):
                x = SCREEN_WIDTH//2 - 60 + (col * r * 2.1)
                y = y_pos - (row * r * 2.1)
                obstacles.append(Obstacle(x, y, r))
    elif choice == 'scatter':
        for _ in range(15):
            x = random.randint(30, SCREEN_WIDTH - 30)
            y = y_pos - random.randint(0, 150)
            obstacles.append(Obstacle(x, y, random.randint(10, 24)))
    elif choice == 'side_walls':
        for i in range(6):
            obstacles.append(Obstacle(15, y_pos - i * 35, r, vx=random.uniform(3, 7), vy=random.uniform(-0.5, 0.5)))
            obstacles.append(Obstacle(SCREEN_WIDTH - 15, y_pos - i * 35, r, vx=random.uniform(-7, -3), vy=random.uniform(-0.5, 0.5)))
    elif choice == 'drone_wave':
        drones.append(FPVDrone(SCREEN_WIDTH // 2, y_pos - 40))
        obstacles.append(Obstacle(SCREEN_WIDTH // 2 - 60, y_pos, r, vx=2, vy=-1))
        obstacles.append(Obstacle(SCREEN_WIDTH // 2 + 60, y_pos, r, vx=-2, vy=-1))
        
    return obstacles, drones

def draw_background(screen, stars):
    for y in range(SCREEN_HEIGHT):
        inter = y / SCREEN_HEIGHT
        color = (
            int(NIGHT_TOP[0] * (1 - inter) + NIGHT_BOTTOM[0] * inter),
            int(NIGHT_TOP[1] * (1 - inter) + NIGHT_BOTTOM[1] * inter),
            int(NIGHT_TOP[2] * (1 - inter) + NIGHT_BOTTOM[2] * inter)
        )
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
        
    for star in stars:
        star.update()
        star.draw(screen)

    moon_x, moon_y, moon_r = 380, 100, 45
    pygame.draw.circle(screen, MOON_COLOR, (moon_x, moon_y), moon_r)

def draw_landscape(screen, offset_y=0):
    pygame.draw.polygon(screen, (40, 50, 70), [(-50, SCREEN_HEIGHT + offset_y), (100, SCREEN_HEIGHT-250 + offset_y), (250, SCREEN_HEIGHT + offset_y)])
    pygame.draw.polygon(screen, (30, 40, 60), [(150, SCREEN_HEIGHT + offset_y), (320, SCREEN_HEIGHT-300 + offset_y), (480, SCREEN_HEIGHT + offset_y)])
    pygame.draw.polygon(screen, (50, 60, 80), [(300, SCREEN_HEIGHT + offset_y), (420, SCREEN_HEIGHT-180 + offset_y), (550, SCREEN_HEIGHT + offset_y)])
    pygame.draw.circle(screen, (15, 25, 35), (SCREEN_WIDTH // 2, SCREEN_HEIGHT + 350 + offset_y), 450)

def draw_glass_button(surface, rect, text, font, is_hovered):
    btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    alpha = 150 if is_hovered else 80
    border_alpha = 255 if is_hovered else 150
    
    pygame.draw.rect(btn_surf, (100, 180, 255, alpha), btn_surf.get_rect(), border_radius=15)
    pygame.draw.rect(btn_surf, (255, 255, 255, border_alpha), btn_surf.get_rect(), 2, border_radius=15)
        
    surface.blit(btn_surf, (rect.x, rect.y))
    
    text_surf = font.render(text, True, (255, 255, 255))
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))

def main():
    state = "MENU"
    
    chekuska = Chekuska()
    player = Player()
    obstacles = []
    drones = []
    shards = []
    stars = [Star() for _ in range(80)]
    
    score = 0
    high_score = 0
    world_scroll_speed = 3
    menu_offset_y = 0
    
    anti_afk_timer = 0
    
    btn_cx, btn_cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50
    restart_btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 80, 240, 60)

    font_main = pygame.font.SysFont("Arial", 45, bold=True)
    font_btn = pygame.font.SysFont("Arial", 28, bold=True)
    font_small = pygame.font.SysFont("Arial", 24, bold=True)

    play_temp_surf = font_main.render("ИГРАТЬ", True, (255, 255, 255))
    play_rect = play_temp_surf.get_rect(center=(btn_cx, btn_cy))

    running = True
    while running:
        draw_background(screen, stars)
        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        if state == "MENU":
            draw_landscape(screen, 0)
            
            is_hovered_play = play_rect.collidepoint(mouse_pos)
            play_color = (0, 255, 128) if is_hovered_play else (255, 255, 255)
            
            play_text = font_main.render("ИГРАТЬ", True, play_color)
            screen.blit(play_text, play_rect)
            
            title = font_main.render("НЕСИ ЧЕКУШКУ", True, (255, 255, 255))
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 130)))

            highscore_text = font_small.render(f"Твой рекорд: {high_score}", True, (255, 215, 0))
            screen.blit(highscore_text, highscore_text.get_rect(center=(SCREEN_WIDTH//2, 195)))

            if is_hovered_play and click:
                state = "STARTING"
                score = 0
                
        elif state == "STARTING":
            menu_offset_y += 5
            draw_landscape(screen, menu_offset_y)
            
            if chekuska.rect.centery > chekuska.target_y:
                chekuska.rect.centery -= 4
            else:
                player.visible = True
                pygame.mouse.set_pos((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                obstacles.clear()
                drones.clear()
                obs_init, drone_init = spawn_formation(-100)
                obstacles.extend(obs_init)
                drones.extend(drone_init)
                state = "PLAYING"
                
            chekuska.draw(screen)

        elif state == "PLAYING":
            player.update()

            anti_afk_timer += 1
            if anti_afk_timer > 100:
                anti_afk_timer = 0
                drones.append(FPVDrone(random.randint(80, SCREEN_WIDTH - 80), -40))

            for obs in obstacles:
                obs.vel *= 0.96 
                obs.pos += obs.vel
                obs.pos.y += world_scroll_speed
                
                if obs.pos.x < obs.radius:
                    obs.pos.x = obs.radius
                    obs.vel.x *= -0.5
                elif obs.pos.x > SCREEN_WIDTH - obs.radius:
                    obs.pos.x = SCREEN_WIDTH - obs.radius
                    obs.vel.x *= -0.5

            for drone in drones:
                drone.update(world_scroll_speed)

            resolve_collisions(obstacles, drones, player, shards)

            obstacles = [obs for obs in obstacles if obs.pos.y < SCREEN_HEIGHT + 100]
            drones = [drone for drone in drones if drone.pos.y < SCREEN_HEIGHT + 100 and drone.explosion_timer > 0]
            
            highest_y = SCREEN_HEIGHT
            for obs in obstacles:
                if obs.pos.y < highest_y:
                    highest_y = obs.pos.y
            for drone in drones:
                if drone.pos.y < highest_y and not drone.exploded:
                    highest_y = drone.pos.y
                    
            if highest_y > 100:
                new_obs, new_drones = spawn_formation(-150)
                obstacles.extend(new_obs)
                drones.extend(new_drones)
                score += 1
                if score > high_score:
                    high_score = score

            hitbox = chekuska.rect.inflate(-15, -15)
            for obs in obstacles:
                if hitbox.collidepoint(obs.pos.x, obs.pos.y):
                    shards = [Shard(chekuska.rect.centerx, chekuska.rect.centery) for _ in range(40)]
                    state = "GAMEOVER"
            
            for drone in drones:
                if not drone.exploded and hitbox.collidepoint(drone.pos.x, drone.pos.y):
                    drone.exploded = True
                    shards = [Shard(chekuska.rect.centerx, chekuska.rect.centery) for _ in range(40)]
                    state = "GAMEOVER"

            for obs in obstacles:
                obs.draw(screen)
            for drone in drones:
                drone.draw(screen)
                
            chekuska.draw(screen)
            player.draw(screen)

            score_surf = font_main.render(f"{score}", True, SCORE_COLOR)
            screen.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, 50)))

        elif state == "GAMEOVER":
            for obs in obstacles:
                obs.draw(screen)
            for drone in drones:
                drone.update(world_scroll_speed)
                drone.draw(screen)
            
            for shard in shards:
                shard.update()
                shard.draw(screen)
                
            player.draw(screen)
            
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            over_text = pygame.font.SysFont("Arial", 50, bold=True).render("ПРОИГРЫШ", True, (255, 80, 80))
            score_text = font_btn.render(f"Счёт: {score}", True, (255, 255, 255))
            record_text = font_small.render(f"Рекорд: {high_score}", True, (255, 215, 0))
            
            screen.blit(over_text, over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80)))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 25)))
            screen.blit(record_text, record_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 15)))
            
            is_hovered = restart_btn_rect.collidepoint(mouse_pos)
            draw_glass_button(screen, restart_btn_rect, "Начать заново?", font_btn, is_hovered)
            
            if is_hovered and click:
                chekuska.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT + 150)
                player.visible = False
                player.alpha = 0
                menu_offset_y = 0
                anti_afk_timer = 0
                state = "STARTING"
                score = 0

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()