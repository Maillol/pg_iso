from typing import Type

import pygame
from collections import defaultdict
from dataclasses import dataclass


class Board:

    @staticmethod
    def read_level(level: str):
        """
        Read level and return position of each cube
        """
        positions = []
        z = 0
        y = 0
        for line in level.splitlines():
            if not line:
                z += 1
                y = 0
                continue

            for x, char in enumerate(line):
                positions.append(([x, y, z], char))
            y += 1

        for pos, _ in positions:
            pos[2] = z - pos[2]

        return positions

    def __init__(self, level, items_builder):
        self.items_builder = items_builder
        self.offset_y = 0
        self.group = pygame.sprite.LayeredDirty()
        self.current_case = None
        self.positions = self.read_level(level)
        self.image = pygame.surface.Surface(self.compute_image_size())
        self.image.fill((0, 255, 255))
        self.bg = self.image.copy()
        self.rect = self.image.get_rect()
        self._place_cubes()
        self._reorder_before_drawing = False

    def _place_cubes(self):
        self.positions.sort(
            key=lambda pos: (-pos[0][0], pos[0][1], pos[0][2]))
        self.group.empty()

        for position, type_ in self.positions:
            item = self.items_builder[type_](*position)
            self.group.add(item)

        for item in self.group:
            item.rect.y -= self.offset_y

    def compute_image_size(self):
        max_x = 0
        max_y = 0
        min_x = float('inf')
        min_y = float('inf')
        offset_y = float('inf')
        for _ in range(4):
            offset = max(pos[1] for pos, _ in self.positions)
            for pos, type_ in self.positions:
                pos[0], pos[1] = offset - pos[1], pos[0]
                rect = BoardBox.create_and_place_rect(*pos)
                max_x = max(max_x, rect.right)
                max_y = max(max_y, rect.bottom)
                min_x = min(min_x, rect.left)
                min_y = min(min_y, rect.top)

            offset_y = min(max_y - min_y, offset_y)

        if min_x < 0:
            max_x -= min_x

        if min_y < 0:
            max_y -= min_y

        self.offset_y = min_y
        return max_x, max_y

    def rotate(self):
        """
        Rotate the board.
        """
        items = list(self.group)

        offset = max(item.y for item in items)
        for item in items:
            item.place(
                offset - item.y,
                item.x,
                item.z,
                # Center middle of board to y
                -self.offset_y
            )

        items.sort(
            key=lambda item: (-item.x, item.y, item.z))

        self.group.empty()
        for item in items:
            item.rotate()
            self.group.add(item)

        self.image.fill((0, 255, 255))

    def draw(self, surface):
        if self._reorder_before_drawing:
            items = list(self.group)
            items.sort(key=lambda item: (-item.x, item.y, item.z))
            self.group.empty()
            for item in items:
                self.group.add(item)
            self._reorder_before_drawing = False

        self.group.draw(self.image)
        self.group.clear(self.image, self.bg)
        surface.blit(self.image, self.rect.topleft)

    def get_element(self, x: int, y: int, z: int):
        """
        Get element from position x, y and z

        Return None if element is not found.
        """
        # TODO self.group is sorted, a more efficient way is possible.
        for element in self.group:
            if element.x == x and element.y == y and element.z == z:
                return element

    def get_element_from_screen_position(self, point):
        """
        Get element from x, y screen  position.
        """
        point = (point[0] - self.rect.x, point[1] - self.rect.y)
        cases = []
        for case in self.group:
            if case.rect.collidepoint(point):
                cases.append(case)

        if cases:
            dist_from_case = [
                (pygame.math.Vector2(case.center).distance_to(point), i)
                for i, case
                in enumerate(cases)]

            i = min(dist_from_case)[1]
            cases[i].activate()
            if self.current_case is not None and \
                    self.current_case is not cases[i]:
                self.current_case.deactivate()

            self.current_case = cases[i]
            return self.current_case

    def place_item(self, item, x: int, y: int, z: int) -> None:
        item.place(x, y, z, -self.offset_y)
        self.group.add(item)
        self._reorder_before_drawing = True

    def place_char(self, char: 'Char', x: int, y: int, z: int) -> None:
        char.x, char.y, char.z = x, y, z
        item = self.get_element(x, y, z)
        if not isinstance(item, BoardBox):
            raise TypeError(f'{x} {y} {z} is not a box')

        # TODO if char is already placed
        item.char = char
        item.update()

    def move_char(self, char: 'Char', x: int, y: int, z: int) -> None:
        item = self.get_element(char.x, char.y, char.z)
        if item is not None:
            item.char = None
            item.update()
        self.place_char(char, x, y, z)


class BoardElement(pygame.sprite.DirtySprite):
    """
    A BoardElement is an element of the Board.

    Each element has x, y, z coordinates. In the example bellow,
    the board has 4 BoardElements with coordinates

        z x
        ↑↗
         ↘
          y
             ╱╲
            ╱E1╱╲        E1  (1, 0, 0)
           ╱╲ ╱E2╲       E2  (1, 1, 1)
          ╱E3╲╲  ╱       E3  (0, 0, 0)
          ╲  ╱╲╲╱        E4  (0, 1, 0)
           ╲╱E4╲
            ╲  ╱
             ╲╱

    A BoardElement provides 7 points named a, b, c, d, e, f and g for easy
    cube or boxes isometric drawing.

           a
          ╱│╲
        d╱ │ ╲ b
        │ ╱c╲ │
        │╱   ╲│
       g ╲   ╱ e
          ╲ ╱
           f
    """

    size: int = 120
    rate: float = 0.5
    offset_x: int = int(size / 2)
    offset_y_c: int = int(size * rate)
    offset_y_bd: int = int(offset_y_c / 2)
    offset_y_eg: int = int(offset_y_bd + (size - offset_y_c))

    a = (offset_x, 0)
    b = (size, offset_y_bd)
    c = (offset_x, offset_y_c)
    d = (0, offset_y_bd)
    e = (size, offset_y_eg)
    f = (offset_x, size)
    g = (0, offset_y_eg)

    key_color = (0, 0, 0)

    def __init__(self, x, y, z, color):
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self._orientation = 'sn'
        self.cursor = None
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(self.key_color)
        self.image.set_colorkey(self.key_color)
        self.color = color
        self.rect = self.create_and_place_rect(x, y, z)

        self.center = (self.rect.x + self.offset_x, self.rect.bottom)

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        choices = ('sn', 'ns', 'we', 'ew')
        if value not in choices:
            raise ValueError(f'orientation should be one of {choices}')
        self._orientation = value

    @classmethod
    def create_and_place_rect(cls, x, y, z, y_px=0):
        """
        :param x: board x
        :param y: board y
        :param z: board z
        :param y_px: px correction
        """
        return pygame.rect.Rect(
            (x * cls.offset_x) + (y * cls.offset_x),
            (y * cls.offset_y_bd) - (x * cls.offset_y_bd) - (z * (cls.size - cls.offset_y_c)) + y_px,
            cls.size,
            cls.size)

    def place(self, x, y, z, y_px=0):
        self.x = x
        self.y = y
        self.z = z
        self.rect = self.create_and_place_rect(self.x, self.y, self.z, y_px)
        self.center = (self.rect.x + self.offset_x, self.rect.bottom)
        self.dirty = 1

    def activate(self):
        pass

    def deactivate(self):
        pass

    def rotate(self):
        current_orientation = self._orientation
        if current_orientation == 'ns':
            self._orientation = 'we'
        elif current_orientation == 'we':
            self._orientation = 'sn'
        elif current_orientation == 'sn':
            self._orientation = 'ew'
        else:
            self._orientation = 'ns'

    def update(self):
        pass


class BoardBox(BoardElement):
    """
    This BoardElement can contain a char and can have walls.


     In the example bellow, 4 BoardBox with respectively wall ne, nw,
     sw and se drew.

           a            a
          ╱│            │╲
        d╱ │            │ ╲b          b     d
        │ ╱c╲          ╱c╲ │      ╱c╲╱│     │╲╱c╲
        │╱   ╲        ╱   ╲│     ╱  ╱ │     │ ╲  ╲
       g ╲   ╱ e    g ╲   ╱ e   g╲ │ ╱e     g╲ │ ╱e
          ╲ ╱          ╲ ╱        ╲│╱         ╲│╱
           f            f          f           f
    """

    def __init__(self, x, y, z, color):
        super().__init__(x, y, z, color)

        self.wall_nw = None
        self.wall_ne = None
        self.wall_sw = None
        self.wall_se = None
        self.char = None
        self.highlighted = False

    def draw_ground(self):
        pygame.draw.polygon(
            self.image,
            [min(e + 15, 255) for e in self.color],
            (self.g, self.c, self.e, self.f)
        )

        pygame.draw.polygon(
            self.image,
            self.color,
            (self.g, self.c, self.e, self.f),
            1
        )

    def draw_wall_ne(self):
        pygame.draw.polygon(
            self.image,
            [max(e - 15, 0) for e in self.color],
            (self.a, self.b, self.e, self.c)
        )

    def draw_wall_nw(self):
        pygame.draw.polygon(
            self.image,
            self.color,
            (self.a, self.c, self.g, self.d)
        )

    def draw_wall_sw(self):
        pygame.draw.polygon(
            self.image,
            [max(e - 15, 0) for e in self.color],
            (self.d, self.c, self.f, self.g)
        )

    def draw_wall_se(self):
        pygame.draw.polygon(
            self.image,
            self.color,
            (self.c, self.b, self.e, self.f)
        )

    def draw_char(self):
        self.image.blit(self.char.image, (0, 0))

    def activate(self):
        self.cursor = True
        self.update()

    def deactivate(self):
        self.cursor = None
        self.update()

    def highlight(self):
        self.highlighted = True
        self.update()

    def unhighlight(self):
        self.highlighted = False
        self.update()

    def rotate(self):
        super().rotate()
        self.wall_nw, self.wall_ne, self.wall_se, self.wall_sw = \
            self.wall_sw, self.wall_nw, self.wall_ne, self.wall_se
        self.update()

    def update(self):
        # # DEBUG
        # pygame.draw.polygon(
        #      self.image,
        #      (240, 30, 30),
        #      ((2, 2), (self.size-2, 2), (self.size-2, self.size-2), (2, self.size-2)),
        #      1)
        self.image.fill((0, 2, 3))
        self.image.fill(self.key_color)

        if self.wall_ne:
            self.draw_wall_ne()
        if self.wall_nw:
            self.draw_wall_nw()
        self.draw_ground()

        if self.highlighted:
            pygame.draw.polygon(
                self.image,
                (255, 30, 30),
                (self.g, self.c, self.e, self.f)
            )

        if self.cursor:
            pygame.draw.polygon(
                self.image,
                (30, 100, 230),
                (self.g, self.d, self.d, self.a, self.c),
                2
            )

            pygame.draw.polygon(
                self.image,
                (30, 100, 230),
                (self.a, self.b, self.e, self.c),
                2
            )

        if self.char:
            self.draw_char()

        if self.cursor:
            pygame.draw.polygon(
                self.image,
                (30, 100, 230),
                (self.d, self.c, self.f, self.g),
                2
            )

            pygame.draw.polygon(
                self.image,
                (30, 100, 230),
                (self.c, self.b, self.e, self.f),
                2
            )

        if self.wall_se:
            self.draw_wall_se()
        if self.wall_sw:
            self.draw_wall_sw()
        self.dirty = 1


class Char(BoardElement):

    def __init__(self, x, y, z, color):
        super().__init__(x, y, z, color)
        pygame.draw.polygon(
            self.image,
            self.color,
            ((self.size / 4, 10),
             (self.size / 4 * 3, 10),
             (self.size / 4 * 3, self.size - 30),
             (self.size / 4, self.size - 30))
        )


@dataclass
class BoardEvent:
    board: Board


@dataclass
class ItemSelected(BoardEvent):
    item: BoardElement


class Event:
    def __init__(self):
        self._triggers = defaultdict(list)

    def add_trigger(self, trigger, on_event: Type[BoardEvent]):
        self._triggers[on_event].append(trigger)

    def emit(self, event: BoardEvent):
        for trigger in self._triggers[type(event)]:
            trigger(event)


Event = Event()

