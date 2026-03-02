from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def __repr__(self):
        return f'({self.x}, {self.y})'


class OutOfMapError(ValueError):
    def __init__(self, pos: Position):
        super().__init__(f'({pos.x}, {pos.y}) is outside the map')


def convert_string(pos: str) -> Position:
    pos = pos.split(' ')
    pos = [int(i) for i in pos]
    return Position(pos[0], pos[1])