"""
This module contains classes which form part of the BugBattle
system and which are used in the creation of competitor creatures.

Competitor creatures are forbidden from accessing private
attributes and methods as well as attributes and methods whose
names start with `f_` or `F_`. These are reserved for game framework
use.

version 1.13
2021-11-23

Python implementation: Greg Phillips
Based on an original design by Scott Knight and a series of
implementations in C++ and Java by Scott Knight and Greg Phillips
"""


import random
import math
from enum import Enum
from abc import ABC, abstractmethod


class Creature(ABC):
    """
    The abstract superclass of all creatures.

    Subclasses must have a class attribute __instance_count which must be

    - incremented in the subclass constructor
    - decremented in a class method called destroyed()
    - returned from a class method called instance_count()

    If you have multiple Creature subclasses as part of your competitor strategy,
    then a few things are required to make instance counting and colour coding in
    in the view work properly.

    1. All your competitor classes MUST be subclasses of your main competitor class,
    and MUST NOT define their own __instance_count attribute, destroyed() method, or
    instance_count() method.

    2. All accesses MUST use the explicit name of the main competitor class. E.g., if
    your main competitor is Hunter, its destroyed() method must be

        @classmethod
        def destroyed(cls):
            Hunter.__instance_count -= 1

    and NOT

        @classmethod
        def destroyed(cls):
            cls.__instance_count -= 1

    See the Hunter and LittleHunter classes in competitors/HuntingInstructors.py
    for an example.

    """

    __MAX_STRENGTH = MAX_STRENGTH = 2000
    __MAINTENANCE_COST = MAINTENANCE_COST = 20
    __MAX_ORGANS = MAX_ORGANS = 10
    __DEAD_COLOUR = 'black'

    def __init__(self):
        self.__world = None
        self.__location = None
        self.__alive = True
        self.__strength = 0
        self.__colour = None
        self.__organs = []
        self.__cloaked = False
        self.__poisonous = False

    @abstractmethod
    def do_turn(self):
        pass

    @abstractmethod
    def destroyed(self):
        pass

    @abstractmethod
    def instance_count(self):
        pass

    def strength(self):
        return self.__strength

    def is_alive(self):
        return self.__alive

    def f_set_world(self, world):
        self.__world = world

    def f_world(self):
        return self.__world

    def f_set_location(self, location):
        self.__location = location

    def f_location(self):
        return self.__location

    @staticmethod
    def f_fights_back():
        return True

    def f_apparent_strength(self):
        return 0 if self.__cloaked else self.strength()

    def f_apparent_type(self):
        return Soil if self.__cloaked else type(self)

    def f_appears_poisonous(self):
        return self.__poisonous and not self.__cloaked

    def f_add_organ(self, organ):
        self.f_expend(organ.creation_cost())
        if len(self.__organs) < self.__MAX_ORGANS:
            self.__organs.append(organ)

    def f_defensive_damage(self):
        damage = 0
        for organ in self.__organs:
            damage += organ.f_defensive_damage()
        return damage

    def f_metabolic_cycle(self):
        for organ in self.__organs:
            organ.f_new_turn()
            self.f_expend(organ.maintenance_cost())
        self.f_expend(self.__MAINTENANCE_COST)

    def f_cap_strength(self):
        self.__strength = min(self.__strength, self.__MAX_STRENGTH)

    def f_feed(self, food_energy):
        if self.__alive:
            self.__strength += food_energy

    def f_expend(self, food_energy):
        self.__strength -= food_energy
        if self.__strength < 0:
            self.f_die()

    def f_die(self):
        if self.__alive:
            self.destroyed()
        self.__strength = 0
        self.__alive = False

    def f_replace_me_with(self, replacement):
        self.__world.replace(self, replacement)

    def f_attack(self, defender):
        if not defender.f_fights_back():
            return self.__attacker_wins(defender)
        if not self.f_fights_back():
            return self.__defender_wins(defender)
        if self.strength() > defender.strength():
            return self.__attacker_wins(defender)
        return self.__defender_wins(defender)

    def __defender_wins(self, defender):
        defender.f_feed(self.strength() - self.f_defensive_damage())
        self.f_die()
        return defender

    def __attacker_wins(self, defender):
        self.f_feed(defender.strength() - defender.f_defensive_damage())
        defender.f_die()
        return self

    def f_cloak(self):
        self.__cloaked = True

    def f_uncloak(self):
        self.__cloaked = False

    def f_is_cloaked(self):
        return self.__cloaked

    def f_become_poisonous(self):
        self.__poisonous = True


class Soil(Creature):
    __PLANT_GROWTH_PROBABILITY = 0.01
    __instance_count = 0
    colour = ''

    def __init__(self):
        super().__init__()
        Soil.__instance_count += 1

    def do_turn(self):
        if random.random() < self.__PLANT_GROWTH_PROBABILITY:
            self.become_plant()

    def become_plant(self):
        self.f_replace_me_with(Plant())

    @classmethod
    def instance_count(cls):
        return Soil.__instance_count

    @classmethod
    def destroyed(cls):
        Soil.__instance_count -= 1

    @staticmethod
    def f_fights_back():
        return False

    def f_expend(self, food_energy):
        pass

    def f_grant_initial_strength(self):
        pass

    def f_feed(self, food_energy):
        pass

    def f_die(self):
        pass


class Plant(Creature):
    __instance_count = 0
    colour = '#d2f53c'

    def __init__(self):
        super().__init__()
        Plant.__instance_count += 1
        self.f_feed(PhotoGland.CREATION_COST + Propagator.CREATION_COST)
        PhotoGland(self)
        self.propagator = PlantPropagator(self)

    @staticmethod
    def f_fights_back():
        return False

    def do_turn(self):
        if self.strength() > Creature.MAX_STRENGTH:
            self.propagator.give_birth(self.strength() / 2, Direction.random())

    @classmethod
    def instance_count(cls):
        return Plant.__instance_count

    @classmethod
    def destroyed(cls):
        Plant.__instance_count -= 1


class PoisonDrop(Creature):
    F_DISSIPATION_RATE = 0.5
    __instance_count = 0
    colour = 'black'

    def __init__(self, volume):
        super().__init__()
        self.f_feed(1 + volume)
        self.__gland = PoisonGland(self)
        self.__gland.add_poison(volume)
        super().f_expend(volume)
        PoisonDrop.__instance_count += 1

    def f_apparent_type(self):
        return Soil

    def f_expend(self, food_energy):
        pass

    def do_turn(self):
        volume = math.ceil(self.__gland.current_volume() * self.F_DISSIPATION_RATE)
        self.__gland.remove_poison(volume)
        if self.__gland.current_volume() <= 0:
            self.f_die()

    @classmethod
    def instance_count(cls):
        return PoisonDrop.__instance_count

    @classmethod
    def destroyed(cls):
        PoisonDrop.__instance_count -= 1


class Direction(Enum):
    N = (0, -1)
    NE = (1, -1)
    E = (1, 0)
    SE = (1, 1)
    S = (0, 1)
    SW = (-1, 1)
    W = (-1, -0)
    NW = (-1, -1)

    def __init__(self, dx, dy):
        self.dx, self.dy = dx, dy

    # noinspection PyArgumentList
    def opposite(self):
        return Direction((-self.dx, -self.dy))

    # noinspection PyTypeChecker
    @classmethod
    def random(cls):
        return random.choice(list(cls))


class Organ(ABC):
    F_CREATION_COST = None
    F_USE_COST = None
    F_MAINTENANCE_COST = None

    def __init__(self, host: Creature):
        self.__host = host
        host.f_add_organ(self)
        self.__uses_this_turn = 0  # currently affects only Cilia

    def host(self):
        return self.__host

    def creation_cost(self):
        return self.F_CREATION_COST

    def use_cost(self):
        return self.F_USE_COST

    def maintenance_cost(self):
        return self.F_MAINTENANCE_COST

    def f_new_turn(self):
        self.__uses_this_turn = 0

    def f_used_once(self):
        self.__uses_this_turn += 1

    def f_uses_this_turn(self):
        return self.__uses_this_turn

    def f_defensive_damage(self):
        return 0

    def f_host_would_be_alive_after_use(self):
        self.host().f_expend(self.use_cost())
        return self.__host.is_alive()


class Cilia(Organ):
    F_CREATION_COST = CREATION_COST = 100
    F_MAINTENANCE_COST = MAINTENANCE_COST = 10
    F_USE_COST = USE_COST = 20

    def move_in_direction(self, bearing):
        if self.f_host_would_be_alive_after_use() and self.f_uses_this_turn() == 0:
            self.f_used_once()
            self.host().f_world().move(self.host(), bearing)


class PhotoGland(Organ):
    F_CREATION_COST = CREATION_COST = 250
    F_MAINTENANCE_COST = MAINTENANCE_COST = -150


class Propagator(Organ, ABC):
    F_CREATION_COST = CREATION_COST = 50
    F_MAINTENANCE_COST = MAINTENANCE_COST = 5
    F_USE_COST = USE_COST = 100

    def give_birth(self, initial_energy, direction):
        self.host().f_expend(initial_energy)
        if self.f_host_would_be_alive_after_use():
            child = self.make_child()
            child.f_feed(initial_energy)
            self.host().f_world().drop_beside(self.host(), child, direction)

    @abstractmethod
    def make_child(self):
        pass


class PlantPropagator(Propagator):

    def make_child(self):
        return Plant()


class Cloaking(Organ):
    F_CREATION_COST = CREATION_COST = 500
    F_MAINTENANCE_COST = MAINTENANCE_COST = 10
    F_USE_COST = USE_COST = 100

    def cloak(self):
        if self.f_host_would_be_alive_after_use():
            self.host().f_cloak()

    def uncloak(self):
        self.host().f_uncloak()

    def maintenance_cost(self):
        return self.F_MAINTENANCE_COST + (self.F_USE_COST if self.host().f_is_cloaked() else 0)


class Sensor(Organ, ABC):
    F_DEFAULT_VALUE = None

    def sense(self, direction):
        if self.f_host_would_be_alive_after_use():
            target = self.host().f_world().creature_at_offset_from(self.host(), direction)
            return self.sensor_value(target)
        else:
            return self.F_DEFAULT_VALUE

    @abstractmethod
    def sensor_value(self, target):
        pass


class EnergySensor(Sensor):
    F_DEFAULT_VALUE = 0
    F_CREATION_COST = CREATION_COST = 100
    F_MAINTENANCE_COST = MAINTENANCE_COST = 10
    F_USE_COST = USE_COST = 2

    def sensor_value(self, target):
        return target.f_apparent_strength()


class CreatureTypeSensor(Sensor):
    F_DEFAULT_VALUE = Soil
    F_CREATION_COST = CREATION_COST = 100
    F_MAINTENANCE_COST = MAINTENANCE_COST = 10
    F_USE_COST = USE_COST = 2

    def sensor_value(self, target):
        return target.f_apparent_type()


class LifeSensor(Sensor):
    F_DEFAULT_VALUE = False
    F_CREATION_COST = CREATION_COST = 50
    F_MAINTENANCE_COST = MAINTENANCE_COST = 5
    F_USE_COST = USE_COST = 1

    def sensor_value(self, target):
        return target.f_apparent_type() != Soil


class PoisonSensor(Sensor):
    F_DEFAULT_VALUE = False
    F_CREATION_COST = CREATION_COST = 50
    F_MAINTENANCE_COST = MAINTENANCE_COST = 5
    F_USE_COST = USE_COST = 1

    def sensor_value(self, target):
        return target.f_appears_poisonous()


class PoisonGland(Organ):
    F_CREATION_COST = CREATION_COST = 500
    F_MAINTENANCE_COST = MAINTENANCE_COST = 20
    __RESERVOIR_CAPACITY = 1000
    __DAMAGE_MULTIPLIER = 4

    def __init__(self, host):
        super().__init__(host)
        self.host().f_become_poisonous()
        self.__reservoir_volume = 0

    def f_defensive_damage(self):
        return self.__reservoir_volume * self.__DAMAGE_MULTIPLIER

    def add_poison(self, to_add):
        if to_add <= 0:
            return
        to_add = min(self.host().strength(), to_add)
        self.host().f_expend(to_add)
        self.__reservoir_volume = min(self.__RESERVOIR_CAPACITY, self.__reservoir_volume + to_add)

    def remove_poison(self, to_remove):
        if to_remove > 0:
            self.__reservoir_volume = max(0, self.__reservoir_volume - to_remove)

    def current_volume(self):
        return self.__reservoir_volume

    def drop_poison(self, direction, volume_desired):
        if volume_desired <= 0:
            return
        volume = min(self.__reservoir_volume, volume_desired)
        self.__reservoir_volume -= volume
        drop = PoisonDrop(volume)
        self.host().f_world().drop_beside(self.host(), drop, direction)


class Spikes(Organ):
    F_CREATION_COST = CREATION_COST = 100
    F_MAINTENANCE_COST = MAINTENANCE_COST = 5
    F_DEFENSIVE_DAMAGE = DEFENSIVE_DAMAGE = 200

    def f_defensive_damage(self):
        return self.F_DEFENSIVE_DAMAGE
