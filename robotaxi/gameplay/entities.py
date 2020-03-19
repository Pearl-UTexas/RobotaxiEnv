import itertools
import random

import numpy as np
from collections import deque, namedtuple


class Point(namedtuple('PointTuple', ['x', 'y'])):
    """ Represents a 2D point with named axes. """

    def __add__(self, other):
        """ Add two points coordinate-wise. """
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """ Subtract two points coordinate-wise. """
        return Point(self.x - other.x, self.y - other.y)


class CellType(object):
    """ Defines all types of cells that can be found in the game. """

    EMPTY = 0
    GOOD_FRUIT = 1
    BAD_FRUIT = 2
    LAVA = 3
    SNAKE_HEAD = 4
    SNAKE_BODY = 5
    WALL = 6
    PIT = 7
    COLLABORATOR_HEAD = 8
    COLLABORATOR_BODY = 9


class SnakeDirection(object):
    """ Defines all possible directions the snake can take, as well as the corresponding offsets. """

    NORTH = Point(0, -1)
    EAST = Point(1, 0)
    SOUTH = Point(0, 1)
    WEST = Point(-1, 0)


ALL_SNAKE_DIRECTIONS = [
    SnakeDirection.NORTH,
    SnakeDirection.EAST,
    SnakeDirection.SOUTH,
    SnakeDirection.WEST,
]


class SnakeAction(object):
    """ Defines all possible actions the agent can take in the environment. """

    MAINTAIN_DIRECTION = 0
    TURN_LEFT = 1
    TURN_RIGHT = 2


ALL_SNAKE_ACTIONS = [
    SnakeAction.MAINTAIN_DIRECTION,
    SnakeAction.TURN_LEFT,
    SnakeAction.TURN_RIGHT,
]

SNAKE_GROW = False
WALL_WARP = True

class Snake(object):
    """ Represents the snake that has a position, can move, and change directions. """
   
    
    def __init__(self, start_coord, length=2, body_coord=None):
        """
        Create a new snake.
        
        Args:
            start_coord: A point representing the initial position of the snake. 
            length: An integer specifying the initial length of the snake.
        """
        self.directions = ALL_SNAKE_DIRECTIONS
        if body_coord == None:
            # Place the snake vertically, heading north.
            self.body = deque([
                Point(start_coord.x, start_coord.y + i)
                for i in range(length)
            ])
            self.direction = SnakeDirection.NORTH            
        else:
            self.body = deque([
                Point(start_coord.x, start_coord.y),
                Point(body_coord.x, body_coord.y)
            ])
            if body_coord.y - start_coord.y == 1: self.direction = SnakeDirection.NORTH
            elif body_coord.y - start_coord.y == -1: self.direction = SnakeDirection.SOUTH
            elif body_coord.x - start_coord.x == -1: self.direction = SnakeDirection.WEST
            elif body_coord.x - start_coord.x == 1: self.direction = SnakeDirection.EAST

    @property
    def head(self):
        """ Get the position of the snake's head. """
        return self.body[0]

    @property
    def tail(self):
        """ Get the position of the snake's tail. """
        return self.body[-1]

    @property
    def mid(self):
        """ Get the position of the snake's mid. """
        return self.body[1]

    @property
    def length(self):
        """ Get the current length of the snake. """
        return len(self.body)

    def peek_next_move(self):
        """ Get the point the snake will move to at its next step. """
        return self.head + self.direction

    def turn_left(self):
        """ At the next step, take a left turn relative to the current direction. """
        direction_idx = self.directions.index(self.direction)
        self.direction = self.directions[direction_idx - 1]

    def turn_right(self):
        """ At the next step, take a right turn relative to the current direction. """
        direction_idx = self.directions.index(self.direction)
        self.direction = self.directions[(direction_idx + 1) % len(self.directions)]

    def grow(self):
        """ Grow the snake by 1 block from the head. """
        self.body.appendleft(self.peek_next_move())

    def move(self):
        """ Move the snake 1 step forward, taking the current direction into account. """
        self.body.appendleft(self.peek_next_move())
        self.body.pop()


class Field(object):
    """ Represents the playing field for the Snake game. """

    def __init__(self, level_map=None):
        """
        Create a new Snake field.
        
        Args:
            level_map: a list of strings representing the field objects (1 string per row).
        """
        self.level_map = level_map
        self._cells = None
        self._empty_cells = set()
        self._pit_cells = set()
        self._good_fruits = set()
        self._bad_fruits = set()
        self._lavas = set()
        self._level_map_to_cell_type = {
            'S': CellType.SNAKE_HEAD,
            's': CellType.SNAKE_BODY,
            '#': CellType.WALL,
            'O': CellType.GOOD_FRUIT,
            '.': CellType.EMPTY,
            'o': CellType.BAD_FRUIT,
            '!': CellType.LAVA,
            'P': CellType.PIT,
            'C': CellType.COLLABORATOR_HEAD,
            'c': CellType.COLLABORATOR_BODY
        }
        self._cell_type_to_level_map = {
            cell_type: symbol
            for symbol, cell_type in self._level_map_to_cell_type.items()
        }

    def __getitem__(self, point):
        """ Get the type of cell at the given point. """
        x, y = point
        return self._cells[y, x]

    def __setitem__(self, point, cell_type):
        """ Update the type of cell at the given point. """
        x, y = point
        self._cells[y, x] = cell_type

        # Do some internal bookkeeping to not rely on random selection of blank cells.
        if cell_type == CellType.EMPTY:
            self._empty_cells.add(point)
        else:
            if point in self._empty_cells:
                self._empty_cells.remove(point)

    def __str__(self):
        return '\n'.join(
            ''.join(self._cell_type_to_level_map[cell] for cell in row)
            for row in self._cells
        )

    @property
    def size(self):
        """ Get the size of the field (size == width == height). """
        return len(self.level_map)

    def create_level(self, init_cells=True):
        """ Create a new field based on the level map. """
        try:
            if init_cells:
                print(self.level_map)
                self._cells = np.array([
                    [self._level_map_to_cell_type[symbol] for symbol in line]
                    for line in self.level_map
                ])
            self._good_fruits = {
                Point(x, y)
                for y in range(self.size)
                for x in range(self.size)
                if self[(x, y)] == CellType.GOOD_FRUIT
            }
            self._bad_fruits = {
                Point(x, y)
                for y in range(self.size)
                for x in range(self.size)
                if self[(x, y)] == CellType.BAD_FRUIT
            }
            self._lavas = {
                Point(x, y)
                for y in range(self.size)
                for x in range(self.size)
                if self[(x, y)] == CellType.LAVA
            }
            self._empty_cells = {
                Point(x, y)
                for y in range(self.size)
                for x in range(self.size)
                if self[(x, y)] == CellType.EMPTY
            }
            self._pit_cells = {
                Point(x, y)
                for y in range(self.size)
                for x in range(self.size)
                if self[(x, y)] == CellType.PIT
            }
        except KeyError as err:
            raise ValueError(f'Unknown level map symbol: "{err.args[0]}"')
    
    def find_snake_body(self):
        """ Find the snake's head on the field. """
        for y in range(self.size):
            for x in range(self.size):
                if self[(x, y)] == CellType.SNAKE_BODY:
                    return Point(x, y)
        raise ValueError('Initial snake body not specified on the level map')
        
    def find_snake_head(self):
        """ Find the snake's head on the field. """
        for y in range(self.size):
            for x in range(self.size):
                if self[(x, y)] == CellType.SNAKE_HEAD:
                    return Point(x, y)
        raise ValueError('Initial snake position not specified on the level map')

    def find_collaborator(self):
        """ Find the snake's head on the field. """
        for y in range(self.size):
            for x in range(self.size):
                if self[(x, y)] == CellType.COLLABORATOR_HEAD:
                    return Point(x, y)
        raise ValueError('Initial collaborator position not specified on the level map')

    def get_random_empty_cell(self):
        """ Get the coordinates of a random empty cell. """
        return random.choice(list(self._empty_cells))

    def get_initial_items(self):
        return list(self._good_fruits), list(self._bad_fruits), list(self._lavas), self._pit_cells

    def place_snake(self, snake):
        """ Put the snake on the field and fill the cells with its body. """
        self[snake.head] = CellType.SNAKE_HEAD
        for snake_cell in itertools.islice(snake.body, 1, len(snake.body)):
            self[snake_cell] = CellType.SNAKE_BODY

    def place_collaborator(self, snake):
        """ Put the snake on the field and fill the cells with its body. """
        self[snake.head] = CellType.COLLABORATOR_HEAD
        for snake_cell in itertools.islice(snake.body, 1, len(snake.body)):
            self[snake_cell] = CellType.COLLABORATOR_BODY

    def update_snake_footprint(self, old_head, old_tail, new_head, collaborator=None):
        """
        Update field cells according to the new snake position.
        
        Environment must be as fast as possible to speed up agent training.
        Therefore, we'll sacrifice some duplication of information between
        the snake body and the field just to execute timesteps faster.
        
        Args:
            old_head: position of the head before the move. 
            old_tail: position of the tail before the move.
            new_head: position of the head after the move.
        """
        self[old_head] = CellType.SNAKE_BODY

        # If we've grown at this step, the tail cell shouldn't move.
        if old_tail:
            if old_tail in self._pit_cells:
                if not (old_tail in collaborator.body):
                    self[old_tail] = CellType.PIT
            else:
                if collaborator is not None:
                    if not (old_tail in collaborator.body):
                        self[old_tail] = CellType.EMPTY
                else:
                    self[old_tail] = CellType.EMPTY

        # Support the case when we're chasing own tail.
        if collaborator is not None:
            if (self[new_head] != CellType.WALL and new_head != collaborator.head) or new_head == old_tail:
                self[new_head] = CellType.SNAKE_HEAD
        else:
            if self[new_head] != CellType.WALL or new_head == old_tail:
                self[new_head] = CellType.SNAKE_HEAD

    def update_collaborator_footprint(self, old_head, old_tail, new_head, human):
        """
        Update field cells according to the new snake position.
        
        Environment must be as fast as possible to speed up agent training.
        Therefore, we'll sacrifice some duplication of information between
        the snake body and the field just to execute timesteps faster.
        
        Args:
            old_head: position of the head before the move. 
            old_tail: position of the tail before the move.
            new_head: position of the head after the move.
        """

        if new_head == old_head:
            if old_tail not in human.body:
                self[old_tail] = CellType.COLLABORATOR_BODY
            return

        self[old_head] = CellType.COLLABORATOR_BODY

        # If we've grown at this step, the tail cell shouldn't move.
        if old_tail:
            if old_tail in self._pit_cells:
                if not (old_tail in human.body):
                    self[old_tail] = CellType.PIT
            else:
                if not (old_tail in human.body):
                    self[old_tail] = CellType.EMPTY

        # Support the case when we're chasing own tail.
        if (self[new_head] != CellType.WALL and new_head != human.head) or new_head == old_tail:
            self[new_head] = CellType.COLLABORATOR_HEAD
