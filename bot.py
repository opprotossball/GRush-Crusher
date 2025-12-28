from map import Map
from utils import Tile, Rotation, Command
from agent import Agent
import random
import logging


class Bot:
    EXPLORE = 1.5
    MINERS = 0.2
    
    def __init__(self, n, game_length, n_players, my_base, enemy_bases):
        self.n = n
        self.game_length = game_length
        self.n_players = n_players
        self.my_base = my_base
        self.enemy_bases = enemy_bases
        self.map = Map(n, my_base, enemy_bases)
        self.agents = []
        self.camp_locations = []
        
    def update(self, agents):
        self.agents = agents
        self.map.update(agents)

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
            if agent.vision.tile == Tile.ENEMY and not agent.has_gold:
                commands[id] = Command.FIRE
        return commands

    # go to base if holding gold
    def go_to_gold(self, agents, commands):
        miners = 0
        for id, agent in enumerate(agents):
            if miners > len(agents) * Bot.MINERS:
                break
            if commands[id] is not None or agent.has_gold:
                continue
            cords, dist = self.map.find_closest(agent.row, agent.col, Tile.GOLD)
            # if cannot find fog command stays None
            if cords is None:
                continue
            commands[id] = self.go(agent, cords)
            miners += 1
        return commands
    
    # return gold
    def return_gold(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is not None:
                continue
            if agent.has_gold:
                commands[id] = self.go(agent, self.my_base)
        return commands
    
    # mine if on gold
    def mine(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is not None:
                continue
            if not agent.has_gold and agent.on_gold:
                commands[id] = Command.MINE
        return commands

    # returns action or None
    def go(self, agent, target):
        next_step = self.map.bfs((agent.row, agent.col), target)
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
                commands[id] = random.choice([Command.GO, Command.LEFT, Command.RIGHT, Command.BACK])            
        return commands

    # go to camp locations
    def go_to_camp(self, agents, commands):
        pass
    
    # stay in camp locations
    def hold_position(self, agents, commands):
        for id, agent in enumerate(agents):
            if commands[id] is None and ((agent.row, agent.col), agent.rot) in self.camp_locations:
                commands[id] = Command.MINE
            else:
                for ((camp_row, camp_col), camp_rot) in self.camp_locations:
                    if (agent.row, agent.col) == (camp_row, camp_col):
                        return agent.calculate_rotation(camp_rot)
        return commands
        
    # only explore
    def command(self):
        commands = [None for _ in range(len(self.agents))]
        commands = self.return_gold(self.agents, commands)
        commands = self.shoot(self.agents, commands)
        commands = self.mine(self.agents, commands)
        commands = self.go_to_gold(self.agents, commands)
        if self.map.count_on_board(Tile.FOG) / (self.map.n ** 2) > (1 / self.n_players) * Bot.EXPLORE:
            commands = self.explore(self.agents, commands)
        commands = self.default(self.agents, commands)
        return commands
  