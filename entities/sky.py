from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from core.settings import *
from core.utils import import_folder
from entities.sprites import BaseSprite

if TYPE_CHECKING:
    from typing import Any, Literal

    from pygame import Surface, Vector2
    from pygame.sprite import Group

    from entities.player import CameraGroup


class Sky:
    def __init__(self, display: Surface) -> None:
        self.display_surface: Surface = display
        self.full_surf: Surface = pygame.Surface(Display.SCREEN_RESOLUTION)
        self.start_color: list[int | float] = [255, 255, 255]
        self.end_color: tuple[Literal[38], Literal[101], Literal[189]] = (
            38,
            101,
            189,
        )
        self.day_speed: float = 1.2

    def display(self, dt: float) -> None:
        for index, value in enumerate(self.end_color):
            if self.start_color[index] > value:
                self.start_color[index] -= self.day_speed * dt

        self.full_surf.fill(
            pygame.Color(*(int(channel) for channel in self.start_color))
        )
        self.display_surface.blit(
            self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )


class Drop(BaseSprite):
    def __init__(
        self,
        surf: pygame.Surface,
        pos: tuple[int, int],
        moving: bool,
        groups: Group[Any] | Sequence[Group[Any]],
        z: int,
    ) -> None:
        # general setup
        super().__init__(pos, surf, groups, z)
        self.lifetime: int = random.randint(400, 500)
        self.start_time: int = pygame.time.get_ticks()

        # moving
        self.moving: bool = moving
        if self.moving:
            self.pos: Vector2 = pygame.math.Vector2(self.rect.topleft)
            self.direction: Vector2 = pygame.math.Vector2(-2, 4)
            self.speed: int = random.randint(200, 250)

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
        self, display: pygame.Surface, all_sprites: CameraGroup
    ) -> None:
        self.display_window: Surface = display
        self.all_sprites: CameraGroup = all_sprites
        self.rain_drops: list[Surface] = import_folder(
            "graphics/images/rain/drops"
        )
        self.rain_floor: list[Surface] = import_folder(
            "graphics/images/rain/floor"
        )
        self.floor_w: int
        self.floor_h: int

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
