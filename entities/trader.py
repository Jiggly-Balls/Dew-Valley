import pygame

from entities.player import Player
from core.settings import Display, SALE_PRICES, PURCHASE_PRICES
from core.utils import Timer, get_path


class Trader:
    def __init__(self, player: Player) -> None:
        # general setup
        self.player = player
        self.display_surface = pygame.display.get_surface()
        font_path = get_path("../graphics/LycheeSoda.ttf")
        self.font = pygame.font.Font(font_path, 30)

        # options
        self.width = 400
        self.space = 10
        self.padding = 8

        # entries
        self.options = ["wood", "apple", "corn", "tomato", "corn", "tomato"]
        self.sell_border = 3
        self.setup()

        # movement
        self.index = 0
        self.timer = Timer(200)

    def setup(self) -> None:
        # create text surfaces
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            text_surf = self.font.render(item, False, "Black")
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = Display.SCREEN_RESOLUTION[1] / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(
            Display.SCREEN_RESOLUTION[0] / 2 - self.width / 2,
            self.menu_top,
            self.width,
            self.total_height,
        )

        # buy / sell surface
        self.buy_text = self.font.render("buy", False, "Black")
        self.sell_text = self.font.render("sell", False, "Black")

    def input(self) -> None:
        keys = pygame.key.get_pressed()
        self.timer.update()

        if keys[pygame.K_ESCAPE]:
            self.player.toggle_active = not self.player.toggle_active

        if not self.timer.active:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.timer.activate()
                self.index -= 1
                if self.index < 0:
                    self.index = len(self.options) - 1

            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.timer.activate()
                self.index += 1
                if self.index > len(self.options) - 1:
                    self.index = 0

            if keys[pygame.K_f]:
                self.timer.activate()

                # get item
                current_item = self.options[self.index]

                # sell
                if self.index <= self.sell_border:
                    if self.player.inventory.inv[current_item] > 0:
                        self.player.inventory.update_item(-1, current_item)
                        self.player.money += SALE_PRICES[current_item]
                # buy
                else:
                    seed_price = PURCHASE_PRICES[current_item]
                    if self.player.money >= seed_price:
                        self.player.inventory.update_item(1, current_item)
                        self.player.money -= PURCHASE_PRICES[current_item]

        if self.index < 0:
            self.index = len(self.options) - 1
        if self.index > len(self.options) - 1:
            self.index = 0

    def show_entry(
        self, text_surf: pygame.Surface, amount: int, top: int, selected: str
    ) -> None:
        # background
        bg_rect = pygame.Rect(
            self.main_rect.left,
            top,
            self.width,
            text_surf.get_height() + self.padding * 2,
        )
        pygame.draw.rect(self.display_surface, "White", bg_rect, 0, 4)

        # text
        text_rect = text_surf.get_rect(
            midleft=(self.main_rect.left + 20, bg_rect.centery)
        )
        self.display_surface.blit(text_surf, text_rect)

        # amount
        # if self.index > self.sell_border:
        amount_surf = self.font.render(str(amount), False, "Black")
        amount_rect = amount_surf.get_rect(
            midright=(self.main_rect.right - 20, bg_rect.centery)
        )
        self.display_surface.blit(amount_surf, amount_rect)

        # selected
        if selected:
            pygame.draw.rect(self.display_surface, "black", bg_rect, 4, 4)
            if self.index <= self.sell_border:  # buy
                buy_pos_rect = self.sell_text.get_rect(
                    midleft=(self.main_rect.left + 150, bg_rect.centery)
                )
                self.display_surface.blit(self.sell_text, buy_pos_rect)
            else:  # sell
                sell_pos_rect = self.buy_text.get_rect(
                    midleft=(self.main_rect.left + 150, bg_rect.centery)
                )
                self.display_surface.blit(self.buy_text, sell_pos_rect)

    def update(self) -> None:
        self.input()

        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (
                text_surf.get_height() + (self.padding * 2) + self.space
            )

            amount_list = [self.player.inventory.inv[i] for i in self.options]
            amount = amount_list[text_index]
            if text_index > self.sell_border:
                amount = ""
            self.show_entry(text_surf, amount, top, self.index == text_index)
