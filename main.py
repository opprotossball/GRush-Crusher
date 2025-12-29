import sys
import logging
from enum import Enum
from map import Map
from utils import Rotation, Tile
from bot import Bot
from agent import Agent, Vision


if __name__ == "__main__":
    print("Grush Crusher")
    sys.stdout.flush()
    N, GAME_LENGTH = map(int, input().split())
    N_PLAYERS = int(input())
    MY_BASE = tuple(map(int, input().split()))
    ENEMY_BASES = [tuple(map(int, input().split())) for _ in range(N_PLAYERS-1)]

    bot = Bot(N, GAME_LENGTH, N_PLAYERS, MY_BASE, ENEMY_BASES)

    while True:
        try:
            # take input
            n_agents = int(input())
            agents = []
            for _ in range(n_agents):
                agents.append(Agent.from_string(input()))
            bot.update(agents)
            # assign commands
            commands = bot.command()
            for command in commands:
                print(command.name)
            sys.stdout.flush()
        except Exception as e:
            logging.exception(e)
