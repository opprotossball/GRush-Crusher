from utils import Tile, Rotation, Command
from map import Map
from dataclasses import dataclass


@dataclass
class Vision:
    tile: Tile
    dist: int

class Agent:
    def __init__(self, row, col, rot, vision, has_gold=False, on_gold=False):
        self.row = row
        self.col = col
        self.rot = rot
        self.has_gold = has_gold
        self.on_gold = on_gold
        self.vision = vision

    def calculate_rotation(self, target_rot):
        diff = target_rot.value - self.rot.value
        if diff == 0:
            return None
        elif diff in [1, -3]:
            return Command.RIGHT
        elif diff in [-1, 3]:
            return Command.LEFT
        elif abs(diff) == 2: 
            return Command.BACK
        else:
            raise Exception("Rotation diff incorrect")
        
    @staticmethod
    def from_string(string):
        data = string.split()
        agent = Agent(
            row=int(data[0]), 
            col=int(data[1]),
            rot=Rotation.from_string(data[4]),
            vision = Vision(
                tile=Tile.from_string(data[2]),
                dist=int(data[3]),
            )
        )
        return agent
        