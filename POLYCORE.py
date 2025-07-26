import pygame
import math
import random
import json
import os
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
PLAYER_SIZE = 12
PLAYER_SPEED = 5
DASH_SPEED = 100
DASH_COOLDOWN = 1000  # milliseconds
FOCUS_COOLDOWN = 10000  # 10 seconds
PULSE_COOLDOWN = 3000  # 3 seconds
SHRINK_DURATION = 2000  # 2 seconds
SHRINK_COOLDOWN = 8000  # 8 seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 100, 100)
BLUE = (100, 150, 255)
GREEN = (100, 255, 150)
YELLOW = (255, 255, 100)
PURPLE = (200, 100, 255)
ORANGE = (255, 150, 100)
CYAN = (100, 255, 255)
PINK = (255, 150, 200)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

class ShapeType(Enum):
    # 2D Basic Shapes
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    SQUARE = "square"
    PENTAGON = "pentagon"
    HEXAGON = "hexagon"
    OCTAGON = "octagon"
    STAR = "star"
    DIAMOND = "diamond"
    ELLIPSE = "ellipse"
    CROSS = "cross"
    
    # 2D Complex Shapes
    ARROW = "arrow"
    HEART = "heart"
    CRESCENT = "crescent"
    SPIRAL = "spiral"
    LIGHTNING = "lightning"
    BOWTIE = "bowtie"
    HOURGLASS = "hourglass"
    FLOWER = "flower"
    GEAR = "gear"
    SNOWFLAKE = "snowflake"
    
    # Pseudo-3D Shapes (rendered in 2D with depth illusion)
    CUBE = "cube"
    PYRAMID = "pyramid"
    CYLINDER = "cylinder"
    CONE = "cone"
    SPHERE = "sphere"
    TORUS = "torus"
    PRISM = "prism"
    DODECAHEDRON = "dodecahedron"
    ICOSAHEDRON = "icosahedron"
    TETRAHEDRON = "tetrahedron"
    
    # 4D Projections (tesseract projections, hypersphere slices)
    TESSERACT = "tesseract"
    HYPERSPHERE = "hypersphere"
    HYPERPRISM = "hyperprism"
    SIMPLEX_4D = "simplex_4d"

@dataclass
class Enemy:
    x: float
    y: float
    vx: float
    vy: float
    shape_type: ShapeType
    size: float
    color: Tuple[int, int, int]
    rotation: float = 0
    rotation_speed: float = 0
    pulse_phase: float = 0
    dimension_phase: float = 0

class Pattern(Enum):
    RANDOM = "random"
    SPIRAL = "spiral"
    WAVE = "wave"
    CIRCLE = "circle"
    ZIGZAG = "zigzag"
    CROSS = "cross"
    BURST = "burst"
    ORBIT = "orbit"

class GameState:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("POLYCORE")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Music system
        self.music_enabled = True
        self.music_volume = 0.3
        self.current_music = None
        self.load_music()
        
        # Game state
        self.running = True
        self.game_active = False
        self.paused = False
        
        # Player
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2
        self.player_size = PLAYER_SIZE
        self.is_shrunk = False
        
        # Abilities
        self.last_dash = 0
        self.last_focus = 0
        self.last_pulse = 0
        self.last_shrink = 0
        self.focus_active = False
        self.focus_end_time = 0
        self.shrink_end_time = 0
        self.pulse_uses = 5
        
        # Game mechanics
        self.enemies: List[Enemy] = []
        self.score = 0
        self.start_time = 0
        self.high_score = self.load_high_score()
        self.difficulty_multiplier = 1.0
        self.spawn_timer = 0
        self.pattern_timer = 0
        self.current_pattern = Pattern.RANDOM
        
        # Visual effects
        self.screen_shake = 0
        self.particles = []
        self.trail_points = []
        
        # Start menu music
        self.play_music('menu')

    def load_high_score(self) -> float:
        try:
            if os.path.exists("polycore_score.json"):
                with open("polycore_score.json", "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0.0)
        except:
            pass
        return 0.0

    def save_high_score(self):
        try:
            with open("polycore_score.json", "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except:
            pass
    
    def load_music(self):
        """Load music files if they exist"""
        self.music_files = {
            'menu': None,
            'gameplay': None,
            'gameover': None
        }
        
        # Try to load music files
        music_paths = {
            'menu': ['music/menu_theme.ogg', 'music/menu_theme.mp3'],
            'gameplay': ['music/gameplay_theme.ogg', 'music/gameplay_theme.mp3'],
            'gameover': ['music/gameover_theme.ogg', 'music/gameover_theme.mp3']
        }
        
        for music_type, paths in music_paths.items():
            for path in paths:
                if os.path.exists(path):
                    self.music_files[music_type] = path
                    break
    
    def play_music(self, music_type, loop=-1):
        """Play background music"""
        if not self.music_enabled or not self.music_files.get(music_type):
            return
        
        try:
            if self.current_music != music_type:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.music_files[music_type])
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
                self.current_music = music_type
        except pygame.error:
            pass  # Music file not found or invalid
    
    def stop_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        self.current_music = None
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
        else:
            # Resume appropriate music based on game state
            if not self.game_active:
                self.play_music('menu')
            else:
                self.play_music('gameplay')
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def reset_game(self):
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2
        self.player_size = PLAYER_SIZE
        self.enemies.clear()
        self.particles.clear()
        self.trail_points.clear()
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.difficulty_multiplier = 1.0
        self.spawn_timer = 0
        self.pattern_timer = 0
        self.current_pattern = Pattern.RANDOM
        self.last_dash = 0
        self.last_focus = 0
        self.last_pulse = 0
        self.last_shrink = 0
        self.focus_active = False
        self.is_shrunk = False
        self.pulse_uses = 5
        self.screen_shake = 0
        
        # Start gameplay music
        self.play_music('gameplay')

    def handle_input(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        
        # Movement
        speed = PLAYER_SPEED
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if current_time - self.last_dash > DASH_COOLDOWN:
                speed = DASH_SPEED
                self.last_dash = current_time
                self.screen_shake = 5
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_x = max(self.player_size, self.player_x - speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_x = min(SCREEN_WIDTH - self.player_size, self.player_x + speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player_y = max(self.player_size, self.player_y - speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player_y = min(SCREEN_HEIGHT - self.player_size, self.player_y + speed)
        
        # Add trail effect
        self.trail_points.append((self.player_x, self.player_y, current_time))
        self.trail_points = [p for p in self.trail_points if current_time - p[2] < 200]

    def handle_abilities(self, event):
        current_time = pygame.time.get_ticks()
        
        if event.type == pygame.KEYDOWN:
            # Focus Mode
            if event.key == pygame.K_SPACE:
                if current_time - self.last_focus > FOCUS_COOLDOWN:
                    self.focus_active = True
                    self.focus_end_time = current_time + 3000  # 3 seconds
                    self.last_focus = current_time
            
            # Pulse
            elif event.key == pygame.K_e:
                if self.pulse_uses > 0 and current_time - self.last_pulse > PULSE_COOLDOWN:
                    self.pulse_enemies()
                    self.pulse_uses -= 1
                    self.last_pulse = current_time
                    self.screen_shake = 10
            
            # Shrink
            elif event.key == pygame.K_q:
                if not self.is_shrunk and current_time - self.last_shrink > SHRINK_COOLDOWN:
                    self.is_shrunk = True
                    self.shrink_end_time = current_time + SHRINK_DURATION
                    self.last_shrink = current_time
                    self.player_size = PLAYER_SIZE // 2

    def pulse_enemies(self):
        for enemy in self.enemies:
            dx = enemy.x - self.player_x
            dy = enemy.y - self.player_y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < 150:  # Pulse range
                if distance > 0:
                    force = 200 / distance
                    enemy.vx += (dx / distance) * force
                    enemy.vy += (dy / distance) * force
                # Add particle effect
                for _ in range(5):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2, 6)
                    self.particles.append({
                        'x': enemy.x,
                        'y': enemy.y,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'life': 30,
                        'color': CYAN
                    })

    def update_abilities(self):
        current_time = pygame.time.get_ticks()
        
        # Update focus mode
        if self.focus_active and current_time > self.focus_end_time:
            self.focus_active = False
        
        # Update shrink
        if self.is_shrunk and current_time > self.shrink_end_time:
            self.is_shrunk = False
            self.player_size = PLAYER_SIZE
        
        # Regenerate pulse uses
        if self.pulse_uses < 5 and current_time - self.last_pulse > PULSE_COOLDOWN * 2:
            self.pulse_uses = min(5, self.pulse_uses + 1)

    def spawn_enemy(self, pattern: Pattern = None):
        if pattern is None:
            pattern = self.current_pattern
        
        # Choose random shape type
        shape_type = random.choice(list(ShapeType))
        
        # Determine spawn position based on pattern
        if pattern == Pattern.SPIRAL:
            angle = (pygame.time.get_ticks() * 0.01) % (2 * math.pi)
            radius = 400
            x = SCREEN_WIDTH // 2 + math.cos(angle) * radius
            y = SCREEN_HEIGHT // 2 + math.sin(angle) * radius
        elif pattern == Pattern.WAVE:
            x = random.choice([0, SCREEN_WIDTH])
            y = SCREEN_HEIGHT // 2 + math.sin(pygame.time.get_ticks() * 0.005) * 200
        elif pattern == Pattern.CIRCLE:
            angle = random.uniform(0, 2 * math.pi)
            radius = 500
            x = SCREEN_WIDTH // 2 + math.cos(angle) * radius
            y = SCREEN_HEIGHT // 2 + math.sin(angle) * radius
        else:  # RANDOM and others
            side = random.randint(0, 3)
            if side == 0:  # Top
                x, y = random.randint(0, SCREEN_WIDTH), -50
            elif side == 1:  # Right
                x, y = SCREEN_WIDTH + 50, random.randint(0, SCREEN_HEIGHT)
            elif side == 2:  # Bottom
                x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 50
            else:  # Left
                x, y = -50, random.randint(0, SCREEN_HEIGHT)
        
        # Calculate velocity toward player (with some randomness)
        dx = self.player_x - x
        dy = self.player_y - y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            speed = random.uniform(1, 3) * self.difficulty_multiplier
            vx = (dx / distance) * speed + random.uniform(-0.5, 0.5)
            vy = (dy / distance) * speed + random.uniform(-0.5, 0.5)
        else:
            vx = random.uniform(-2, 2)
            vy = random.uniform(-2, 2)
        
        # Create enemy
        size = random.uniform(15, 40)
        colors = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, CYAN, PINK]
        color = random.choice(colors)
        
        enemy = Enemy(
            x=x, y=y, vx=vx, vy=vy,
            shape_type=shape_type,
            size=size,
            color=color,
            rotation=random.uniform(0, 2*math.pi),
            rotation_speed=random.uniform(-0.1, 0.1),
            pulse_phase=random.uniform(0, 2*math.pi),
            dimension_phase=random.uniform(0, 2*math.pi)
        )
        
        self.enemies.append(enemy)

    def update_enemies(self):
        current_time = pygame.time.get_ticks()
        time_factor = 0.5 if self.focus_active else 1.0
        
        for enemy in self.enemies[:]:
            # Update position
            enemy.x += enemy.vx * time_factor
            enemy.y += enemy.vy * time_factor
            
            # Update rotation and effects
            enemy.rotation += enemy.rotation_speed * time_factor
            enemy.pulse_phase += 0.05 * time_factor
            enemy.dimension_phase += 0.03 * time_factor
            
            # Remove off-screen enemies
            if (enemy.x < -100 or enemy.x > SCREEN_WIDTH + 100 or
                enemy.y < -100 or enemy.y > SCREEN_HEIGHT + 100):
                self.enemies.remove(enemy)

    def check_collisions(self):
        player_radius = self.player_size
        
        for enemy in self.enemies:
            dx = enemy.x - self.player_x
            dy = enemy.y - self.player_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            collision_distance = player_radius + (enemy.size * 0.6)  # Slightly forgiving hitbox
            
            if distance < collision_distance:
                # Game over
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                self.game_active = False
                # Play game over music
                self.play_music('gameover', loop=0)  # Play once
                return

    def update_game_logic(self):
        current_time = pygame.time.get_ticks()
        
        if not self.game_active:
            return
        
        # Update score (survival time)
        self.score = (current_time - self.start_time) / 1000.0
        
        # Update difficulty
        self.difficulty_multiplier = 1.0 + (self.score / 30.0)  # Increases every 30 seconds
        
        # Spawn enemies
        spawn_rate = max(200, 1000 - int(self.score * 10))  # Faster spawning over time
        if current_time - self.spawn_timer > spawn_rate:
            self.spawn_enemy()
            self.spawn_timer = current_time
        
        # Change patterns
        if current_time - self.pattern_timer > 10000:  # Change every 10 seconds
            self.current_pattern = random.choice(list(Pattern))
            self.pattern_timer = current_time
        
        # Update abilities
        self.update_abilities()
        
        # Update enemies
        self.update_enemies()
        
        # Check collisions
        self.check_collisions()
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= 1

    def draw_shape(self, surface, shape_type: ShapeType, x: float, y: float, size: float, 
                  color: Tuple[int, int, int], rotation: float = 0, 
                  pulse_phase: float = 0, dimension_phase: float = 0):
        
        # Apply pulse effect
        pulse_size = size + math.sin(pulse_phase) * 3
        
        # Apply screen shake
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        x += shake_x
        y += shake_y
        
        if shape_type == ShapeType.CIRCLE:
            pygame.draw.circle(surface, color, (int(x), int(y)), int(pulse_size))
        
        elif shape_type == ShapeType.SQUARE:
            rect = pygame.Rect(x - pulse_size, y - pulse_size, pulse_size * 2, pulse_size * 2)
            pygame.draw.rect(surface, color, rect)
        
        elif shape_type == ShapeType.TRIANGLE:
            points = []
            for i in range(3):
                angle = rotation + (i * 2 * math.pi / 3)
                px = x + math.cos(angle) * pulse_size
                py = y + math.sin(angle) * pulse_size
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        
        elif shape_type == ShapeType.PENTAGON:
            points = []
            for i in range(5):
                angle = rotation + (i * 2 * math.pi / 5)
                px = x + math.cos(angle) * pulse_size
                py = y + math.sin(angle) * pulse_size
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        
        elif shape_type == ShapeType.HEXAGON:
            points = []
            for i in range(6):
                angle = rotation + (i * 2 * math.pi / 6)
                px = x + math.cos(angle) * pulse_size
                py = y + math.sin(angle) * pulse_size
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        
        elif shape_type == ShapeType.STAR:
            points = []
            for i in range(10):
                angle = rotation + (i * 2 * math.pi / 10)
                radius = pulse_size if i % 2 == 0 else pulse_size * 0.5
                px = x + math.cos(angle) * radius
                py = y + math.sin(angle) * radius
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
        
        elif shape_type == ShapeType.DIAMOND:
            points = [
                (x, y - pulse_size),
                (x + pulse_size, y),
                (x, y + pulse_size),
                (x - pulse_size, y)
            ]
            pygame.draw.polygon(surface, color, points)
        
        elif shape_type == ShapeType.CROSS:
            thickness = pulse_size * 0.3
            # Vertical bar
            rect1 = pygame.Rect(x - thickness, y - pulse_size, thickness * 2, pulse_size * 2)
            pygame.draw.rect(surface, color, rect1)
            # Horizontal bar
            rect2 = pygame.Rect(x - pulse_size, y - thickness, pulse_size * 2, thickness * 2)
            pygame.draw.rect(surface, color, rect2)
        
        elif shape_type == ShapeType.CUBE:
            # Pseudo-3D cube
            depth = pulse_size * 0.3
            # Front face
            rect = pygame.Rect(x - pulse_size, y - pulse_size, pulse_size * 2, pulse_size * 2)
            pygame.draw.rect(surface, color, rect)
            # Top face
            points = [
                (x - pulse_size, y - pulse_size),
                (x - pulse_size + depth, y - pulse_size - depth),
                (x + pulse_size + depth, y - pulse_size - depth),
                (x + pulse_size, y - pulse_size)
            ]
            pygame.draw.polygon(surface, tuple(min(255, c + 30) for c in color), points)
            # Right face
            points = [
                (x + pulse_size, y - pulse_size),
                (x + pulse_size + depth, y - pulse_size - depth),
                (x + pulse_size + depth, y + pulse_size - depth),
                (x + pulse_size, y + pulse_size)
            ]
            pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in color), points)
        
        elif shape_type == ShapeType.SPIRAL:
            # Draw spiral
            points = []
            for i in range(20):
                t = i * 0.3
                r = t * 3
                angle = rotation + t
                px = x + math.cos(angle) * r
                py = y + math.sin(angle) * r
                if r <= pulse_size:
                    points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(surface, color, False, points, 3)
        
        elif shape_type == ShapeType.TESSERACT:
            # 4D tesseract projection
            scale = pulse_size * 0.7
            w = math.sin(dimension_phase) * 0.5 + 0.5  # 4th dimension parameter
            
            # Inner cube
            inner_scale = scale * (0.5 + w * 0.3)
            inner_rect = pygame.Rect(x - inner_scale, y - inner_scale, inner_scale * 2, inner_scale * 2)
            pygame.draw.rect(surface, tuple(max(0, c - 50) for c in color), inner_rect)
            
            # Outer cube
            outer_scale = scale * (0.8 + w * 0.2)
            outer_rect = pygame.Rect(x - outer_scale, y - outer_scale, outer_scale * 2, outer_scale * 2)
            pygame.draw.rect(surface, color, outer_rect, 2)
            
            # Connecting lines
            for i in range(4):
                angle = i * math.pi / 2
                inner_x = x + math.cos(angle) * inner_scale
                inner_y = y + math.sin(angle) * inner_scale
                outer_x = x + math.cos(angle) * outer_scale
                outer_y = y + math.sin(angle) * outer_scale
                pygame.draw.line(surface, color, (inner_x, inner_y), (outer_x, outer_y), 1)
        
        else:
            # Default to circle for unimplemented shapes
            pygame.draw.circle(surface, color, (int(x), int(y)), int(pulse_size))

    def draw_ui(self):
        current_time = pygame.time.get_ticks()
        
        # Score
        score_text = self.font.render(f"Time: {self.score:.1f}s", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # High Score
        high_score_text = self.small_font.render(f"Best: {self.high_score:.1f}s", True, GRAY)
        self.screen.blit(high_score_text, (10, 50))
        
        # Difficulty
        diff_text = self.small_font.render(f"Difficulty: {self.difficulty_multiplier:.1f}x", True, GRAY)
        self.screen.blit(diff_text, (10, 70))
        
        # Abilities cooldowns
        y_offset = SCREEN_HEIGHT - 100
        
        # Dash
        dash_ready = (current_time - self.last_dash) > DASH_COOLDOWN
        dash_color = GREEN if dash_ready else RED
        dash_text = self.small_font.render("SHIFT: Dash", True, dash_color)
        self.screen.blit(dash_text, (10, y_offset))
        
        # Focus
        focus_ready = (current_time - self.last_focus) > FOCUS_COOLDOWN
        focus_color = GREEN if focus_ready else RED
        focus_text = self.small_font.render("SPACE: Focus Mode", True, focus_color)
        self.screen.blit(focus_text, (10, y_offset + 20))
        
        # Pulse
        pulse_ready = (current_time - self.last_pulse) > PULSE_COOLDOWN and self.pulse_uses > 0
        pulse_color = GREEN if pulse_ready else RED
        pulse_text = self.small_font.render(f"E: Pulse ({self.pulse_uses})", True, pulse_color)
        self.screen.blit(pulse_text, (10, y_offset + 40))
        
        # Shrink
        shrink_ready = (current_time - self.last_shrink) > SHRINK_COOLDOWN and not self.is_shrunk
        shrink_color = GREEN if shrink_ready else RED
        shrink_text = self.small_font.render("Q: Shrink", True, shrink_color)
        self.screen.blit(shrink_text, (10, y_offset + 60))
        
        # Music controls
        music_y = SCREEN_HEIGHT - 140
        music_status = "ON" if self.music_enabled else "OFF"
        music_text = self.small_font.render(f"M: Music ({music_status})", True, WHITE if self.music_enabled else GRAY)
        self.screen.blit(music_text, (SCREEN_WIDTH - 200, music_y))
        
        volume_text = self.small_font.render(f"Volume: {int(self.music_volume * 100)}% (+/-)", True, GRAY)
        self.screen.blit(volume_text, (SCREEN_WIDTH - 200, music_y + 20))

    def draw(self):
        self.screen.fill(BLACK)
        
        if not self.game_active:
            # Game over screen
            title_text = self.font.render("POLYCORE", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            self.screen.blit(title_text, title_rect)
            
            if self.score > 0:
                score_text = self.font.render(f"Final Time: {self.score:.1f}s", True, WHITE)
                score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
                self.screen.blit(score_text, score_rect)
            
            high_score_text = self.font.render(f"Best Time: {self.high_score:.1f}s", True, YELLOW)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(high_score_text, high_score_rect)
            
            start_text = self.small_font.render("Press ENTER to start | ESC to quit", True, GRAY)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(start_text, start_rect)
            
            # Controls
            controls = [
                "CONTROLS:",
                "Arrow Keys/WASD: Move",
                "SHIFT: Dash (cooldown)",
                "SPACE: Focus Mode (slows time)",
                "E: Pulse (knock enemies away)",
                "Q: Shrink (become smaller)",
                "M: Toggle Music",
                "+/-: Volume Control"
            ]
            
            for i, control in enumerate(controls):
                color = WHITE if i == 0 else GRAY
                control_text = self.small_font.render(control, True, color)
                control_rect = control_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100 + i * 25))
                self.screen.blit(control_text, control_rect)
        
        else:
            # Draw trail
            for i, (tx, ty, t) in enumerate(self.trail_points):
                alpha = int(255 * (i / len(self.trail_points)) * 0.3)
                trail_color = (*BLUE[:3], alpha)
                size = int(self.player_size * 0.3 * (i / len(self.trail_points)))
                if size > 0:
                    pygame.draw.circle(self.screen, BLUE, (int(tx), int(ty)), size)
            
            # Draw enemies
            for enemy in self.enemies:
                self.draw_shape(self.screen, enemy.shape_type, enemy.x, enemy.y, 
                              enemy.size, enemy.color, enemy.rotation, 
                              enemy.pulse_phase, enemy.dimension_phase)
            
            # Draw particles  
            for particle in self.particles:
                alpha = int(255 * (particle['life'] / 30))
                color = (*particle['color'][:3], alpha)
                pygame.draw.circle(self.screen, particle['color'], 
                                 (int(particle['x']), int(particle['y'])), 2)
            
            # Draw player
            player_color = CYAN if self.is_shrunk else WHITE
            if self.focus_active:
                player_color = YELLOW
            
            pygame.draw.circle(self.screen, player_color, 
                             (int(self.player_x), int(self.player_y)), self.player_size)
            pygame.draw.circle(self.screen, BLACK, 
                             (int(self.player_x), int(self.player_y)), self.player_size, 2)
            
            # Draw UI
            self.draw_ui()
            
            # Focus mode overlay
            if self.focus_active:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(30)
                overlay.fill(YELLOW)
                self.screen.blit(overlay, (0, 0))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN:
                        if not self.game_active:
                            self.reset_game()
                            self.game_active = True
                    elif event.key == pygame.K_p and self.game_active:
                        self.paused = not self.paused
                    elif event.key == pygame.K_m:
                        self.toggle_music()
                    elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        self.set_music_volume(self.music_volume - 0.1)
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                        self.set_music_volume(self.music_volume + 0.1)
                    
                    # Handle abilities
                    if self.game_active and not self.paused:
                        self.handle_abilities(event)
            
            # Handle continuous input
            if self.game_active and not self.paused:
                self.handle_input()
                self.update_game_logic()
            
            # Draw everything
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Clean up
        pygame.mixer.quit()
        pygame.quit()

# Additional shape drawing methods (extending the draw_shape method)
def draw_advanced_shapes(game_state, surface, shape_type: ShapeType, x: float, y: float, 
                        size: float, color: Tuple[int, int, int], rotation: float = 0, 
                        pulse_phase: float = 0, dimension_phase: float = 0):
    """Extended shape drawing for more complex shapes"""
    
    pulse_size = size + math.sin(pulse_phase) * 3
    shake_x = random.randint(-game_state.screen_shake, game_state.screen_shake) if game_state.screen_shake > 0 else 0
    shake_y = random.randint(-game_state.screen_shake, game_state.screen_shake) if game_state.screen_shake > 0 else 0
    x += shake_x
    y += shake_y
    
    if shape_type == ShapeType.OCTAGON:
        points = []
        for i in range(8):
            angle = rotation + (i * 2 * math.pi / 8)
            px = x + math.cos(angle) * pulse_size
            py = y + math.sin(angle) * pulse_size
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)
    
    elif shape_type == ShapeType.ELLIPSE:
        # Draw ellipse using multiple circles
        width = pulse_size * 1.5
        height = pulse_size * 0.8
        rect = pygame.Rect(x - width, y - height, width * 2, height * 2)
        pygame.draw.ellipse(surface, color, rect)
    
    elif shape_type == ShapeType.ARROW:
        # Arrow pointing in rotation direction
        tip_x = x + math.cos(rotation) * pulse_size
        tip_y = y + math.sin(rotation) * pulse_size
        
        back_x = x - math.cos(rotation) * pulse_size * 0.5
        back_y = y - math.sin(rotation) * pulse_size * 0.5
        
        wing1_x = back_x + math.cos(rotation + math.pi/2) * pulse_size * 0.3
        wing1_y = back_y + math.sin(rotation + math.pi/2) * pulse_size * 0.3
        
        wing2_x = back_x - math.cos(rotation + math.pi/2) * pulse_size * 0.3
        wing2_y = back_y - math.sin(rotation + math.pi/2) * pulse_size * 0.3
        
        points = [(tip_x, tip_y), (wing1_x, wing1_y), (back_x, back_y), (wing2_x, wing2_y)]
        pygame.draw.polygon(surface, color, points)
    
    elif shape_type == ShapeType.HEART:
        # Simple heart shape
        points = []
        for i in range(20):
            t = i * 2 * math.pi / 20
            heart_x = 16 * math.sin(t)**3
            heart_y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            
            # Scale and rotate
            cos_r = math.cos(rotation)
            sin_r = math.sin(rotation)
            scale = pulse_size / 20
            
            px = x + (heart_x * cos_r - heart_y * sin_r) * scale
            py = y + (heart_x * sin_r + heart_y * cos_r) * scale
            points.append((px, py))
        
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points)
    
    elif shape_type == ShapeType.CRESCENT:
        # Draw crescent moon
        # Outer circle
        pygame.draw.circle(surface, color, (int(x), int(y)), int(pulse_size))
        # Inner circle (cutout)
        offset_x = x + math.cos(rotation) * pulse_size * 0.3
        offset_y = y + math.sin(rotation) * pulse_size * 0.3
        pygame.draw.circle(surface, BLACK, (int(offset_x), int(offset_y)), int(pulse_size * 0.8))
    
    elif shape_type == ShapeType.LIGHTNING:
        # Zigzag lightning bolt
        points = []
        segments = 6
        for i in range(segments + 1):
            t = i / segments
            base_x = x + (t - 0.5) * pulse_size * 2
            base_y = y + (t - 0.5) * pulse_size * 0.3
            
            # Add zigzag
            if i % 2 == 1:
                base_x += pulse_size * 0.3 * math.sin(rotation)
                base_y += pulse_size * 0.3 * math.cos(rotation)
            
            points.append((base_x, base_y))
        
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, 4)
    
    elif shape_type == ShapeType.BOWTIE:
        # Bowtie shape
        points = [
            (x - pulse_size, y - pulse_size * 0.5),
            (x, y),
            (x - pulse_size, y + pulse_size * 0.5),
            (x + pulse_size, y + pulse_size * 0.5),
            (x, y),
            (x + pulse_size, y - pulse_size * 0.5)
        ]
        pygame.draw.polygon(surface, color, points)
    
    elif shape_type == ShapeType.HOURGLASS:
        # Hourglass shape
        top_points = [
            (x - pulse_size, y - pulse_size),
            (x + pulse_size, y - pulse_size),
            (x, y)
        ]
        bottom_points = [
            (x, y),
            (x - pulse_size, y + pulse_size),
            (x + pulse_size, y + pulse_size)
        ]
        pygame.draw.polygon(surface, color, top_points)
        pygame.draw.polygon(surface, color, bottom_points)
    
    elif shape_type == ShapeType.FLOWER:
        # Flower with petals
        petals = 6
        for i in range(petals):
            angle = rotation + (i * 2 * math.pi / petals)
            petal_x = x + math.cos(angle) * pulse_size * 0.7
            petal_y = y + math.sin(angle) * pulse_size * 0.7
            pygame.draw.circle(surface, color, (int(petal_x), int(petal_y)), int(pulse_size * 0.4))
        # Center
        pygame.draw.circle(surface, tuple(min(255, c + 50) for c in color), (int(x), int(y)), int(pulse_size * 0.3))
    
    elif shape_type == ShapeType.GEAR:
        # Gear with teeth
        teeth = 8
        inner_radius = pulse_size * 0.6
        outer_radius = pulse_size
        
        points = []
        for i in range(teeth * 2):
            angle = rotation + (i * 2 * math.pi / (teeth * 2))
            radius = outer_radius if i % 2 == 0 else inner_radius
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius
            points.append((px, py))
        
        pygame.draw.polygon(surface, color, points)
        # Center hole
        pygame.draw.circle(surface, BLACK, (int(x), int(y)), int(pulse_size * 0.2))
    
    elif shape_type == ShapeType.SNOWFLAKE:
        # 6-armed snowflake
        for i in range(6):
            angle = rotation + (i * math.pi / 3)
            end_x = x + math.cos(angle) * pulse_size
            end_y = y + math.sin(angle) * pulse_size
            pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)
            
            # Add small branches
            for j in [0.3, 0.6]:
                branch_x = x + math.cos(angle) * pulse_size * j
                branch_y = y + math.sin(angle) * pulse_size * j
                
                for k in [-1, 1]:
                    branch_angle = angle + k * math.pi / 6
                    branch_end_x = branch_x + math.cos(branch_angle) * pulse_size * 0.2
                    branch_end_y = branch_y + math.sin(branch_angle) * pulse_size * 0.2
                    pygame.draw.line(surface, color, (branch_x, branch_y), (branch_end_x, branch_end_y), 1)
    
    elif shape_type == ShapeType.PYRAMID:
        # 3D pyramid effect
        base_size = pulse_size
        height = pulse_size * 1.2
        
        # Base (square)
        base_points = [
            (x - base_size, y + base_size * 0.5),
            (x + base_size, y + base_size * 0.5),
            (x + base_size * 0.5, y + base_size),
            (x - base_size * 0.5, y + base_size)
        ]
        pygame.draw.polygon(surface, tuple(max(0, c - 40) for c in color), base_points)
        
        # Front face
        apex = (x, y - height * 0.5)
        front_points = [
            (x - base_size, y + base_size * 0.5),
            (x + base_size, y + base_size * 0.5),
            apex
        ]
        pygame.draw.polygon(surface, color, front_points)
        
        # Side face
        side_points = [
            (x + base_size, y + base_size * 0.5),
            (x + base_size * 0.5, y + base_size),
            apex
        ]
        pygame.draw.polygon(surface, tuple(max(0, c - 20) for c in color), side_points)
    
    elif shape_type == ShapeType.CYLINDER:
        # 3D cylinder effect
        width = pulse_size * 1.2
        height = pulse_size * 0.8
        depth = pulse_size * 0.3
        
        # Front ellipse
        front_rect = pygame.Rect(x - width, y - height, width * 2, height * 2)
        pygame.draw.ellipse(surface, color, front_rect)
        
        # Back ellipse (top)
        back_rect = pygame.Rect(x - width + depth, y - height - depth, width * 2, height * 2)
        pygame.draw.ellipse(surface, tuple(min(255, c + 30) for c in color), back_rect)
        
        # Side rectangles
        side_rect = pygame.Rect(x - width, y - height, width * 2, height * 2)
        pygame.draw.rect(surface, tuple(max(0, c - 20) for c in color), side_rect)
    
    elif shape_type == ShapeType.CONE:
        # 3D cone
        base_radius = pulse_size
        height = pulse_size * 1.5
        
        # Base circle
        pygame.draw.circle(surface, tuple(max(0, c - 40) for c in color), (int(x), int(y + height * 0.3)), int(base_radius))
        
        # Cone surface
        apex = (x, y - height * 0.7)
        cone_points = []
        for i in range(16):
            angle = i * 2 * math.pi / 16
            base_x = x + math.cos(angle) * base_radius
            base_y = y + height * 0.3 + math.sin(angle) * base_radius * 0.3
            cone_points.extend([apex, (base_x, base_y)])
        
        for i in range(0, len(cone_points) - 2, 2):
            if i + 3 < len(cone_points):
                triangle_points = [cone_points[i], cone_points[i + 1], cone_points[i + 3]]
                pygame.draw.polygon(surface, color, triangle_points)
    
    elif shape_type == ShapeType.SPHERE:
        # 3D sphere with shading
        # Main circle
        pygame.draw.circle(surface, color, (int(x), int(y)), int(pulse_size))
        
        # Highlight
        highlight_x = x - pulse_size * 0.3
        highlight_y = y - pulse_size * 0.3
        highlight_color = tuple(min(255, c + 80) for c in color)
        pygame.draw.circle(surface, highlight_color, (int(highlight_x), int(highlight_y)), int(pulse_size * 0.3))
        
        # Shadow
        shadow_x = x + pulse_size * 0.2
        shadow_y = y + pulse_size * 0.2
        shadow_color = tuple(max(0, c - 60) for c in color)
        pygame.draw.circle(surface, shadow_color, (int(shadow_x), int(shadow_y)), int(pulse_size * 0.4))
    
    elif shape_type == ShapeType.TORUS:
        # Torus (donut shape)
        outer_radius = pulse_size
        inner_radius = pulse_size * 0.4
        
        # Outer circle
        pygame.draw.circle(surface, color, (int(x), int(y)), int(outer_radius))
        # Inner circle (hole)
        pygame.draw.circle(surface, BLACK, (int(x), int(y)), int(inner_radius))
        
        # 3D effect with ellipses
        depth_offset = pulse_size * 0.2
        top_rect = pygame.Rect(x - outer_radius, y - outer_radius - depth_offset, 
                              outer_radius * 2, inner_radius)
        pygame.draw.ellipse(surface, tuple(min(255, c + 30) for c in color), top_rect)
    
    elif shape_type == ShapeType.PRISM:
        # Triangular prism
        base_size = pulse_size
        depth = pulse_size * 0.4
        
        # Front triangle
        front_points = [
            (x, y - base_size),
            (x - base_size, y + base_size * 0.5),
            (x + base_size, y + base_size * 0.5)
        ]
        pygame.draw.polygon(surface, color, front_points)
        
        # Back triangle (offset)
        back_points = [
            (x + depth, y - base_size - depth),
            (x - base_size + depth, y + base_size * 0.5 - depth),
            (x + base_size + depth, y + base_size * 0.5 - depth)
        ]
        pygame.draw.polygon(surface, tuple(min(255, c + 20) for c in color), back_points)
        
        # Connecting edges
        for i in range(3):
            pygame.draw.line(surface, tuple(max(0, c - 30) for c in color), 
                           front_points[i], back_points[i], 2)
    
    elif shape_type == ShapeType.DODECAHEDRON:
        # 12-sided polyhedron (simplified as complex polygon)
        points = []
        for i in range(12):
            angle = rotation + (i * 2 * math.pi / 12)
            radius = pulse_size * (0.8 + 0.2 * math.sin(i * 3))  # Slight variation
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)
        
        # Inner detail
        inner_points = []
        for i in range(6):
            angle = rotation + (i * 2 * math.pi / 6)
            px = x + math.cos(angle) * pulse_size * 0.4
            py = y + math.sin(angle) * pulse_size * 0.4
            inner_points.append((px, py))
        pygame.draw.polygon(surface, tuple(min(255, c + 40) for c in color), inner_points)
    
    elif shape_type == ShapeType.ICOSAHEDRON:
        # 20-sided polyhedron
        points = []
        layers = 3
        for layer in range(layers):
            layer_radius = pulse_size * (1 - layer * 0.2)
            points_in_layer = 6 + layer * 2
            for i in range(points_in_layer):
                angle = rotation + (i * 2 * math.pi / points_in_layer) + layer * 0.5
                px = x + math.cos(angle) * layer_radius
                py = y + math.sin(angle) * layer_radius * 0.8
                points.append((px, py))
        
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points)
    
    elif shape_type == ShapeType.TETRAHEDRON:
        # 4-sided pyramid
        base_size = pulse_size * 0.8
        height = pulse_size
        
        # Base triangle
        base_points = [
            (x - base_size, y + base_size * 0.5),
            (x + base_size, y + base_size * 0.5),
            (x, y - base_size * 0.5)
        ]
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in color), base_points)
        
        # Apex point
        apex = (x, y - height * 0.8)
        
        # Three visible faces
        for i in range(3):
            face_points = [base_points[i], base_points[(i + 1) % 3], apex]
            face_color = tuple(max(0, c - 10 * i) for c in color)
            pygame.draw.polygon(surface, face_color, face_points)
    
    elif shape_type == ShapeType.HYPERSPHERE:
        # 4D hypersphere projection (series of concentric circles)
        w = math.sin(dimension_phase) * 0.5 + 0.5
        
        for i in range(4):
            layer_w = (i / 3) * 2 - 1  # -1 to 1
            if abs(layer_w) <= 1:
                radius = pulse_size * math.sqrt(1 - layer_w**2) * (0.3 + w * 0.7)
                alpha = int(255 * (1 - abs(layer_w)) * 0.7)
                layer_color = (*color[:3], alpha)
                if radius > 1:
                    pygame.draw.circle(surface, color, (int(x), int(y)), int(radius), 2)
    
    elif shape_type == ShapeType.HYPERPRISM:
        # 4D hyperprism projection
        w1 = math.sin(dimension_phase) * 0.3
        w2 = math.cos(dimension_phase) * 0.3
        
        # Multiple rectangular layers
        for i in range(3):
            layer_w = (i - 1) * 0.5
            offset_x = layer_w * w1 * pulse_size
            offset_y = layer_w * w2 * pulse_size
            
            rect_size = pulse_size * (0.6 + 0.4 * (2 - i))
            rect = pygame.Rect(x + offset_x - rect_size, y + offset_y - rect_size, 
                              rect_size * 2, rect_size * 2)
            
            alpha = int(255 * (0.3 + 0.7 * (2 - i) / 2))
            layer_color = tuple(max(0, min(255, c + i * 20)) for c in color)
            pygame.draw.rect(surface, layer_color, rect, 2)
    
    elif shape_type == ShapeType.SIMPLEX_4D:
        # 4D simplex (5-vertex hypertetrahedron projection)
        w = dimension_phase
        vertices_4d = [
            (1, 1, 1, 1),
            (1, -1, -1, 1),
            (-1, 1, -1, 1),
            (-1, -1, 1, 1),
            (0, 0, 0, -4)
        ]
        
        # Project to 2D
        projected_vertices = []
        for vx, vy, vz, vw in vertices_4d:
            # Simple 4D to 2D projection
            scale = pulse_size * 0.3
            px = x + (vx + vw * math.cos(w)) * scale
            py = y + (vy + vw * math.sin(w)) * scale
            projected_vertices.append((px, py))
        
        # Draw edges (simplified)
        for i in range(len(projected_vertices)):
            for j in range(i + 1, len(projected_vertices)):
                pygame.draw.line(surface, color, 
                               (int(projected_vertices[i][0]), int(projected_vertices[i][1])),
                               (int(projected_vertices[j][0]), int(projected_vertices[j][1])), 1)

# Extend the original draw_shape method to use advanced shapes
def extend_draw_shape_method():
    """Monkey patch to extend the draw_shape method"""
    original_draw_shape = GameState.draw_shape
    
    def extended_draw_shape(self, surface, shape_type: ShapeType, x: float, y: float, 
                           size: float, color: Tuple[int, int, int], rotation: float = 0, 
                           pulse_phase: float = 0, dimension_phase: float = 0):
        
        # Try advanced shapes first
        advanced_shapes = {
            ShapeType.OCTAGON, ShapeType.ELLIPSE, ShapeType.ARROW, ShapeType.HEART,
            ShapeType.CRESCENT, ShapeType.LIGHTNING, ShapeType.BOWTIE, ShapeType.HOURGLASS,
            ShapeType.FLOWER, ShapeType.GEAR, ShapeType.SNOWFLAKE, ShapeType.PYRAMID,
            ShapeType.CYLINDER, ShapeType.CONE, ShapeType.SPHERE, ShapeType.TORUS,
            ShapeType.PRISM, ShapeType.DODECAHEDRON, ShapeType.ICOSAHEDRON, 
            ShapeType.TETRAHEDRON, ShapeType.HYPERSPHERE, ShapeType.HYPERPRISM, 
            ShapeType.SIMPLEX_4D
        }
        
        if shape_type in advanced_shapes:
            draw_advanced_shapes(self, surface, shape_type, x, y, size, color, 
                                rotation, pulse_phase, dimension_phase)
        else:
            # Use original method for basic shapes
            original_draw_shape(self, surface, shape_type, x, y, size, color, 
                               rotation, pulse_phase, dimension_phase)
    
    GameState.draw_shape = extended_draw_shape

# Apply the extension
extend_draw_shape_method()

# Main execution
if __name__ == "__main__":
    game = GameState()
    game.run()