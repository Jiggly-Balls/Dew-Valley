from typing import Dict, Tuple

import pygame
from pygame.sprite import Group

from core.settings import LAYERS, PLAYER_TOOL_OFFSET, Display
from core.utils import Animation, ItemIterator, Timer, get_path
from entities.sprites import BaseSprite


class Player(BaseSprite):
    def __init__(
        self,
        pos: Tuple[int, int],
        animation: Animation,
        group: Group,
        collison_sprites: Group,
        tree_sprites: Group,
        interaction_sprites: Group,
        soil_layer: Group,
    ) -> None:
        super().__init__(pos, animation.get_frame(0), group, LAYERS["main"])
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.copy().inflate((-126, -70))

        self.collision_sprites = collison_sprites
        self.tree_sprites = tree_sprites
        self.interaction_sprites = interaction_sprites
        self.soil_layer = soil_layer

        self.animation = animation
        self.sleep = False

        self.speed = 300
        self.position = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2()
        self.direction_str = "down"

        self.inventory = ItemIterator(
            ["hoe", "axe", "water", "corn", "tomato", "wood", "apple"]
        )
        self.inventory.set_item("corn", 5)
        self.inventory.set_item("tomato", 5)
        self.money = 50

        self.toggle_active = False
        self.timers: Dict[str, Timer] = {
            "interact": Timer(50, self.interact),
            "tool_use": Timer(500, self.use_tool),
            "tool_switch": Timer(200),
            "seed_use": Timer(50, self.use_seed),
        }

        watering_sound_path = get_path("../audio/water.mp3")
        self.watering = pygame.mixer.Sound(watering_sound_path)
        self.watering.set_volume(0.2)

    def get_target_pos(self) -> pygame.Vector2:
        return self.rect.center + PLAYER_TOOL_OFFSET[self.direction_str]

    def use_tool(self) -> None:
        if self.inventory.selected == "hoe":
            self.soil_layer.get_hit(self.get_target_pos())

        elif self.inventory.selected == "axe":
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.get_target_pos()):
                    tree.damage()

        elif self.inventory.selected == "water":
            self.watering.play()
            self.soil_layer.water(self.get_target_pos())

        elif self.inventory.selected in ("corn", "tomato"):
            self.timers["seed_use"].activate()
            self.direction = pygame.math.Vector2()

    def use_seed(self):
        if self.inventory.inv[self.inventory.selected] > 0:
            self.soil_layer.plant_seed(
                self.get_target_pos(), self.inventory.selected, self
            )

    def interact(self) -> None:
        interacted = False

        if not interacted:
            # Grabbing apples
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.get_target_pos()):
                    tree.interact()
                    interacted = True

        if not interacted:
            # Bed / trader
            collided_interaction_sprite = pygame.sprite.spritecollide(
                self, self.interaction_sprites, False
            )
            if collided_interaction_sprite:
                if collided_interaction_sprite[0].name == "Trader":
                    self.toggle_active = not self.toggle_active

                elif collided_interaction_sprite[0].name == "Bed":
                    self.direction_str = "left"
                    self.animation.set_status("idle_left")
                    self.sleep = True

    def input(self, dt: int) -> None:
        # User input system
        if not self.timers["tool_use"].active and not self.sleep:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.direction.y = -1
                self.direction_str = "up"
                self.animation.set_status(self.direction_str)
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.direction_str = "down"
                self.animation.set_status(self.direction_str)
            else:
                self.direction.y = 0

            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.direction_str = "left"
                self.animation.set_status(self.direction_str)
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.direction_str = "right"
                self.animation.set_status(self.direction_str)
            else:
                self.direction.x = 0

            if self.direction.length() != 0.0:
                self.direction.normalize_ip()
            else:
                self.animation.set_status(f"{self.direction_str}_idle")

            # Interactions / using tools
            if keys[pygame.K_f]:
                self.timers["interact"].activate()

            if keys[pygame.K_SPACE]:
                self.timers["tool_use"].activate()
                self.direction = pygame.math.Vector2()

            elif keys[pygame.K_e] and not self.timers["tool_switch"].active:
                self.timers["tool_switch"].activate()
                self.inventory.next()

            elif keys[pygame.K_q] and not self.timers["tool_switch"].active:
                self.timers["tool_switch"].activate()
                self.inventory.previous()

        if self.timers["tool_use"].active:
            self.animation.set_status(
                f"{self.direction_str}_{self.inventory.selected}"
            )

        # Updating the player's postition
        # Horizontal movement
        self.position.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.position.x)
        self.rect.centerx = self.hitbox.centerx
        self.collide(horizontal=True)

        # Vertical movement
        self.position.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.position.y)
        self.rect.centery = self.hitbox.centery
        self.collide(horizontal=False)

    def collide(self, *, horizontal: bool) -> None:
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, "hitbox"):
                if sprite.hitbox.colliderect(self.hitbox):
                    if horizontal:
                        if self.direction.x > 0:  # moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0:  # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.position.x = self.hitbox.centerx

                    else:
                        if self.direction.y > 0:  # moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0:  # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.position.y = self.hitbox.centery

    def update_timers(self) -> None:
        for timer in self.timers.values():
            timer.update()

    def update(self, dt: int) -> None:
        self.input(dt=dt)
        # self.use_tool()
        self.update_timers()
        self.get_target_pos()
        self.image = self.animation.play_status(dt=dt)


class CameraGroup(Group):
    def __init__(self, window: pygame.Surface):
        super().__init__()
        self.window = window
        self.offset = pygame.math.Vector2()

    def draw(self, player: Player) -> None:
        self.offset.x = player.rect.centerx - Display.SCREEN_RESOLUTION[0] / 2
        self.offset.y = player.rect.centery - Display.SCREEN_RESOLUTION[1] / 2

        for layer in LAYERS.values():
            for sprite in sorted(
                self.sprites(), key=lambda sprite: sprite.rect.centery
            ):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.window.blit(sprite.image, offset_rect)
