import pygame
import random
import heapq

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 64
GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE
grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Village Simulation")


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Clock
clock = pygame.time.Clock()
FPS = 30  # Reduced FPS for slower movement

# A* Pathfinding Algorithm
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(grid, start, goal):
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal:
            break

        for next in neighbors(grid, current):
            new_cost = cost_so_far[current] + 1
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                heapq.heappush(frontier, (priority, next))
                came_from[next] = current

    return reconstruct_path(came_from, start, goal)

def neighbors(grid, current):
    (x, y) = current
    results = [(x + dx, y + dy) for dx, dy in [
        (-1, 0), (1, 0), (0, -1), (0, 1),  # Orthogonal
        (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonals
    ]]
    results = filter(lambda p: 0 <= p[0] < GRID_WIDTH and 0 <= p[1] < GRID_HEIGHT, results)
    results = filter(lambda p: grid[p[1]][p[0]] == 0, results)
    return results

def reconstruct_path(came_from, start, goal):
    current = goal
    path = []
    while current != start:
        if current not in came_from:
            print(f"Error: {current} not in came_from dictionary")
            return []  # Return an empty path or handle the error
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

# Load and extract villager walking animation sprites
def extract_sprites(sheet, sprite_width, sprite_height, num_sprites_x, num_sprites_y):
    sprites = []
    for y in range(num_sprites_y):
        for x in range(num_sprites_x):
            rect = pygame.Rect(x * sprite_width, y * sprite_height, sprite_width, sprite_height)
            image = pygame.Surface(rect.size, pygame.SRCALPHA)  # Ensure alpha transparency
            image.blit(sheet, (0, 0), rect)
            sprites.append(image)
    return sprites

# Load sprite sheet
sprite_sheet = pygame.image.load('sprites/Unarmed_Walk_full.png').convert_alpha()  # Ensure correct transparency handling
villager_sprites = extract_sprites(sprite_sheet, TILE_SIZE, TILE_SIZE, 6, 4)

# Create grid
grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
# Set to keep track of occupied cells
occupied_cells = set()

class Item:
    def __init__(self, item_type):
        self.item_type = item_type

class Villager(pygame.sprite.Sprite):
    def __init__(self, x, y, money=10, health=100, hunger=0):
        super().__init__()
        self.idle_sprites = extract_sprites(pygame.image.load('sprites/Unarmed_Idle_full.png').convert_alpha(), TILE_SIZE, TILE_SIZE, 6, 4)
        self.foraging_sprites = extract_sprites(pygame.image.load('sprites/Unarmed_Walk_full.png').convert_alpha(), TILE_SIZE, TILE_SIZE, 6, 4)
        
        self.sprites = self.idle_sprites  # Start with idle animation
        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.grid_pos = (x, y)
        self.rect.topleft = (x * TILE_SIZE, y * TILE_SIZE)
        self.path = []
        self.state = "idle"
        self.target = None
        self.animation_time = 0  # Time for animation frame update
        self.animation_speed = 50  # Time between frames in milliseconds
        self.movement_delay = 50  # Time between movement steps (in milliseconds)
        self.last_move_time = pygame.time.get_ticks()  # Time of last move
        self.money = money  # Initialize money
        self.health = health  # Initialize health
        self.hunger = hunger  # Initialize hunger
        self.hunger_increment_time = pygame.time.get_ticks()  # Time of last hunger increment
        self.hunger_increment_delay = 5000  # Increase hunger every 5 seconds
        self.inventory = []  # Initialize inventory as an empty list

    def find_seller(self):
        # Find the nearest villager with food
        min_distance = float('inf')
        seller = None
        for v in villagers:
            if v != self and v.inventory and v.inventory[0].item_type == "food":
                distance = abs(self.grid_pos[0] - v.grid_pos[0]) + abs(self.grid_pos[1] - v.grid_pos[1])
                if distance < min_distance:
                    min_distance = distance
                    seller = v
        return seller

    def buy_food(self, seller):
        if self.money >= 10:
            self.money -= 10
            seller.money += 10
            if seller.inventory:
                food_item = seller.inventory.pop(0)
                self.inventory.append(food_item)
                print(f"Villager {self.grid_pos} bought food from Villager {seller.grid_pos}.")
        else:
            print(f"Villager {self.grid_pos} does not have enough money to buy food.")

    def move_to(self, target_pos):
        self.state = "moving"
        self.target = target_pos
        self.path = a_star_search(grid, self.grid_pos, self.target)
        print(f"Villager {self.grid_pos} is moving towards {self.target}")

    def update(self):
        current_time = pygame.time.get_ticks()

        # Increment hunger over time
        if current_time - self.hunger_increment_time >= self.hunger_increment_delay:
            self.hunger += 2  # Increase hunger by 2 (you can adjust this value)
            self.hunger_increment_time = current_time  # Reset the last increment time

        # Eat food if hunger is greater than 9
        if self.hunger > 9 and self.inventory:
            self.hunger = 0  # Reset hunger after eating
            self.inventory.pop(0)  # Remove one food from inventory
            print(f"Villager {self.grid_pos} ate a food item from the inventory. Remaining inventory: {len(self.inventory)}")

        if self.state == "idle":
            if random.random() < 0.01:
                if len(food_items) > 0:
                    available_food = [food for food in food_items if food.claimed_by is None]  # Only unclaimed food
                    if available_food:
                        self.state = "foraging"
                        self.target = random.choice(available_food).grid_pos
                        food_item = next(food for food in food_items if food.grid_pos == self.target)
                        food_item.claimed_by = self  # Claim the food
                        self.path = a_star_search(grid, self.grid_pos, self.target)
                        print(f"Villager {self.grid_pos} starts foraging towards {self.target}")

        elif self.state == "foraging":
            if self.path:
                if current_time - self.last_move_time >= self.movement_delay:
                    next_pos = self.path.pop(0)
                    if grid[next_pos[1]][next_pos[0]] == 0:
                        self.grid_pos = next_pos
                        self.rect.topleft = (self.grid_pos[0] * TILE_SIZE, self.grid_pos[1] * TILE_SIZE)
                        self.last_move_time = current_time

                        if self.grid_pos == self.target:
                            # Unclaim the food item before changing the state
                            for food in food_items:
                                if food.grid_pos == self.grid_pos:
                                    if food.claimed_by == self:
                                        food.claimed_by = None

                            self.state = "idle"
                            self.target = None

                            # Find the food item at this position
                            for food in food_items:
                                if food.grid_pos == self.grid_pos:
                                    if self.hunger < 5:
                                        self.inventory.append(Item("food"))
                                        print(f"Villager {self.grid_pos} has stored the food. Inventory: {len(self.inventory)}")
                                    else:
                                        self.hunger = 0
                                        print(f"Villager {self.grid_pos} has eaten the food.")
                                    food.kill()
                                    break

        elif self.state == "buying":
            if self.path:
                if current_time - self.last_move_time >= self.movement_delay:
                    next_pos = self.path.pop(0)
                    if grid[next_pos[1]][next_pos[0]] == 0:
                        self.grid_pos = next_pos
                        self.rect.topleft = (self.grid_pos[0] * TILE_SIZE, self.grid_pos[1] * TILE_SIZE)
                        self.last_move_time = current_time

                        if self.grid_pos == self.target:
                            seller = self.find_seller()
                            if seller:
                                self.buy_food(seller)
                                self.state = "idle"
                                self.target = None
                            else:
                                self.state = "idle"
                                self.target = None

        # Additional check before any other state transitions
        if self.state != "foraging" and self.target is not None:
            food_item = next((food for food in food_items if food.grid_pos == self.target), None)
            if food_item and food_item.claimed_by == self:
                food_item.claimed_by = None

        # Update animation
        self.animation_time += clock.get_time()
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_sprite = (self.current_sprite + 1) % len(self.sprites)
            self.image = self.sprites[self.current_sprite]

        # Update sprite list based on state
        if self.state == "idle":
            self.sprites = self.idle_sprites
        elif self.state == "foraging":
            self.sprites = self.foraging_sprites

class House(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Load the house sprite image
        self.image = pygame.image.load('sprites/House.png').convert_alpha()  # Ensure correct transparency handling
        # Scale the image to cover 2x2 tiles
        self.image = pygame.transform.scale(self.image, (2 * TILE_SIZE, 2 * TILE_SIZE))
        self.rect = self.image.get_rect()
        # Set the position of the house to cover four tiles
        self.grid_pos = (x, y)
        self.rect.topleft = (x * TILE_SIZE, y * TILE_SIZE)
        # Mark the grid cells as blocked
        self.update_grid()

    def update_grid(self):
        # Mark 2x2 area as blocked in the grid
        for dy in range(2):
            for dx in range(2):
                grid_y = self.grid_pos[1] + dy
                grid_x = self.grid_pos[0] + dx
                grid[grid_y][grid_x] = 1
                occupied_cells.add((grid_x, grid_y))

class Food(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        original_image = pygame.image.load('sprites/Apple.png').convert_alpha()
        self.image = pygame.transform.scale(original_image, (32, 32))  # Scale to 32x32
        self.rect = self.image.get_rect()
        self.grid_pos = (x, y)
        #Center of a Food within a Grid Cell
        self.rect.center = (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
        self.claimed_by = None  # No villager is claiming this food initially

class Bush(pygame.sprite.Sprite):
    def __init__(self, x, y, bush_type):
        super().__init__()
        bush_image = pygame.image.load(f'sprites/Bush_{bush_type}.png').convert_alpha()
        self.image = pygame.transform.scale(bush_image, (TILE_SIZE, TILE_SIZE))  # Scale to 64x64
        self.rect = self.image.get_rect()
        self.grid_pos = (x, y)
        self.rect.topleft = (x * TILE_SIZE, y * TILE_SIZE)
        self.update_grid()

    def update_grid(self):
        grid_y, grid_x = self.grid_pos
        
        # Add bounds check before updating the grid
        if 0 <= grid_y < GRID_HEIGHT and 0 <= grid_x < GRID_WIDTH:
            grid[grid_y][grid_x] = 1
            occupied_cells.add((grid_x, grid_y))
        else:
            print(f"Error: Bush position out of bounds! grid_pos=({grid_x}, {grid_y})")

# Update Tree class to block the grid correctly
class Tree(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Load the tree sprite image and resize it to 64x64 (or appropriate size)
        original_image = pygame.image.load('sprites/Tree.png').convert_alpha()
        self.image = pygame.transform.scale(original_image, (2 * TILE_SIZE, 2 * TILE_SIZE))  # Scale to cover 2x2 tiles
        self.rect = self.image.get_rect()
        self.grid_pos = (x, y)
        # Set the position to cover four tiles
        self.rect.topleft = (x * TILE_SIZE, y * TILE_SIZE)
        # Mark the grid cells as blocked
        self.update_grid()

    def update_grid(self):
        # Mark a 2x2 area as blocked in the grid
        for dy in range(2):
            for dx in range(2):
                grid_y = self.grid_pos[1] + dy
                grid_x = self.grid_pos[0] + dx
                if 0 <= grid_y < GRID_HEIGHT and 0 <= grid_x < GRID_WIDTH:
                    grid[grid_y][grid_x] = 1
                    occupied_cells.add((grid_x, grid_y))



# Sprite groups
villagers = pygame.sprite.Group()
houses = pygame.sprite.Group()
food_items = pygame.sprite.Group()
trees = pygame.sprite.Group()
# Sprite group for bushes
bushes = pygame.sprite.Group()

# Create houses
for _ in range(5):
    while True:
        x, y = random.randint(0, GRID_WIDTH - 2), random.randint(0, GRID_HEIGHT - 2)
        # Check if the 2x2 area for the new house is free
        if all((x + dx, y + dy) not in occupied_cells for dx in range(2) for dy in range(2)):
            house = House(x, y)
            houses.add(house)
            break

# Create trees, ensuring they do not overlap with houses, food items, or villagers
for _ in range(5):  # Number of trees to spawn
    while True:
        x, y = random.randint(0, GRID_WIDTH - 2), random.randint(0, GRID_HEIGHT - 2)
        # Ensure the spawn location for the 2x2 area is not occupied
        if all(
            (x + dx, y + dy) not in occupied_cells and
            not any(villager.grid_pos == (x + dx, y + dy) for villager in villagers) and
            not any(food.grid_pos == (x + dx, y + dy) for food in food_items)
            for dx in range(2) for dy in range(2)
        ):
            tree = Tree(x, y)
            trees.add(tree)
            break

# Create food items, ensuring they do not spawn on top of houses or trees
for _ in range(9):
    while True:
        x, y = random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)
        if grid[y][x] == 0 and not any(villager.grid_pos == (x, y) for villager in villagers):
            food = Food(x, y)
            food_items.add(food)
            break

# Create villagers
for _ in range(9):
    while True:
        x, y = random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)
        if grid[y][x] == 0:
            villager = Villager(x, y)
            villagers.add(villager)
            break

# Create bushes, ensuring they do not overlap with houses, food items, or villagers
for _ in range(10):  # Number of bushes to spawn
    while True:
        x, y = random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)
        # Ensure the spawn location is not occupied by a house, villager, or existing food
        if grid[y][x] == 0 and not any(villager.grid_pos == (x, y) for villager in villagers) and not any(food.grid_pos == (x, y) for food in food_items):
            bush_type = random.choice([1, 2])  # Randomly select Bush_1 or Bush_2
            bush = Bush(x, y, bush_type)
            bushes.add(bush)
            break



# Load and scale grass texture
grass_texture = pygame.image.load('sprites/grass.jpg').convert()
grass_texture = pygame.transform.scale(grass_texture, (TILE_SIZE, TILE_SIZE))  # Scale to 32x32

# Main game loop
running = True
last_food_spawn_time = pygame.time.get_ticks()  # Time of the last food spawn
selected_villager = None  # Track the selected villager

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button click
            mouse_pos = pygame.mouse.get_pos()
            for villager in villagers:
                if villager.rect.collidepoint(mouse_pos):
                    selected_villager = villager
                    break

    # Update sprites
    villagers.update()

    # Check if it's time to spawn new food
    current_time = pygame.time.get_ticks()
    if current_time - last_food_spawn_time >= 10000:  # 10 seconds
        last_food_spawn_time = current_time
        num_food_to_spawn = len(villagers) * (1) - 3  # Number of food items to spawn

        for _ in range(num_food_to_spawn):
            while True:
                x, y = random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)
                # Ensure the spawn location is not occupied by a house, villager, or existing food
                if grid[y][x] == 0 and not any(villager.grid_pos == (x, y) for villager in villagers) and not any(food.grid_pos == (x, y) for food in food_items):
                    food = Food(x, y)
                    food_items.add(food)
                    break

    # Render the game world
    for y in range(0, HEIGHT, TILE_SIZE):
        for x in range(0, WIDTH, TILE_SIZE):
            screen.blit(grass_texture, (x, y))  # Draw grass texture tile by tile

    houses.draw(screen)
    villagers.draw(screen)
    trees.draw(screen)
    food_items.draw(screen)
    bushes.draw(screen)  # Draw bushes


    # Display selected villager stats
    if selected_villager:
        font = pygame.font.Font(None, 36)
        stats_text = f"Health: {selected_villager.health} Money: {selected_villager.money} Hunger: {selected_villager.hunger} Inventory: {len(selected_villager.inventory)}"
        text_surface = font.render(stats_text, True, BLACK)
        screen.blit(text_surface, (10, HEIGHT - 40))  # Bottom left corner of the screen

    pygame.display.flip()

    # Cap the frame rate
    clock.tick(FPS)

pygame.quit()