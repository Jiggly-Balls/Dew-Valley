from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import (
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import pygame

T = TypeVar("T")


@dataclass
class TextStyle:
    text_colour: Union[int, str, Sequence[int]]
    text_bg_colour: Optional[Union[int, str, Sequence[int]]] = None
    bold: bool = False
    italic: bool = False
    font_name: Optional[Union[str, bytes]] = None

    def copy(self) -> TextStyle:
        return TextStyle(
            text_colour=self.text_colour,
            text_bg_colour=self.text_bg_colour,
            bold=self.bold,
            italic=self.italic,
            font_name=self.font_name,
        )


class Text:
    __slots__ = ("window", "center", "text_style", "text_size", "font", "rect")

    def __init__(
        self,
        window: pygame.Surface,
        text_style: TextStyle,
        text_size: int,
        center: Tuple[int, int],
    ) -> None:
        self.window = window
        self.center = center
        self.text_style = text_style

        if self.text_style.font_name:
            self.font = pygame.font.Font(self.text_style.font_name, text_size)
        else:
            self.font = pygame.font.SysFont(
                self.text_style.font_name,
                text_size,
                self.text_style.bold,
                self.text_style.italic,
            )

        self.rect: Optional[pygame.Rect] = None

    def render(
        self,
        text: str,
        colour: Optional[Union[int, str, Sequence[int]]] = None,
        text_bg_colour: Optional[Union[int, str, Sequence[int]]] = None,
        antialias: bool = True,
    ) -> None:
        rendered_text = self.font.render(
            text,
            antialias,
            colour or self.text_style.text_colour,
            text_bg_colour or self.text_style.text_bg_colour,
        )
        if self.rect is None:
            self.rect = rendered_text.get_rect(center=self.center)
        self.window.blit(rendered_text, self.rect)


class Animation:
    def __init__(
        self,
        frames: Dict[str, List[pygame.Surface]],
        *,
        start_status: Optional[str] = None,
        sprite: Optional[pygame.sprite.Sprite] = None,
        speed: int = 4,
        ignore_invalid_state: bool = True,
    ) -> None:
        self.frames = frames
        self.sprite = sprite
        self.speed = speed
        self.ignore_invalid_state = ignore_invalid_state

        self.status: Optional[str] = None
        self.current_frame = 0
        self.max_frames = 0
        if start_status is not None:
            self.set_status(start_status)

    def get_frame(self, frame: int) -> pygame.Surface:
        return self.frames[self.status][frame]

    def set_status(self, animation: str) -> None:
        if not self.ignore_invalid_state:
            assert animation in self.frames, (
                f"{animation} is not present in list of animations: {self.frames.keys()}"
            )

        if animation in self.frames:
            # if animation != self.status:
            self.status = animation
            # self.current_frame = 0
            self.max_frames = len(self.frames[self.status]) - 1

    def play_status(self, dt: int) -> pygame.Surface:
        if not self.ignore_invalid_state:
            assert self.ignore_invalid_state or self.status is not None, (
                "No animation state has been set to run"
            )

        self.current_frame += self.speed * dt
        if self.current_frame > self.max_frames:
            self.current_frame = 0

        return self.frames[self.status][round(self.current_frame)]

    def play_status_ip(self, dt: int) -> None:
        assert self.sprite is not None, (
            "No sprite has been passed to play the status in-place."
        )
        self.current_frame += self.speed * dt
        if self.current_frame > self.max_frames:
            self.current_frame = 0
        self.sprite.image = self.frames[self.status][round(self.current_frame)]


class Timer:
    def __init__(self, duration: int, func: Optional[Callable] = None) -> None:
        self.duration = duration
        self.func = func
        self.start_time = 0
        self.active = False

    def activate(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.start_time = 0

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time >= self.duration:
            if self.func and self.start_time != 0:
                self.func()
            self.deactivate()


class ItemIterator(Generic[T]):
    def __init__(self, seq: List[T]) -> None:
        self.seq = seq
        self.index = 0
        self.selected = seq[0]
        self.max_index = len(seq) - 1
        self.inv: Dict[T, int] = {key: 1 for key in seq}

    def next(self) -> None:
        self.index += 1
        if self.index > self.max_index:
            self.index = 0
        self.selected = self.seq[self.index]

    def previous(self) -> None:
        self.index -= 1
        if self.index < 0:
            self.index = self.max_index
        self.selected = self.seq[self.index]

    def append(self, element: T) -> None:
        self.seq.append(element)
        self.inv[element] = 0
        self.max_index += 1

    def remove(self, element: T) -> None:
        self.seq.remove(element)
        del self.inv[element]
        self.max_index -= 1

    def update_item(self, amount: int = 1, item: Optional[T] = None) -> None:
        item = item or self.selected
        if item not in self.seq:
            self.append(item)
        self.inv[item] += amount

    def set_item(self, item: T, value: int) -> None:
        self.inv[item] = value
        if item not in self.seq:
            self.append(item)


def import_folder(path: str) -> List[pygame.Surface]:
    surface_list = []
    for folder, _, image_files in os.walk(path):
        for image in image_files:
            full_path = f"{folder}/{image}"
            surface = pygame.image.load(full_path).convert_alpha()
            surface_list.append(surface)
    return surface_list


def import_folder_dict(path: str) -> dict:
    surface_dict = {}

    for _, __, img_files in os.walk(path):
        for image in img_files:
            full_path = path + "/" + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[image.split(".")[0]] = image_surf

    return surface_dict


def get_path(path: str) -> str:
    absolute_path = os.path.dirname(__file__)
    return os.path.join(absolute_path, path)
