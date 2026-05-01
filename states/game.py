from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING

import pygame
from pytmx.util_pygame import (
    load_pygame,  # pyright: ignore[reportUnknownVariableType]
)

from core.settings import (
    BACKGROUND_COLOUR,
    CHARACTER_ANIMATIONS,
    LAYERS,
    TILE_SIZE,
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

    from pygame.mixer import Sound
    from pygame.sprite import Group
    from pytmx import TiledMap


class Game(BaseState):
    def __init__(self) -> None:
        super().__init__()

        self.all_sprites: CameraGroup = CameraGroup(BaseState.window)
        self.collision_sprites: Group[Any] = pygame.sprite.Group()
        self.tree_sprites: Group[Any] = pygame.sprite.Group()
        self.interaction_sprites: Group[Any] = pygame.sprite.Group()

        self.sky: Sky = Sky(display=BaseState.window)
        self.rain: Rain = Rain(BaseState.window, self.all_sprites)
        self.raining: bool = random.randint(0, 10) > 7
        self.soil_layer: SoilLayer = SoilLayer(
            self.all_sprites, self.collision_sprites, self.raining
        )

        self.player_animation: Animation = Animation(
            {
                animation: import_folder(
                    f"{CHARACTER_ANIMATIONS}/{animation}/"
                )
                for animation in os.listdir(CHARACTER_ANIMATIONS)
            },
            start_status="down_idle",
        )
        self.player: Player = Player(
            (0, 0),
            self.player_animation,
            self.all_sprites,
            self.collision_sprites,
            self.tree_sprites,
            self.interaction_sprites,
            self.soil_layer,
        )
        self.trader: Trader = Trader(self.player)

        self.transition: Transition = Transition(
            self.reset, self.player, BaseState.window
        )
        self.overlay: Overlay = Overlay(self.player, BaseState.window)
        self.tmx_data: TiledMap = load_pygame(
            get_path("../graphics/data/map.tmx")
        )

        music_path = get_path("../audio/bg_music.mp3")
        self.music: Sound = pygame.mixer.Sound(music_path)
        self.music.set_volume(0.5)
        self.music.play(loops=-1)

        interact_sound_path = get_path("../audio/interact.wav")
        self.interact_sound: Sound = pygame.mixer.Sound(interact_sound_path)
        self.interact_sound.set_volume(0.2)

        rain_path: str = get_path("../audio/rain.wav")
        self.rain_sound: Sound = pygame.mixer.Sound(rain_path)
        self.rain_sound.set_volume(0.2)
        self.rain_playing: bool = False

    def on_load(self, reload: bool) -> None:
        # World Map
        BaseSprite(
            (0, 0),
            pygame.image.load(
                "graphics/images/world/ground.png"
            ).convert_alpha(),
            self.all_sprites,
            LAYERS["ground"],
        )

        # fmt: off
        # The pytmx library doesn't have great typing support...

        for obj in self.tmx_data.get_layer_by_name("Player"):                      # pyright: ignore[reportGeneralTypeIssues, reportUnknownVariableType]
            if obj.name == "Start":                                                     # pyright: ignore[reportUnknownMemberType]
                self.player.position.x = obj.x                                          # pyright: ignore[reportUnknownMemberType]
                self.player.position.y = obj.y                                          # pyright: ignore[reportUnknownMemberType]

            elif obj.name == "Bed":                                                     # pyright: ignore[reportUnknownMemberType]
                Interaction(
                    (obj.x, obj.y),                                                 # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                    (obj.width, obj.height),                                       # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                    self.interaction_sprites,
                    LAYERS["main"],
                    obj.name,
                )

            elif obj.name == "Trader":                                                 # pyright: ignore[reportUnknownMemberType]
                Interaction(
                    (obj.x, obj.y),                                                # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                    (obj.width, obj.height),                                      # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                    self.interaction_sprites,
                    LAYERS["main"],
                    obj.name,
                )

        # Collision tiles
        for x, y, _ in self.tmx_data.get_layer_by_name("Collision").tiles():      # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
            BaseSprite(
                (x * TILE_SIZE, y * TILE_SIZE),                                    # pyright: ignore[reportUnknownArgumentType]
                pygame.Surface((TILE_SIZE, TILE_SIZE)),
                self.collision_sprites,
                LAYERS["main"],
            )

        # House furnitures
        for layer in ("HouseFloor", "HouseFurnitureBottom"):
            for x, y, surface in self.tmx_data.get_layer_by_name(                      # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                layer
            ).tiles():                                                                 # pyright: ignore[reportAttributeAccessIssue]
                BaseSprite(
                    (x * TILE_SIZE, y * TILE_SIZE),                                # pyright: ignore[reportUnknownArgumentType]
                    surface,                                                      # pyright: ignore[reportUnknownArgumentType]
                    self.all_sprites,
                    LAYERS["house_bottom"],
                )
        for layer in ("HouseWalls", "HouseFurnitureTop", "Fence"):
            for x, y, surface in self.tmx_data.get_layer_by_name(                      # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                layer
            ).tiles():  # pyright: ignore[reportAttributeAccessIssue]
                BaseSprite(
                    (x * TILE_SIZE, y * TILE_SIZE),                                # pyright: ignore[reportUnknownArgumentType]
                    surface,                                                      # pyright: ignore[reportUnknownArgumentType]
                    (
                        self.all_sprites
                        if layer != "Fence"
                        else [self.all_sprites, self.collision_sprites]
                    ),
                    LAYERS["main"],
                )

        for obj in self.tmx_data.get_layer_by_name("Trees"):                      # pyright: ignore[reportGeneralTypeIssues, reportUnknownVariableType]
            Tree(
                (obj.x, obj.y),                                                    # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                obj.image,                                                        # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                [self.all_sprites, self.collision_sprites, self.tree_sprites],
                LAYERS["main"],
                obj.name,                                                              # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                self.all_sprites,
                self.player,
            )

        # Decorations
        for obj in self.tmx_data.get_layer_by_name("Decoration"):                 # pyright: ignore[reportGeneralTypeIssues, reportUnknownVariableType]
            Wildflower(
                (obj.x, obj.y),                                                    # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                obj.image,                                                        # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                [self.all_sprites, self.collision_sprites],
                LAYERS["main"],
            )

        # Water
        for x, y, surface in self.tmx_data.get_layer_by_name("Water").tiles():    # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
            Water(
                (x * TILE_SIZE, y * TILE_SIZE),                                    # pyright: ignore[reportUnknownArgumentType]
                self.all_sprites,
                LAYERS["water"],
            )

        # fmt: on

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

    def process_update(self, dt: float) -> None:
        self.window.fill(BACKGROUND_COLOUR)

        self.all_sprites.draw(self.player)
        self.overlay.draw(dt=dt)
        self.sky.display(dt=dt)

        if self.player.toggle_active:
            if self.raining:
                self.rain.dim_screen()
            self.trader.update()
        else:
            self.all_sprites.update(dt=dt)
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
