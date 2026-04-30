from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core.settings import BG_COLOUR, COIN_ANIMATIONS, Display
from core.utils import Animation, get_path, import_folder, import_folder_dict
from entities.player import Player

if TYPE_CHECKING:
    from pygame import Font, Rect, Surface


class Overlay:
    def __init__(self, player: Player, display: pygame.Surface) -> None:
        self.display_surface: Surface = display
        self.player: Player = player
        self.font: Font = pygame.font.Font(
            get_path(r"..\graphics\LycheeSoda.ttf"),
            30,
        )

        self.coin_animation: Animation = Animation(
            {"coin": [image for image in import_folder(COIN_ANIMATIONS)]},
            start_status="coin",
            speed=10,
        )

        overlay_path = get_path("../graphics/images/overlay/")
        fruit_path = get_path("../graphics/images/fruit")

        self.tools_surf: dict[str, Surface] = import_folder_dict(
            get_path(overlay_path)
        )
        self.tools_surf["apple"] = pygame.image.load(
            f"{fruit_path}/apple.png"
        ).convert_alpha()

        self.all_tool_rect: Rect = self.tools_surf[
            self.player.inventory.selected
        ].get_rect(
            center=(
                Display.SCREEN_RESOLUTION[0] / 1.2,
                Display.SCREEN_RESOLUTION[1] / 1.3,
            )
        )

    def draw(self, dt: float) -> None:
        tool_surf: Surface = self.tools_surf[self.player.inventory.selected]
        tool_rect = tool_surf.get_rect(
            center=(
                Display.SCREEN_RESOLUTION[0] / 1.2,
                Display.SCREEN_RESOLUTION[1] / 1.3,
            )
        )

        coin_surf = self.coin_animation.play_status(dt=dt)
        coin_rect = coin_surf.get_rect(
            center=(
                Display.SCREEN_RESOLUTION[0] / 1.25,
                Display.SCREEN_RESOLUTION[1] / 5,
            )
        )

        inv_amount_surf = self.font.render(
            f"x{self.player.inventory.inv[self.player.inventory.selected]}",
            False,
            "white",
        )
        inv_amount_rect = inv_amount_surf.get_rect(
            center=(
                Display.SCREEN_RESOLUTION[0] / 1.2,
                Display.SCREEN_RESOLUTION[1] / 1.17,
            )
        )

        money_surf = self.font.render(f"{self.player.money}", False, "white")
        money_rect = money_surf.get_rect(
            center=(
                Display.SCREEN_RESOLUTION[0] / 1.2,
                Display.SCREEN_RESOLUTION[1] / 5,
            )
        )

        money_bg_surf = pygame.Surface(coin_rect.topleft)
        money_bg_surf.fill(BG_COLOUR)
        money_bg_rect = money_bg_surf.get_rect(
            topleft=coin_rect.topleft
        ).inflate(20, 15)
        self.display_surface.blit(
            money_bg_surf,
            money_bg_rect,
            money_rect.inflate(350, 90),
            special_flags=pygame.BLEND_RGBA_MULT,
        )

        tool_bg_surf = pygame.Surface(self.all_tool_rect.topleft)
        tool_bg_surf.fill(BG_COLOUR)
        tool_bg_rect = money_bg_surf.get_rect(
            topleft=self.all_tool_rect.topleft
        ).inflate(100, 100)
        self.display_surface.blit(
            tool_bg_surf,
            tool_bg_rect,
            self.all_tool_rect.inflate(300, 400),
            special_flags=pygame.BLEND_RGBA_MULT,
        )

        self.display_surface.blit(inv_amount_surf, inv_amount_rect)
        self.display_surface.blit(money_surf, money_rect)
        self.display_surface.blit(tool_surf, tool_rect)
        self.display_surface.blit(coin_surf, coin_rect)
