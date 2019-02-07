from collections.abc import MutableMapping
from dataclasses import dataclass
from textwrap import dedent

import pygame

from .board import INDEX, Board, BoardBox, Char, CharSelected, ItemSelected, Event, KeyEvent
from .algo import compute_path


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
BOARD_WIDTH = SCREEN_WIDTH
BOARD_HEIGHT = SCREEN_HEIGHT
BOARD_SIZE = (BOARD_WIDTH, BOARD_HEIGHT)
FPS = 30


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

background = pygame.Surface(BOARD_SIZE)
background.fill((255, 255, 255))  # fill white

MAINLOOP = True


def get_board():

    def ground_without_wall(x, y, z):
        box = BoardBox(x, y, z, (23, 76, 96))
        box.update()
        return box

    def ground_with_x_wall(x, y, z):
        box = BoardBox(x, y, z, (23, 76, 96))
        box.wall_nw = True
        box.update()
        return box

    def ground_with_y_wall(x, y, z):
        box = BoardBox(x, y, z, (23, 76, 96))
        box.wall_ne = True
        box.update()
        return box

    def ground_with_xy_wall(x, y, z):
        box = BoardBox(x, y, z, (23, 76, 96))
        box.wall_nw = True
        box.wall_ne = True
        box.update()
        return box

    translate_map = {
        'b': ground_with_xy_wall,
        'x': ground_with_x_wall,
        'y': ground_with_y_wall,
        'w': ground_without_wall,
    }

    level = dedent("""
    yxbw
    wwyw
    wxxw
    wwww
    wwww
    """)

    return Board(
        level,
        translate_map
    )


board = get_board()
board.place_char(
    Char(0, 0, 0, (212, 23, 132)),
    0, 0, 0
)


board.place_char(
    Char(0, 0, 0, (124, 12, 90)),
    1, 2, 0
)


def compute_area(x, y, z, nb_steps, out=None):
    if out is None:
        out = []

    if not nb_steps:
        return out

    item = board.get_element(x, y, z)
    next_item = board.get_element(x + 1, y, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_sw is None and \
            item.wall_ne is None:
        out.append(next_item)
        compute_area(x + 1, y, z, nb_steps - 1, out)

    next_item = board.get_element(x - 1, y, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_ne is None and \
            item.wall_sw is None:
        out.append(next_item)
        compute_area(x - 1, y, z, nb_steps - 1, out)

    next_item = board.get_element(x, y + 1, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_nw is None and \
            item.wall_se is None:
        out.append(next_item)
        compute_area(x, y + 1, z, nb_steps - 1, out)

    next_item = board.get_element(x, y - 1, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_se is None and \
            item.wall_nw is None:
        out.append(next_item)
        compute_area(x, y - 1, z, nb_steps - 1, out)

    return out


class StateContext(MutableMapping):

    def __init__(self, first_state_cls):
        self._state = first_state_cls(self)
        self._data = {}

    def switch_state(self, state_cls):
        self._state = state_cls(self)

    def on_item_selected(self, event: ItemSelected):
        self._state.on_item_selected(event)

    def on_char_selected(self, event: CharSelected):
        self._state.on_char_selected(event)

    def on_key_pressed(self, event: KeyEvent):
        self._state.on_attack_selected(event)

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class State:

    def __init__(self, ctx):
        self.ctx = ctx

    def on_item_selected(self, event: ItemSelected):
        pass

    def on_char_selected(self, event: CharSelected):
        pass

    def on_attack_selected(self, event: 'AttackEvent'):
        pass


class ViewState(State):

    def on_char_selected(self, event: CharSelected):
        for box in list(INDEX.highlighted):
            box.unhighlight()

        for box in compute_area(event.char.x,
                                event.char.y,
                                event.char.z, 2):
            box.highlight()

        self.ctx['char_to_move'] = event.char
        self.ctx.switch_state(MoveState)

    def on_item_selected(self, event: ItemSelected):
        for box in list(INDEX.highlighted):
            box.unhighlight()
        self.ctx.switch_state(ViewState)

    def on_attack_selected(self, event):
        self.ctx.switch_state(ViewState)


class MoveState(State):

    def on_char_selected(self, event: CharSelected):
        for box in list(INDEX.highlighted):
            box.unhighlight()

        for box in compute_area(event.char.x,
                                event.char.y,
                                event.char.z, 2):
            box.highlight()

        self.ctx['char_to_move'] = event.char
        self.ctx.switch_state(MoveState)

    def on_item_selected(self, event: ItemSelected):
        char_to_move = self.ctx['char_to_move']
        box = event.board.get_element(
             char_to_move.x,
             char_to_move.y,
             char_to_move.z)

        if event.item in INDEX.highlighted:
            box.char = None
            box.update()

            event.board.place_char(
                char_to_move,
                event.item.x,
                event.item.y,
                event.item.z)

        for box in list(INDEX.highlighted):
            box.unhighlight()

        self.ctx.switch_state(ViewState)

    def on_attack_selected(self, event):
        for box in list(INDEX.highlighted):
            box.unhighlight()
        self.ctx.switch_state(AttackState)


class AttackState(State):

    def on_char_selected(self, event: CharSelected):
        for box in list(INDEX.highlighted):
            box.unhighlight()

        for pos in compute_path(
                self.ctx['char_to_move'].x,
                self.ctx['char_to_move'].y,
                event.char.x,
                event.char.y):
            box = event.board.get_element(*pos, event.char.z)
            if box is None:
                box.highlight()

        self.ctx.switch_state(AttackState)

    def on_item_selected(self, event: ItemSelected):
        for box in list(INDEX.highlighted):
            box.unhighlight()
        for pos in compute_path(
                self.ctx['char_to_move'].x,
                self.ctx['char_to_move'].y,
                event.item.x,
                event.item.y):
            box = event.board.get_element(pos[0], pos[1], self.ctx['char_to_move'].z)
            if box is not None:
                box.highlight()

        self.ctx.switch_state(AttackState)

    def on_attack_selected(self, event):
        for box in list(INDEX.highlighted):
            box.unhighlight()

        char = self.ctx['char_to_move']
        for box in compute_area(char.x,
                                char.y,
                                char.z, 2):
            box.highlight()

        self.ctx.switch_state(MoveState)



STATE = StateContext(ViewState)
Event.add_trigger(STATE.on_item_selected, ItemSelected)
Event.add_trigger(STATE.on_char_selected, CharSelected)
Event.add_trigger(STATE.on_key_pressed, KeyEvent)

clock = pygame.time.Clock()


while MAINLOOP:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            MAINLOOP = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                MAINLOOP = False
            elif event.key == pygame.K_r:
                board.rotate()
            elif event.key == pygame.K_a:
                Event.emit(KeyEvent(board, 'a'))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                item = board.get_element_from_screen_position(event.pos)
                if item is not None:
                    if item.char is not None:
                        Event.emit(CharSelected(board, item))
                    else:
                        Event.emit(ItemSelected(board, item))

    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_UP]:
        board.rect.y += 10
    elif pressed[pygame.K_DOWN]:
        board.rect.y -= 10
    if pressed[pygame.K_LEFT]:
        board.rect.x += 10
    elif pressed[pygame.K_RIGHT]:
        board.rect.x -= 10

    position = pygame.mouse.get_pos()
    if position[0] < 40:
        board.rect.x += 10
    elif position[0] > SCREEN_WIDTH - 40:
        board.rect.x -= 10
    if position[1] < 40:
        board.rect.y += 10
    elif position[1] > SCREEN_HEIGHT - 40:
        board.rect.y -= 10

    board.get_element_from_screen_position(position)

    screen.blit(background, (0, 0))
    board.draw(screen)
    # pygame.display.set_caption(f"[FPS]: {pygame.mouse.get_pos()} {clock.get_fps():.2f}")

    clock.tick(FPS)
    pygame.display.flip()  # flip the screen
