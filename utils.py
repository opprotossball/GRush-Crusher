from enum import Enum
from dataclasses import dataclass

class Tile(Enum):
    FOG = 0
    EMPTY = 1
    WALL = 2
    ALLY = 3
    ENEMY = 4
    GOLD = 5
    MY_BASE = 6
    ENEMY_BASE = 7
    RESERVED = 8

    @classmethod
    def from_string(cls, s: str):
        return cls[s.strip().upper()]


class Rotation(Enum):
    U = 0
    R = 1
    D = 2
    L = 3

    @classmethod
    def from_string(cls, s: str):
        return cls[s.strip().upper()]


class Command(Enum):
    FIRE = 0
    GO = 1
    MINE = 2
    LEFT = 3
    RIGHT = 4
    BACK = 5
