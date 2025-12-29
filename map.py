from utils import Tile
from utils import Rotation
import math
import random
import logging
from queue import Queue


class Map:
    def __init__(self, n, my_base, enemy_bases):
        self.n = n
        self.board = [[Tile.FOG for _ in range(n)] for _ in range(n)]
        self.board[my_base[0]][my_base[1]] = Tile.MY_BASE
        for enemy_base in enemy_bases:
            self.board[enemy_base[0]][enemy_base[1]] = Tile.ENEMY_BASE
        self.agent_board = [[Tile.EMPTY for _ in range(n)] for _ in range(n)]
        self.cover_board = [[False for _ in range(n)] for _ in range(n)]

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
    
    # add agent's vision
    def update(self, agents):
        # remove agents from map
        self.agent_board = [[Tile.EMPTY for _ in range(self.n)] for _ in range(self.n)]
        # reset cover map
        self.cover_board = [[False for _ in range(self.n)] for _ in range(self.n)]
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

    # returns first tile on path or None
    # ignore walls & allies
    def bfs(self, start, target):
        if start == target:
            logging.info("bfs target same as start")
            return None
        frontier = Queue()
        frontier.put(start)
        came_from = dict()
        came_from[start] = None

        while not frontier.empty():
            current = frontier.get()
            if current == target:
                break           
            for next in self.adjacent_cords(current):
                if self.board[next[0]][next[1]] == Tile.WALL: # or self.agent_board[next[0]][next[1]] in [Tile.ALLY, Tile.RESERVED]:
                    continue
                if next not in came_from:
                    frontier.put(next)
                    came_from[next] = current

        if target not in came_from:
            return None

        current = target
        while current != start:
            if came_from[current] == start:
                return current
            current = came_from[current]
        raise Exception("Path not reconstructed")
