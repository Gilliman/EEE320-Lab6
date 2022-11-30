"""
Our creature that will compete in lab 6

Created by:
    OCdt Brown, and
    OCdt Gillingham
"""

from shared import Creature, Propagator

class BugKilla(Creature):

    __instance_count = 0

    def __init__(self):
        super().__init__()
        BugKilla.__instance_count += 1


    def do_turn(self):
        pass

    def destroyed(self):
        BugKilla.__instance_count -= 1

    def instance_count(self):
        return BugKilla.__instance_count