import random

MAX_HEALTH = 100

class Player:

    def __init__(self, name, sids):
        self.name = name
        self.sids = sids


class Castle:

    def __init__(self, player, uid):
        self.player = player
        self.health = MAX_HEALTH
        self.uid = uid
        self.level = 1


    def __repr__(self):
        return 'Castle with health: {}'.format(self.health)


class Minion:

    def __init__(self):
        self.health = MAX_HEALTH
        self.level = 1

