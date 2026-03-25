from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING

import pygame
import pytmx

from core.settings import (
    BACKGROUND_COLOUR,
    CHARACTER_ANIMATIONS,
    LAYERS,
    TILE_SIZE,
    Display,
)
from core.utils import Animation, get_path, import_folder
from entities.overlay import Overlay
from entities.player import CameraGroup, Player
from entities.sky import Rain, Sky
from entities.soil import SoilLayer
from entities.sprites import (
    BaseSprite,
    Interaction,
    Particle,
    Tree,
    Water,
    Wildflower,
)
from entities.trader import Trader
from entities.transition import Transition
from states.base import BaseState

if TYPE_CHECKING:
    from typing import Any

    from pygame.sprite import Group


class Game(BaseState):
    def __init__(self) -> None:
        super().__init__()

        self.all_sprites: CameraGroup = CameraGroup(BaseState.window)  # type: ignore
        self.collision_sprites: Group[Any] = pygame.sprite.Group()
        self.tree_sprites: Group[Any] = pygame.sprite.Group()
        self.interaction_sprites: Group[Any] = pygame.sprite.Group()

        self.sky: Sky = Sky(display=BaseState.window)
        self.rain: Rain = Rain(BaseState.window, self.all_sprites)  # type: ignore
        self.raining: bool = random.randint(0, 10) > 7
        self.soil_layer: SoilLayer = SoilLayer(
            self.all_sprites, self.collision_sprites, self.raining
        )

        self.player_animation = Animation(
            {
                animation: import_folder(
                    f"{CHARACTER_ANIMATIONS}/{animation}/"
                )
                for animation in os.listdir(CHARACTER_ANIMATIONS)
            }
        )
        self.player_animation.set_status("down_idle")
        self.player = Player(
            (0, 0),
            self.player_animation,
            self.all_sprites,
            self.collision_sprites,
            self.tree_sprites,
            self.interaction_sprites,
            self.soil_layer,
        )
        self.trader = Trader(self.player)

        self.transition = Transition(self.reset, self.player, BaseState.window)
        self.overlay = Overlay(self.player, BaseState.window)  # type: ignore
        self.tmx_data = pytmx.util_pygame.load_pygame(
            get_path("../graphics/data/map.tmx")
        )

        music_path = get_path("../audio/bg_music.mp3")
        self.music = pygame.mixer.Sound(music_path)
        self.music.set_volume(0.5)
        self.music.play(loops=-1)

        interact_sound_path = get_path("../audio/interact.wav")
        self.interact_sound = pygame.mixer.Sound(interact_sound_path)
        self.interact_sound.set_volume(0.2)

        rain_path = get_path("../audio/rain.wav")
        self.rain_sound = pygame.mixer.Sound(rain_path)
        self.rain_sound.set_volume(0.2)
        self.rain_playing = False

    def setup(self) -> None:
        # World Map
        BaseSprite(
            (0, 0),
            pygame.image.load(
                "graphics/images/world/ground.png"
            ).convert_alpha(),
            self.all_sprites,
            LAYERS["ground"],
        )

        for obj in self.tmx_data.get_layer_by_name("Player"):
            if obj.name == "Start":
                self.player.position.x = obj.x
                self.player.position.y = obj.y

            elif obj.name == "Bed":
                Interaction(
                    (obj.x, obj.y),
                    (obj.width, obj.height),
                    self.interaction_sprites,
                    LAYERS["main"],
                    obj.name,
                )

            elif obj.name == "Trader":
                Interaction(
                    (obj.x, obj.y),
                    (obj.width, obj.height),
                    self.interaction_sprites,
                    LAYERS["main"],
                    obj.name,
                )

        # Collision tiles
        for x, y, _ in self.tmx_data.get_layer_by_name("Collision").tiles():
            BaseSprite(
                (x * TILE_SIZE, y * TILE_SIZE),
                pygame.Surface((TILE_SIZE, TILE_SIZE)),
                self.collision_sprites,
                LAYERS["main"],
            )

        # House furnitures
        for layer in ("HouseFloor", "HouseFurnitureBottom"):
            for x, y, surface in self.tmx_data.get_layer_by_name(
                layer
            ).tiles():
                BaseSprite(
                    (x * TILE_SIZE, y * TILE_SIZE),
                    surface,
                    self.all_sprites,
                    LAYERS["house_bottom"],
                )
        for layer in ("HouseWalls", "HouseFurnitureTop", "Fence"):
            for x, y, surface in self.tmx_data.get_layer_by_name(
                layer
            ).tiles():
                BaseSprite(
                    (x * TILE_SIZE, y * TILE_SIZE),
                    surface,
                    (
                        self.all_sprites
                        if layer != "Fence"
                        else [self.all_sprites, self.collision_sprites]
                    ),
                    LAYERS["main"],
                )

        for obj in self.tmx_data.get_layer_by_name("Trees"):
            Tree(
                (obj.x, obj.y),
                obj.image,
                [self.all_sprites, self.collision_sprites, self.tree_sprites],
                LAYERS["main"],
                obj.name,
                self.all_sprites,
                self.player,
            )

        # Decorations
        for obj in self.tmx_data.get_layer_by_name("Decoration"):
            Wildflower(
                (obj.x, obj.y),
                obj.image,
                [self.all_sprites, self.collision_sprites],
                LAYERS["main"],
            )

        # Water
        for x, y, surface in self.tmx_data.get_layer_by_name("Water").tiles():
            Water(
                (x * TILE_SIZE, y * TILE_SIZE),
                self.all_sprites,
                LAYERS["water"],
            )

    def plant_collision(self) -> None:
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(
                    self.player.hitbox
                ):
                    self.interact_sound.play()
                    self.player.inventory.update_item(2, plant.plant_type)
                    plant.kill()
                    Particle(
                        plant.rect.topleft,
                        plant.image,
                        self.all_sprites,
                        z=LAYERS["main"],
                    )

                    x = plant.rect.centerx // TILE_SIZE
                    y = plant.rect.centery // TILE_SIZE
                    self.soil_layer.grid[y][x].remove("P")

    def reset(self) -> None:
        self.soil_layer.update_plants()

        self.raining = random.randint(0, 10) > 7
        self.soil_layer.raining = self.raining

        if self.raining:
            self.soil_layer.water_all()
        else:
            self.soil_layer.remove_water()

        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_apple()

        self.sky.start_color = [255, 255, 255]

    def run(self) -> None:
        while True:
            dt = self.clock.tick(Display.FPS) / 1000
            self.window.fill(BACKGROUND_COLOUR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.manager.exit_game()

            self.all_sprites.draw(self.player)
            self.overlay.draw(dt=dt)
            self.sky.display(dt=dt)

            if self.player.toggle_active:
                if self.raining:
                    self.rain.dim_screen()
                self.trader.update()
            else:
                self.all_sprites.update(dt)
                self.plant_collision()

                if self.raining:
                    if not self.rain_playing:
                        self.rain_playing = True
                        self.rain_sound.play(-1)
                    self.rain.update()
                else:
                    self.rain_playing = False
                    self.rain_sound.stop()

                if self.player.sleep:
                    self.transition.run()

            pygame.display.update()


def hook(**kwargs) -> None:
    Game.manager.load_states(Game, **kwargs)
