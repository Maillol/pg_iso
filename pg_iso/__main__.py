from textwrap import dedent

import pygame

from .board import Board, BoardBox, Char, ItemSelected, Event


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


def compute_path(x, y, z, nb_steps, out=None):
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
        compute_path(x + 1, y, z, nb_steps - 1, out)

    next_item = board.get_element(x - 1, y, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_ne is None and \
            item.wall_sw is None:
        out.append(next_item)
        compute_path(x - 1, y, z, nb_steps - 1, out)

    next_item = board.get_element(x, y + 1, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_nw is None and \
            item.wall_se is None:
        out.append(next_item)
        compute_path(x, y + 1, z, nb_steps - 1, out)

    next_item = board.get_element(x, y - 1, z)
    if next_item is not None and \
            next_item.char is None and \
            next_item.wall_se is None and \
            item.wall_nw is None:
        out.append(next_item)
        compute_path(x, y - 1, z, nb_steps - 1, out)

    return out


class OnItemSelected:
    def __init__(self):
        self._char_selected = None
        self._accessible_boxes = None

    def __call__(self, event: ItemSelected):
        item = event.item
        if item.char:
            self._char_selected = item.char
            if self._accessible_boxes is not None:
                for box in self._accessible_boxes:
                    box.unhighlight()

            x, y, z = item.x, item.y, item.z
            self._accessible_boxes = compute_path(x, y, z, 2)
            for box in self._accessible_boxes :
                box.highlight()

        elif self._accessible_boxes is not None and \
                event.item in self._accessible_boxes:

            box = event.board.get_element(
                self._char_selected.x,
                self._char_selected.y,
                self._char_selected.z)
            box.char = None
            box.update()

            event.board.place_char(
                self._char_selected,
                event.item.x, event.item.y, event.item.z)

            for box in self._accessible_boxes:
                box.unhighlight()
            self._accessible_boxes = None
            self._char_selected = None

        else:
            if self._accessible_boxes is not None:
                for box in self._accessible_boxes:
                    box.unhighlight()
                self._accessible_boxes = None
            self._char_selected = None


Event.add_trigger(OnItemSelected(), ItemSelected)


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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                item = board.get_element_from_screen_position(event.pos)
                if item is not None:
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
