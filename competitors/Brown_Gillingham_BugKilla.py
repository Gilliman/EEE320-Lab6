"""
Our creature that will compete in lab 6

Created by:
    OCdt Brown, and
    OCdt Gillingham
"""

from shared import Creature, Propagator, Direction

class BugKilla(Creature):

    __instance_count = 0

    def __init__(self):
        super().__init__()
        BugKilla.__instance_count += 1
        self.womb = None

    def do_turn(self):
        self.kid_ify()

    @classmethod
    def destroyed(self):
        BugKilla.__instance_count -= 1

    @classmethod
    def instance_count(cls):
        return BugKilla.__instance_count


    def kid_ify(self):
        while self.strength() >= 0.9 * Creature.MAX_STRENGTH:
            self.womb.give_birth(self.strength()/2, Direction.random())


class BugKillaPropagator(Propagator):

    def make_child(self):
        return BugKilla