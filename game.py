import sys
import logging
import operator
import pygame
import pygame.time

from collections import namedtuple
from functools import partial
from itertools import chain, groupby

logging.basicConfig(level=logging.INFO)

black = (0, 0, 0)
green = (0, 224, 0)


class Point(namedtuple('Point', ['x', 'y'])):
    def __add__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.x + other.x, self.y + other.y)


def within(board, point):
    return Point(0, 0) <= point < board


def neighbours_of(within, point):
    offsets = [Point(-1, -1), Point(-1, 0), Point(-1, 1),
               Point(0, -1), Point(0, 1),
               Point(1, -1), Point(1, 0), Point(1, 1)]

    return [point + offset for offset in offsets if within(point + offset)]


def game_to_screen(board_coords, screen_coords, point):
    cell_width = screen_coords.x / board_coords.x
    cell_height = screen_coords.y / board_coords.y

    logging.debug("x-scale: {}".format(cell_width))
    logging.debug("y-scale: {}".format(cell_height))

    r = pygame.Rect(point.x * cell_width, point.y * cell_height,
                    cell_width, cell_height)

    logging.debug("cell is: {}".format(r))
    return r


def screen_to_game(board_coords, screen_coords, point):
    cell_width = screen_coords.x / board_coords.x
    cell_height = screen_coords.y / board_coords.y

    return Point(point.x / cell_width, point.y / cell_height)


def handle_click(derasterise, pos, cells):
    p = Point._make(pos)
    cell = derasterise(p)
    if cell not in cells:
        logging.info("adding cell from {} at {}".format(pos, cell))
        cells.add(cell)
    else:
        logging.info("removing cell from {} at {}".format(pos, cell))
        cells.remove(cell)
    return cells


def load_from(iterable):
    cells = set()
    for y, row in enumerate(iterable):
        for x, val in enumerate(row):
            if val == 'x':
                logging.info("adding cell at {}, {}".format(x, y))
                cells.add(Point(x, y))
    return cells


def main(initial_cells):
    pygame.init()
    screen = pygame.display.set_mode([800, 600])

    board = Point(400, 300)
    rasterise = partial(game_to_screen, board, Point(800, 600))
    derasterise = partial(screen_to_game, board, Point(800, 600))
    click_fn = partial(handle_click, derasterise)
    neighbour_fn = partial(neighbours_of, partial(within, board))

    clock = pygame.time.Clock()

    cells = set(initial_cells)
    run_simulation = False

    while 1:
        clock.tick(30)

        for event in pygame.event.get():
            logging.debug(event)
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    run_simulation = not run_simulation
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[0] == 1:
                    cells = click_fn(event.pos, cells)
            if event.type == pygame.MOUSEBUTTONUP:
                cells = click_fn(event.pos, cells)

        screen.fill(black)

        if run_simulation:
            neighbours = chain.from_iterable((neighbour_fn(cell) for cell in cells))
            neighbour_groups = groupby(sorted(neighbours))

            def alive(cell, count):
                return count == 3 or (count == 2 and cell in cells)

            new_cells = set()
            for cell, group in neighbour_groups:
                if alive(cell, len(list(group))):
                    new_cells.add(cell)

            cells = new_cells

        for cell in cells:
            pygame.draw.rect(screen, green, rasterise(cell))

        pygame.display.flip()

if __name__ == '__main__':
    try:
        initial_cells = set()
        try:
            with open(sys.argv[1]) as f:
                initial_cells = load_from(f)
        except:
            pass
        main(initial_cells)
    except:
        logging.exception("Uncaught exception at top-level")
        raise
