from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal, TypeAlias

import pygame
from pygame.rect import Rect

from core.settings import APPLE_POS, LAYERS, WATER_ANIMATIONS
from core.utils import Animation, Timer, get_path, import_folder

if TYPE_CHECKING:
    from typing import Any

    from pygame import Rect, Surface
    from pygame.mixer import Sound
    from pygame.sprite import Group

    from entities.player import CameraGroup, Player

    GroupParam: TypeAlias = Group[Any] | Sequence[Group[Any]]


class BaseSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: tuple[int, int],
        surf: Surface,
        group: GroupParam,
        z: int,
    ) -> None:
        super().__init__(group)
        self.image: Surface = surf
        self.rect: Rect = self.image.get_rect(topleft=pos)
        self.z: int = z
        self.hitbox: Rect = self.rect.copy().inflate(
            -self.rect.width * 0.2, -self.rect.height * 0.75
        )


class Interaction(BaseSprite):
    def __init__(
        self,
        pos: tuple[int, int],
        size: tuple[int, int],
        groups: GroupParam,
        z: int,
        name: str,
    ) -> None:
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups, z)
        self.name: str = name


class Particle(BaseSprite):
    def __init__(
        self,
        pos: tuple[int, int],
        surf: Surface,
        groups: CameraGroup,
        z: int,
        duration: int = 200,
    ) -> None:
        super().__init__(pos, surf, groups, z)
        self.start_time: int = pygame.time.get_ticks()
        self.duration: int = duration

        # white surface
        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0, 0, 0))
        self.image: Surface = new_surf

    def update(self, dt: float) -> None:
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time > self.duration:
            self.kill()


class Water(BaseSprite):
    def __init__(
        self, pos: tuple[int, int], group: GroupParam, z: int
    ) -> None:
        self.animation: Animation = Animation(
            {"water": [image for image in import_folder(WATER_ANIMATIONS)]},
            start_status="water",
            sprite=self,
        )
        super().__init__(pos, self.animation.get_frame(0), group, z)

    def update(self, dt: float) -> None:
        self.animation.play_status_ip(dt=dt)


class Wildflower(BaseSprite):
    def __init__(
        self,
        pos: tuple[int, int],
        surf: pygame.Surface,
        groups: GroupParam,
        z: int,
    ) -> None:
        super().__init__(pos, surf, groups, z)
        self.hitbox: Rect = self.rect.copy().inflate(
            -20, -self.rect.height * 0.9
        )


class Tree(BaseSprite):
    def __init__(
        self,
        pos: tuple[int, int],
        surf: Surface,
        groups: GroupParam,
        z: int,
        name: Literal["Small", "Large"],
        all_sprites: CameraGroup,
        player: Player,
    ) -> None:
        super().__init__(pos, surf, groups, z)

        self.hitbox: Rect = self.rect.copy().inflate(
            -self.rect.width * 0.2, -self.rect.height * 0.9
        )
        self.player: Player = player

        self.apple_surf: Surface = pygame.image.load(
            "graphics/images/fruit/apple.png"
        )
        self.apple_pos: tuple[tuple[int, int], ...] = APPLE_POS[name]
        self.apple_sprites: Group[Any] = pygame.sprite.Group()
        self.all_sprites: CameraGroup = all_sprites
        self.max_apples: int = 3

        self.invul_timer: Timer = Timer(200)
        self.health: int = 5
        self.stump_surf: Surface = pygame.image.load(
            f"graphics/images/stumps/{name.lower()}.png"
        ).convert_alpha()

        axe_sound_path: str = get_path("../audio/axe.mp3")
        self.axe_sound: Sound = pygame.mixer.Sound(axe_sound_path)

        interact_sound_path = get_path("../audio/interact.wav")
        self.interact_sound: Sound = pygame.mixer.Sound(interact_sound_path)
        self.interact_sound.set_volume(0.2)

        self.create_apple()

    def create_apple(self) -> None:
        for pos in self.apple_pos:
            if len(self.apple_sprites) < self.max_apples:
                if random.randint(0, 10) < 2:
                    x = pos[0] + self.rect.left
                    y = pos[1] + self.rect.top
                    BaseSprite(
                        pos=(x, y),
                        surf=self.apple_surf,
                        group=[self.apple_sprites, self.all_sprites],
                        z=LAYERS["fruit"],
                    )
            else:
                break

    def damage(self) -> None:
        self.axe_sound.play()

        self.health -= 1
        if self.health == 0:
            self.interact_sound.play()
            self.image: Surface = self.stump_surf
            self.rect: Rect = self.image.get_rect(
                midbottom=self.rect.midbottom
            )
            self.hitbox = self.rect.copy().inflate(
                -10, -self.rect.height * 0.95
            )
            for apple in self.apple_sprites:
                apple.kill()
                self.player.inventory.update_item(item="apple")
            self.player.inventory.update_item(item="wood")
            Particle(
                self.rect.topleft,
                self.image,
                self.all_sprites,
                LAYERS["fruit"],
                300,
            )

    def interact(self) -> None:
        if len(self.apple_sprites.sprites()) > 0:
            self.interact_sound.play()
            random_apple = random.choice(self.apple_sprites.sprites())
            Particle(
                pos=random_apple.rect.topleft,
                surf=random_apple.image,
                groups=self.all_sprites,
                z=LAYERS["fruit"],
            )
            self.player.inventory.update_item(item="apple")
            random_apple.kill()
