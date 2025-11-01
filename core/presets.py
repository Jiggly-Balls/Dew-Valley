import pygame

from core.utils import TextStyle, get_path

pygame.font.init()
# def_font = pygame.font.SysFont("D:\Python Projects\Pygame Stuff\Dew Valley\graphics\LycheeSoda.ttf")
overlay_style = TextStyle(
    "white", font_name=get_path(r"..\graphics\LycheeSoda.ttf")
)
