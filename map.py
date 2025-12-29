from utils import Tile
from utils import Rotation
import math
import random
import logging
from queue import Queue


class Map:
    def __init__(self, n, my_base, enemy_bases):
        self.n = n
        self.my_base = my_base
        self.enemy_bases = enemy_bases
        self.board = [[Tile.FOG for _ in range(n)] for _ in range(n)]
        self.agent_board = [[Tile.EMPTY for _ in range(n)] for _ in range(n)]

    @staticmethod
    def dist(cords1, cords2):
        return abs(cords1[0] - cords2[0]) + abs(cords1[1] - cords2[1])

    def count_on_board(self, tile_type):
        count = 0
        for _, tile in self.iter():
            if tile == tile_type:
                count += 1
        return count
        
    def line_cords(self, row, col, rot, dist=None):
        # calculate max dist
        if dist is None:
            if rot == Rotation.U:
                dist = row
            elif rot == Rotation.R:
                dist = self.n - col - 1
            elif rot == Rotation.D:
                dist = self.n - row - 1
            elif rot == Rotation.L:
                dist = col
            else:
                raise Exception("Invalid rotation")
        
        res = []
        for _ in range(dist):
            if rot == Rotation.U:
                row -= 1
            elif rot == Rotation.R:
                col += 1
            elif rot == Rotation.D:
                row += 1
            elif rot == Rotation.L:
                col -= 1
            else:
                raise Exception("Invalid rotation")
            res.append((row, col))
        return res
    
    def line(self, row, col, rot, dist=None):
        cords = self.line_cords(row, col, rot, dist)
        return list(zip(cords, [self.board[row][col] for row, col in cords]))

    def iter(self):
        for row, row_vals in enumerate(self.board):
            for col, tile in enumerate(row_vals):
                yield (row, col), tile

    # returns (None, math.inf) if cannot find
    def find_closest(self, row, col, target_tile):
        target = None
        dist = math.inf
        for cords, tile in self.iter():
            if tile != target_tile:
                continue
            new_dist = Map.dist((row, col), cords)
            if new_dist < dist:
                dist = new_dist
                target = cords
        return target, dist
    
    def find_all(self, target_tile):
        result = []
        for cords, tile in self.iter():
            if tile == target_tile:
                result.append(cords)
        return result
    
    # add agent's vision & set my base to EMPTY (not GOLD)
    def update(self, agents):
        # remove agents from map
        self.agent_board = [[Tile.EMPTY for _ in range(self.n)] for _ in range(self.n)]
        # add agents and their visions
        for agent in agents:
            # set agent on agent board
            self.agent_board[agent.row][agent.col] = Tile.ALLY
            # remove fog from agents tile
            if self.board[agent.row][agent.col] == Tile.FOG:
                self.board[agent.row][agent.col] = Tile.EMPTY
            # calculate vision
            vision_line = self.line_cords(agent.row, agent.col, agent.rot, agent.vision.dist)
            for row, col in vision_line[:-1]:
                self.board[row][col] = Tile.EMPTY
            last_row, last_col = vision_line[-1]
            tile = agent.vision.tile
            if tile in [Tile.ALLY, Tile.ENEMY]:
                self.agent_board[last_row][last_col] = tile
            else:
                self.board[last_row][last_col] = tile
        # set my base to EMPTY
        self.board[self.my_base[0]][self.my_base[1]] = Tile.EMPTY

    def random_cords(self):
        return (random.randint(0, self.n-1), random.randint(0, self.n-1))
    
    def adjacent_cords(self, cords):
        adjacent = []
        if cords[0] > 0:
            adjacent.append((cords[0] - 1, cords[1]))
        if cords[0] < self.n - 1:
            adjacent.append((cords[0] + 1, cords[1]))
        if cords[1] > 0:
            adjacent.append((cords[0], cords[1] - 1))
        if cords[1] < self.n - 1:
            adjacent.append((cords[0], cords[1] + 1))
        return adjacent

    def adjacent(self, cords, rot):
        row, col = cords
        if rot == Rotation.U:
            row -= 1
        elif rot == Rotation.R:
            col += 1
        elif rot == Rotation.D:
            row += 1
        elif rot == Rotation.L:
            col -= 1
        if row >= 0 and col >= 0 and row < self.n and col < self.n:
            return (row, col)
        return None
    
    # returns first tile on path or None
    # ignore walls & allies
    def bfs(self, start, start_rot, target):
        if start == target:
            logging.info("bfs target same as start")
            return None
        frontier = Queue()
        frontier.put((start, start_rot))
        came_from = dict()
        came_from[(start, start_rot)] = None

        while not frontier.empty():
            # get new frontier
            current, current_rot = frontier.get()
            if current == target:
                break           
            
            # go forward
            next_tile = self.adjacent(current, current_rot)
            if (next_tile is not None and
                self.board[next_tile[0]][next_tile[1]] != Tile.WALL and
                (self.agent_board[next_tile[0]][next_tile[1]] != Tile.ALLY or next_tile == target) and
                (next_tile, current_rot) not in came_from
            ):
                frontier.put((next_tile, current_rot))
                came_from[(next_tile, current_rot)] = (current, current_rot)
                
            # rotate
            for rot in Rotation:
                if rot == current_rot:
                    continue
                if (current, rot) not in came_from:
                    frontier.put((current, rot))
                    came_from[(current, rot)] = (current, current_rot)
                    
        # check rotation of arrival
        target_rot = None
        for rot in Rotation:
            if (target, rot) in came_from:
                target_rot = rot
                break
        
        if target_rot is None:
            return None

        current = (target, target_rot)
        while current[0] != start:
            if came_from[current][0] == start:
                # return just tile
                return current[0]
            current = came_from[current]
        raise Exception("Path not reconstructed")
