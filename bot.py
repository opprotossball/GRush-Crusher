from map import Map
from utils import Tile, Rotation, Command
from agent import Agent
import math
import random
import logging


class Bot:
    # 1 - explore 1/num of players tiles of map
    EXPLORE = 0.4
    # number of agents gathering gold
    MINERS = 5
    CAMPERS = 0.4
    GUARD_PERIMETER = 4
    LEAVE_PERIMETER = 7
    
    def __init__(self, n, game_length, n_players, my_base, enemy_bases):
        self.n = n
        self.game_length = game_length
        self.n_players = n_players
        self.my_base = my_base
        self.enemy_bases = enemy_bases
        self.map = Map(n, my_base, enemy_bases)
        self.agents = []
        self.camp_locations = []
        self.current_miners = 0
        # remove fog near the base
        for row in range(n):
            for col in range(n):
                if self.map.dist((row, col), my_base) <= Bot.LEAVE_PERIMETER and self.map.board[row][col] == Tile.FOG:
                    self.map.board[row][col] = Tile.EMPTY
        
    def prefered_camp_rotations(self):
        rotations = []
        if self.my_base[0] < self.n // 2:
            rotations.append(Rotation.D)
        else:
            rotations.append(Rotation.U)
        if self.my_base[1] < self.n // 2:
            rotations.append(Rotation.R)
        else:
            rotations.append(Rotation.L)
        return rotations
    
    # returns camp locations for 2 agents
    def guard_location(self, target):
        result = []
        rotations = self.prefered_camp_rotations()
        considerd_tiles = set(target)
        for _ in range(Bot.GUARD_PERIMETER):
            for tile in considerd_tiles:
                for neighbour in self.map.adjacent_cords(tile):
                    considerd_tiles.add(neighbour)
        # dont camp on target
        considerd_tiles.remove(target)
        for rot in rotations:
            best_score = -math.inf
            best_position = None
            # score = vision + 3*covered sides - dist from target if range > 0
            for tile in considerd_tiles:
                # calculate vision
                line = self.map.line_cords(tile[0], tile[1], rot, dist=None)
                vision = 0
                for cords in line:
                    if self.map.board[cords[0]][cords[1]] == Tile.WALL:
                        break
                    vision += 1
                    if self.map.board[cords[0]][cords[1]] == Tile.GOLD:
                        break
                # calculate cover
                cover = 0
                adjacent = self.map.adjacent_cords(tile)
                for cords in adjacent:
                    if self.map.board[cords[0]][cords[1]] == Tile.WALL:
                        cover += 1
                # calculate dist from target
                target_dist = self.map.dist(target, tile)
                # calculate score
                score = 0 if vision == 0 else vision + (3*cover) - target_dist
                if score > best_score:
                    best_position = tile
                    best_score = score
            # should't happen
            if best_position is None:
                continue
            result.append((best_position, rot))
            considerd_tiles.remove(best_position)
            # remove tiles in line
            for cord in self.map.line_cords(best_position[0], best_position[1], rot, dist=None):
                if cord in considerd_tiles:
                    considerd_tiles.remove(cord)
        return result
        
    def update(self, agents):
        self.agents = agents
        self.map.update(agents)
        self.current_miners = 0
        for agent in agents:
            if agent.has_gold:
                self.current_miners += 1

    # If agent can scout by rotating do it. Else go to nearest fog    
    def explore(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is not None:
                continue
            # rotate
            for rot in Rotation:
                line = self.map.line(agent.row, agent.col, rot, dist=None)
                # if fog before obstacle, rotate
                for _, tile in line:
                    if tile == Tile.FOG:
                        commands[id] = agent.calculate_rotation(rot)
                        break
                    if tile != Tile.EMPTY:
                        break
            if commands[id] is not None:
                continue
            # go to nearest fog
            cords, dist = self.map.find_closest(agent.row, agent.col, Tile.FOG)
            # if cannot find fog command stays None
            if cords is None:
                continue
            commands[id] = self.go(agent, cords)
        return commands

    # fire if enemy in sight
    def shoot(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is not None:
                continue
            # TODO shoot based on agent map instead of vision
            if agent.vision.tile == Tile.ENEMY and not agent.has_gold:
                commands[id] = Command.FIRE
        return commands

    # go to base if holding gold
    def go_to_gold(self, agents, commands, max_agents=None):
        gone = 0
        golds = self.map.find_all(Tile.GOLD)
        if len(golds) == 0:
            return commands
        for id, agent in enumerate(agents):
            if max_agents is not None and gone >= max_agents:
                break
            if commands[id] is not None or agent.has_gold:
                continue
            if random.random() < 0.8:
                cords, _ = self.map.find_closest(agent.row, agent.col, Tile.GOLD)
            else:
                cords = random.choice(golds)
            # if cannot find fog command stays None
            if cords is None or cords == self.my_base:
                continue
            commands[id] = self.go(agent, cords)
            gone += 1
        return commands
    
    def go_to_closest_golds(self, agents, commands):
        gone = 0
        golds = self.map.find_all(Tile.GOLD)
        golds.sort(key=lambda x: self.map.dist(x, self.my_base))
        for gold in golds:
            if gone >= 2 * Bot.MINERS:
                break
            best_id = None
            best_dist = math.inf
            for id, agent in enumerate(agents):
                if commands[id] is not None or agent.has_gold:
                    continue
                dist = self.map.dist(agent.cords(), gold)
                if dist < best_dist:
                    best_id = id
                    best_dist = dist
            if best_id is not None:
                commands[best_id] = self.go(agent, gold)
                gone += 1
        return commands
    
    # return gold
    def return_gold(self, agents, commands):
        ids_agents = list(enumerate(agents))
        ids_agents.sort(key=lambda x: self.map.dist((x[1].row, x[1].col), self.my_base))
        for id, agent in ids_agents:
            if commands[id] is not None:
                continue
            if agent.has_gold:
                commands[id] = self.go(agent, self.my_base)
        return commands
    
    # mine if on gold
    def mine(self, agents, commands):
        for id, agent in enumerate(agents):
            if self.current_miners >= Bot.MINERS:
                break
            if commands[id] is not None:
                continue
            if not agent.has_gold and self.map.board[agent.row][agent.col] == Tile.GOLD:
                commands[id] = Command.MINE
                self.current_miners += 1
        return commands
    
    def mine_closest_golds(self, agents, commands):
        golds = self.map.find_all(Tile.GOLD)
        golds.sort(key=lambda x: self.map.dist(x, self.my_base))
        for gold in golds:
            if self.current_miners >= Bot.MINERS:
                break
            for id, agent in enumerate(agents):
                if commands[id] is not None:
                    continue
                if agent.cords() == gold and not agent.has_gold:
                    commands[id] = Command.MINE
                    self.current_miners += 1
        return commands

    # returns action or None
    def go(self, agent, target):
        next_step = self.map.bfs((agent.row, agent.col), agent.rot, target)
        if next_step is None:
            return None
        if next_step[0] == agent.row - 1:
            rot = Rotation.U
        elif next_step[1] == agent.col + 1:
            rot = Rotation.R
        elif next_step[0] == agent.row + 1:
            rot = Rotation.D
        elif next_step[1] == agent.col - 1:
            rot = Rotation.L
        else:
            raise Exception("bfs returned trash")
        if agent.rot == rot:
            if self.map.agent_board[next_step[0]][next_step[1]] != Tile.EMPTY:
                # stall if blocked
                return None
            self.map.agent_board[next_step[0]][next_step[1]] = Tile.RESERVED
            return Command.GO
        return agent.calculate_rotation(rot)
    
    # default behaviour
    def default(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is None:
                commands[id] = random.choices(
                    [Command.MINE, Command.GO, Command.LEFT, Command.RIGHT, Command.BACK],
                    weights=[0.0, 0.50, 0.25, 0.25, 0.0],
                    k=1,
                )[0]            
        return commands

    # go to camp locations
    def go_to_camp(self, agents, commands):
        for camp_cords, camp_rot in self.camp_locations:
            if self.map.agent_board[camp_cords[0]][camp_cords[1]] == Tile.ALLY:
                continue
            # find closest agent
            best_dist = -math.inf
            best_id = None
            for id, agent in enumerate(agents):
                if commands[id] is not None:
                    continue
                dist = self.map.dist(camp_cords, (agent.row, agent.col))
                if dist < best_dist:
                    best_id = id
                    best_dist = dist
            if best_id is not None:
                commands[best_id] = self.go(agents[best_id], camp_cords)
        return commands
                
    # stay in camp locations & rotate properly
    def hold_position(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is None and ((agent.row, agent.col), agent.rot) in self.camp_locations:
                commands[id] = Command.MINE
            else:
                for ((camp_row, camp_col), camp_rot) in self.camp_locations:
                    if (agent.row, agent.col) == (camp_row, camp_col):
                        return agent.calculate_rotation(camp_rot)
        return commands
    
    # if in LEAVE_PERIMETER go to random tile outside
    def leave_base(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is not None:
                continue
            if self.map.dist((agent.row, agent.col), self.my_base) > Bot.LEAVE_PERIMETER:
                continue
            if random.random() < 0.85:
                # randomly choose tile to go to - should succed in max few tries
                for _ in range(10000):
                    target = (random.randint(0, self.map.n-1), random.randint(0, self.map.n-1))
                    if self.map.dist(target, self.my_base) > Bot.LEAVE_PERIMETER and self.map.board[target[0]][target[1]] != Tile.WALL:
                        break
                commands[id] = self.go(agent, target)
            else:
                # go randomly
                commands[id] = random.choices(
                    [Command.GO, Command.LEFT, Command.RIGHT, Command.BACK],
                    weights=[0.25, 0.25, 0.25, 0.25],
                    k=1,
                )[0]            
        return commands
                
    # guard furthest gold
    def choose_camp_locations(self):
        self.camp_locations = []
        golds = self.map.find_all(Tile.GOLD)
        golds.sort(key=lambda x: 1)
        # TODO choose golds to camp on
    
    def should_explore(self):
        return (self.map.count_on_board(Tile.FOG) / (self.map.n ** 2)) * Bot.EXPLORE > (1 / self.n_players)
    
    def command(self):
        commands = [None for _ in range(len(self.agents))]
        commands = self.return_gold(self.agents, commands)
        commands = self.shoot(self.agents, commands)
        if self.should_explore():
            commands = self.explore(self.agents, commands)
        # commands = self.leave_base(self.agents, commands)
        commands = self.mine(self.agents, commands)
        commands = self.go_to_gold(self.agents, commands)
        commands = self.explore(self.agents, commands)
        commands = self.default(self.agents, commands)
        return commands
  