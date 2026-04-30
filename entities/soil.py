from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame
from pytmx.util_pygame import (
    load_pygame,  # pyright: ignore[reportUnknownVariableType]
)

from core.settings import *
from core.utils import get_path, import_folder, import_folder_dict
from entities.player import CameraGroup, Player

if TYPE_CHECKING:
    from typing import Any, Callable, Literal

    from pygame import Rect, Sound, Surface
    from pygame.sprite import Group

    from entities.player import CameraGroup


class SoilTile(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: tuple[int, int],
        surf: Surface,
        groups: list[Group[SoilTile] | CameraGroup],
    ) -> None:
        super().__init__(groups)
        self.image: Surface = surf
        self.rect: Rect = self.image.get_rect(topleft=pos)
        self.z: int = LAYERS["soil"]


class WaterTile(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: tuple[int, int],
        surf: Surface,
        groups: list[Group[WaterTile] | CameraGroup],
    ) -> None:
        super().__init__(groups)
        self.image: Surface = surf
        self.rect: Rect = self.image.get_rect(topleft=pos)
        self.z: int = LAYERS["soil_water"]


class Plant(pygame.sprite.Sprite):
    def __init__(
        self,
        plant_type: str,
        groups: list[Group[Plant] | CameraGroup],
        soil: SoilTile,
        check_watered: Callable[[tuple[int, int]], bool],
    ) -> None:
        super().__init__(groups)
        self.plant_type: str = plant_type

        # setup
        plant_path = f"graphics/images/fruit/{plant_type}"
        self.frames: list[Surface] = import_folder(plant_path)
        self.soil: SoilTile = soil
        self.check_watered: Callable[[tuple[int, int]], bool] = check_watered

        # plant growing
        self.age: int | float = 0
        self.max_age: int = len(self.frames) - 1
        self.grow_speed: int | float = GROW_SPEED[plant_type]
        self.harvestable: bool = False

        # sprite setup
        self.image: Surface = self.frames[self.age]
        self.y_offset: Literal[-16, -8] = -16 if plant_type == "corn" else -8
        self.rect: Rect = self.image.get_rect(
            midbottom=soil.rect.midbottom
            + pygame.math.Vector2(0, self.y_offset)
        )
        self.z: int = LAYERS["ground_plant"]

    def grow(self) -> None:
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS["main"]
                self.hitbox: Rect = self.rect.copy().inflate(
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
        all_sprites: CameraGroup,
        collision_sprites: Group[Any],
        raining: bool,
    ) -> None:
        # sprite groups
        self.all_sprites: CameraGroup = all_sprites
        self.collision_sprites: Group[Any] = collision_sprites
        self.soil_sprites: Group[SoilTile] = pygame.sprite.Group()
        self.water_sprites: Group[WaterTile] = pygame.sprite.Group()
        self.plant_sprites: Group[Plant] = pygame.sprite.Group()

        self.raining: bool = raining

        self.soil_surfs: dict[str, Surface] = import_folder_dict(
            "graphics/images/soil"
        )
        self.water_surfs: list[Surface] = import_folder(
            "graphics/images/soil_water"
        )

        self.create_soil_grid()
        self.create_hit_rects()

        self.soil_coords: list[list[float]] = []

        # sounds
        hoe_sound_path = get_path("../audio/hoe.wav")
        self.hoe_sound: Sound = pygame.mixer.Sound(hoe_sound_path)
        self.hoe_sound.set_volume(0.1)

        plant_sound_path = get_path("../audio/plant.wav")
        self.plant_sound: Sound = pygame.mixer.Sound(plant_sound_path)
        self.plant_sound.set_volume(0.2)

    def create_soil_grid(self) -> None:
        ground_path = "graphics/images/world/ground.png"
        ground = pygame.image.load(ground_path)
        h_tiles, v_tiles = (
            ground.get_width() // TILE_SIZE,
            ground.get_height() // TILE_SIZE,
        )

        self.grid: list[list[list[Any]]] = [
            [[] for _ in range(h_tiles)] for _ in range(v_tiles)
        ]
        map_tmx = "graphics/data/map.tmx"
        for x, y, _ in (  # pyright: ignore[reportUnknownVariableType]
            load_pygame(map_tmx).get_layer_by_name("Farmable").tiles()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        ):
            self.grid[y][x].append("F")

    def create_hit_rects(self) -> None:
        self.hit_rects: list[Rect] = []
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

    def water(self, target_pos: tuple[int, int] | Vector2) -> None:
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

    def check_watered(self, pos: tuple[int, int]) -> bool:
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = "W" in cell
        return is_watered

    def plant_seed(
        self, target_pos: tuple[int, int] | Vector2, seed: str, player: Player
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
