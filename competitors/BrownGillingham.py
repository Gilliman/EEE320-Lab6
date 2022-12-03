"""
Our creature that will compete in lab 6

Created by:
    OCdt Brown, and
    OCdt Gillingham
"""

from shared import Creature, Cilia, CreatureTypeSensor, Propagator, Direction, Soil, Plant


class BugKilla(Creature):

    __instance_count = 0

    def __init__(self):
        super().__init__()
        BugKilla.__instance_count += 1


    def do_turn(self):
        pass

    @classmethod
    def destroyed(cls):
        BugKilla.__instance_count -= 1

    @classmethod
    def instance_count(cls):
        return BugKilla.__instance_count

    def create_organs(self):
        pass

    # copied form Hunter as I think this makes a lot of sense to do it this way but idk bro
    def reproduce_if_able(self):
        if self.strength() >= 0.9 * Creature.MAX_STRENGTH:
            for d in Direction:
                nursery = self.type_sensor.sense(d)
                if nursery == Soil or nursery == Plant:
                    self.womb.give_birth(self.strength()/2, d)
                    break

class MiniBugKilla(Hunter):

    def __init__(self):
        super().__init__()
git
class BugKillaPropagator(Propagator):

    def make_child(self):
        return MiniBugKilla()