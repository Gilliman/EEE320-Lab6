"""
Our creature that will compete in lab 6

Created by:
    OCdt Brown, and
    OCdt Gillingham
"""
from random import random

from shared import Creature, Cilia, CreatureTypeSensor, Propagator, Direction, Soil, Plant, Spikes


class BugKilla(Creature):

    __instance_count = 0
    __less_reproduction = 350

    def __init__(self):
        super().__init__()
        BugKilla.__instance_count += 1
        self.cilia = None
        self.type_sensor = None
        self.womb = None

    def do_turn(self):
        if not (self.cilia and self.type_sensor and self.womb):
            self.organify()
        else:
            self.reproduce_if_able()
            self.move()

    @classmethod
    def destroyed(cls):
        BugKilla.__instance_count -= 1

    @classmethod
    def instance_count(cls):
        return BugKilla.__instance_count

    def organify(self):
        if not self.cilia and self.strength() > Cilia.CREATION_COST:
            self.cilia = Cilia(self)
        if not self.type_sensor and self.strength() > CreatureTypeSensor.CREATION_COST:
            self.type_sensor = CreatureTypeSensor(self)
        if not self.womb and self.strength() > Propagator.CREATION_COST:
            self.womb = BugKillaPropagator(self)

    # copied form Hunter as I think this makes a lot of sense to do it this way but idk bro
    def reproduce_if_able(self):
        if self.strength() >= 0.9 * Creature.MAX_STRENGTH:
            for d in Direction:
                nursery = self.type_sensor.sense(d)
                # if the population of our bug is greater than less_reproduction save energy IOT attack more
                # if BugKilla.__instance_count > BugKilla.__less_reproduction and nursery == Plant:
                #     self.womb.give_birth(self.strength()/2, d)
                if nursery == Plant:
                    self.womb.give_birth(self.strength()/2, d)
                    break

    def move(self):
        for d in Direction:
            block = self.type_sensor.sense(d)
            if block == Plant:
                self.cilia.move_in_direction(d)
        self.cilia.move_in_direction(Direction.random())


class MiniBugKilla(BugKilla):

    def __init__(self):
        super().__init__()


class Spiker(BugKilla):
    def __init__(self):
        super().__init__()
        self.spikes = None
        self.womb = None

    def do_turn(self):
        if not (self.spikes and self.womb):
            self.create_organs()
        else:
            self.reproduce_if_able()

    def create_organs(self):
        if not self.spikes and self.strength() > Spikes.CREATION_COST:
            self.spikes = Spikes(self)
        # if not self.womb and self.strength() > Propagator.CREATION_COST:
        #     self.womb = BugKillaPropagator(self)


class BugKillaPropagator(Propagator):
    def make_child(self):
        randomNum = random()
        if randomNum <= 0.0625:
            return Spiker()
        else:
            return MiniBugKilla()
