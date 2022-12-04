"""
Our creature that will compete in lab 6

Created by:
    OCdt Brown, and
    OCdt Gillingham
"""
from random import random

from shared import Creature, Cilia, CreatureTypeSensor, Propagator, Direction, Soil, Plant, Spikes, EnergySensor, PoisonGland


class BugKilla(Creature):

    __instance_count = 0
    __less_reproduction = 350
    __bad_guys = []

    def __init__(self):
        super().__init__()
        BugKilla.__instance_count += 1
        self.cilia = None
        self.type_sensor = None
        self.womb = None
        self.spikes = None
        self.poison = None
        self.energy_sensor = None

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
    def do_turn(self):
        if not (self.spikes and self.womb and self.type_sensor):
            self.create_organs()
        else:
            self.reproduce_if_able()

    def create_organs(self):
        if not self.spikes and self.strength() > Spikes.CREATION_COST:
            self.spikes = Spikes(self)
        if not self.womb and self.strength() > Propagator.CREATION_COST:
            self.womb = BugKillaPropagator(self)
        if not self.type_sensor and self.strength() > CreatureTypeSensor.CREATION_COST:
            self.type_sensor = CreatureTypeSensor(self)


class BugAttacker(BugKilla):
    def do_turn(self):
        if not (self.cilia and self.type_sensor):
            self.create_organs()
        elif self.poison:
            self.poison.add_poison(self.strength())
            self.poison.drop_poison(Direction.random(), self.poison.current_volume())
        else:
            (did_attack, safe_dir) = self.find_someone_to_attack()
            if not did_attack and safe_dir:
                self.cilia.move_in_direction(safe_dir)
            if did_attack and not safe_dir:
                randomNum = random()
                if randomNum <= 0.1:
                    self.create_posion()

    def create_organs(self):
        if not self.cilia and self.strength() > Cilia.CREATION_COST:
            self.cilia = Cilia(self)
        if not self.type_sensor and self.strength() > CreatureTypeSensor.CREATION_COST:
            self.type_sensor = CreatureTypeSensor(self)

    def create_posion(self):
        if not self.poison and self.strength() > PoisonGland.CREATION_COST:
            self.poison = PoisonGland(self)

    def find_someone_to_attack(self):
        safe_dir = None
        for d in Direction:
            victim = self.type_sensor.sense(d)
            if victim != Soil and victim != BugKilla and victim != MiniBugKilla and victim != Spiker \
                    and victim != BugAttacker:
                self.cilia.move_in_direction(d)
                if victim == Plant:
                    return False, safe_dir
                return True, safe_dir
            elif victim == Soil:
                safe_dir = d
        return False, safe_dir


class BugKillaPropagator(Propagator):
    def make_child(self):
        randomNum = random()
        # 1/16 chance of creating a Spiker
        if randomNum <= 0.0625:
            return Spiker()
        # 2/10 chance of creating an Attacker
        elif randomNum <= 0.2625:
            return BugAttacker()
        # 67/80 chance of creating a MiniBugKila
        else:
            return MiniBugKilla()
