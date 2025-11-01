import random
from typing import List, Tuple

import pygame
from pytmx.util_pygame import load_pygame

from core.settings import *
from core.utils import get_path, import_folder, import_folder_dict
from entities.player import Player


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS["soil"]


class WaterTile(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: Tuple[int, int],
        surf: pygame.Surface,
        groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS["soil_water"]


class Plant(pygame.sprite.Sprite):
    def __init__(
        self,
        plant_type: str,
        groups: List[pygame.sprite.Group],
        soil,
        check_watered: bool,
    ) -> None:
        super().__init__(groups)
        self.plant_type = plant_type

        # setup
        plant_path = f"graphics/images/fruit/{plant_type}"
        self.frames = import_folder(plant_path)
        self.soil = soil
        self.check_watered = check_watered

        # plant growing
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        # sprite setup
        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == "corn" else -8
        self.rect = self.image.get_rect(
            midbottom=soil.rect.midbottom
            + pygame.math.Vector2(0, self.y_offset)
        )
        self.z = LAYERS["ground_plant"]

    def grow(self) -> None:
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS["main"]
                self.hitbox = self.rect.copy().inflate(
                    -26, -self.rect.height * 0.4
                )

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(
                midbottom=self.soil.rect.midbottom
                + pygame.math.Vector2(0, self.y_offset)
            )


class SoilLayer:
    def __init__(
        self,
        all_sprites: pygame.sprite.Sprite,
        collision_sprites: pygame.sprite.Sprite,
        raining: bool,
    ) -> None:
        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.raining = raining

        self.soil_surfs = import_folder_dict("graphics/images/soil")
        self.water_surfs = import_folder("graphics/images/soil_water")

        self.create_soil_grid()
        self.create_hit_rects()

        self.soil_coords: List[Vector2] = []

        # sounds
        hoe_sound_path = get_path("../audio/hoe.wav")
        self.hoe_sound = pygame.mixer.Sound(hoe_sound_path)
        self.hoe_sound.set_volume(0.1)

        plant_sound_path = get_path("../audio/plant.wav")
        self.plant_sound = pygame.mixer.Sound(plant_sound_path)
        self.plant_sound.set_volume(0.2)

    def create_soil_grid(self) -> None:
        ground_path = "graphics/images/world/ground.png"
        ground = pygame.image.load(ground_path)
        h_tiles, v_tiles = (
            ground.get_width() // TILE_SIZE,
            ground.get_height() // TILE_SIZE,
        )

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        map_tmx = "graphics/data/map.tmx"
        for x, y, _ in (
            load_pygame(map_tmx).get_layer_by_name("Farmable").tiles()
        ):
            self.grid[y][x].append("F")

    def create_hit_rects(self) -> None:
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if "F" in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point: Vector2) -> None:
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                self.hoe_sound.play()

                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if "F" in self.grid[y][x]:
                    self.grid[y][x].append("X")
                    self.create_soil_tiles()
                    self.soil_coords.append(list(point))
                    if self.raining:
                        self.water_all()

    def water(self, target_pos: Tuple[int, int]) -> None:
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append("W")

                pos = soil_sprite.rect.topleft
                surf = random.choice(self.water_surfs)
                WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

    def water_all(self) -> None:
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if "X" in cell and "W" not in cell:
                    cell.append("W")

                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    surf = random.choice(self.water_surfs)
                    WaterTile(
                        (x, y), surf, [self.all_sprites, self.water_sprites]
                    )

    def remove_water(self) -> None:
        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up the grid
        for row in self.grid:
            for cell in row:
                if "W" in cell:
                    cell.remove("W")

    def check_watered(self, pos: Tuple[int, int]) -> None:
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = "W" in cell
        return is_watered

    def plant_seed(
        self, target_pos: Tuple[int, int], seed: str, player: Player
    ) -> None:
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                self.plant_sound.play()

                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE

                if "P" not in self.grid[y][x]:
                    self.grid[y][x].append("P")
                    Plant(
                        seed,
                        [
                            self.all_sprites,
                            self.plant_sprites,
                            self.collision_sprites,
                        ],
                        soil_sprite,
                        self.check_watered,
                    )
                    player.inventory.update_item(-1)

    def update_plants(self) -> None:
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self) -> None:
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if "X" in cell:
                    # tile options
                    t = "X" in self.grid[index_row - 1][index_col]
                    b = "X" in self.grid[index_row + 1][index_col]
                    r = "X" in row[index_col + 1]
                    l = "X" in row[index_col - 1]

                    tile_type = "o"

                    # all sides
                    if all((t, r, b, l)):
                        tile_type = "x"

                    # horizontal tiles only
                    if l and not any((t, r, b)):
                        tile_type = "r"
                    if r and not any((t, l, b)):
                        tile_type = "l"
                    if r and l and not any((t, b)):
                        tile_type = "lr"

                    # vertical only
                    if t and not any((r, l, b)):
                        tile_type = "b"
                    if b and not any((r, l, t)):
                        tile_type = "t"
                    if b and t and not any((r, l)):
                        tile_type = "tb"

                    # corners
                    if l and b and not any((t, r)):
                        tile_type = "tr"
                    if r and b and not any((t, l)):
                        tile_type = "tl"
                    if l and t and not any((b, r)):
                        tile_type = "br"
                    if r and t and not any((b, l)):
                        tile_type = "bl"

                    # T shapes
                    if all((t, b, r)) and not l:
                        tile_type = "tbr"
                    if all((t, b, l)) and not r:
                        tile_type = "tbl"
                    if all((l, r, t)) and not b:
                        tile_type = "lrb"
                    if all((l, r, b)) and not t:
                        tile_type = "lrt"

                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites],
                    )
