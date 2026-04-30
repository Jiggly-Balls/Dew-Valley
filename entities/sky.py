import random

import pygame

from core.settings import *
from core.utils import import_folder
from entities.sprites import BaseSprite


class Sky:
    def __init__(self, display: pygame.Surface) -> None:
        self.display_surface = display
        self.full_surf = pygame.Surface(Display.SCREEN_RESOLUTION)
        self.start_color = [255, 255, 255]
        self.end_color = (38, 101, 189)
        self.day_speed = 1.2

    def display(self, dt: float) -> None:
        for index, value in enumerate(self.end_color):
            if self.start_color[index] > value:
                self.start_color[index] -= self.day_speed * dt

        self.full_surf.fill(self.start_color)
        self.display_surface.blit(
            self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )


class Drop(BaseSprite):
    def __init__(
        self,
        surf: pygame.Surface,
        pos: Tuple[int, int],
        moving: bool,
        groups: Union[pygame.sprite.Group, Sequence[pygame.sprite.Group]],
        z: int,
    ) -> None:
        # general setup
        super().__init__(pos, surf, groups, z)
        self.lifetime = random.randint(400, 500)
        self.start_time = pygame.time.get_ticks()

        # moving
        self.moving = moving
        if self.moving:
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-2, 4)
            self.speed = random.randint(200, 250)

    def update(self, dt: int) -> None:
        # movement
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # timer
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()


class Rain:
    def __init__(
        self, display: pygame.Surface, all_sprites: pygame.sprite.Group
    ) -> None:
        self.display_window = display
        self.all_sprites = all_sprites
        self.rain_drops = import_folder("graphics/images/rain/drops")
        self.rain_floor = import_folder("graphics/images/rain/floor")
        self.floor_w, self.floor_h = pygame.image.load(
            "graphics/images/world/ground.png"
        ).get_size()

    def create_floor(self) -> None:
        Drop(
            surf=random.choice(self.rain_floor),
            pos=(
                random.randint(0, self.floor_w),
                random.randint(0, self.floor_h),
            ),
            moving=False,
            groups=self.all_sprites,
            z=LAYERS["rain_floor"],
        )

    def create_drops(self) -> None:
        Drop(
            surf=random.choice(self.rain_drops),
            pos=(
                random.randint(0, self.floor_w),
                random.randint(0, self.floor_h),
            ),
            moving=True,
            groups=self.all_sprites,
            z=LAYERS["rain_drops"],
        )

    def dim_screen(self) -> None:
        self.display_window.fill(
            (200, 200, 200), special_flags=pygame.BLEND_RGBA_MULT
        )

    def update(self) -> None:
        self.dim_screen()
        self.create_floor()
        self.create_drops()
