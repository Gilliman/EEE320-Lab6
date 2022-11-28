"""
An example multi-class creature system with a main class (Hunter) and a
subclass (LittleHunter). Here, LittleHunter is identical to Hunter. In
real multi-creature strategy, subclasses would have different behaviours
and be instantiated based on current game conditions.

version 1.13
2021-11-23

Python implementation: Greg Phillips
Based on an original design by Scott Knight and a series of
implementations in C++ and Java by Scott Knight and Greg Phillips
"""

from shared import Creature, Cilia, CreatureTypeSensor, Propagator, Direction, Soil, Plant


class Hunter(Creature):
    """
    Grows one Cilia, one CreatureTypeSensor, and one HunterPropagator. On
    each turn, reproduces if strength is high enough, then attempts to
    find a creature to attack. Babies are LittleHunter. If unable to attack,
    moves in a random direction.
    """

    __instance_count = 0

    def __init__(self):
        super().__init__()
        Hunter.__instance_count += 1
        self.cilia = None
        self.type_sensor = None
        self.womb = None

    def do_turn(self):
        if not (self.cilia and self.type_sensor and self.womb):
            self.create_organs()
        else:
            self.reproduce_if_able()
            did_attack = self.find_someone_to_attack()
            if not did_attack:
                self.cilia.move_in_direction(Direction.random())

    @classmethod
    def instance_count(cls):
        return Hunter.__instance_count

    @classmethod
    def destroyed(cls):
        Hunter.__instance_count -= 1

    def create_organs(self):
        if not self.cilia and self.strength() > Cilia.CREATION_COST:
            self.cilia = Cilia(self)
        if not self.type_sensor and self.strength() > CreatureTypeSensor.CREATION_COST:
            self.type_sensor = CreatureTypeSensor(self)
        if not self.womb and self.strength() > Propagator.CREATION_COST:
            self.womb = HunterPropagator(self)

    def reproduce_if_able(self):
        if self.strength() >= 0.9 * Creature.MAX_STRENGTH:
            for d in Direction:
                nursery = self.type_sensor.sense(d)
                if nursery == Soil or nursery == Plant:
                    self.womb.give_birth(self.strength()/2, d)
                    break

    def find_someone_to_attack(self):
        for d in Direction:
            victim = self.type_sensor.sense(d)
            if victim != Soil and victim != Hunter and victim != LittleHunter:
                self.cilia.move_in_direction(d)
                return True
        return False


class LittleHunter(Hunter):
    """
    Minimal implementation of a helper creature; in real use you would override at least the
    do_turn method. Helper creatures must be a subclasses of the main creature class,
    here the Hunter class, must call super().__init__(), and must not override __instance_count,
    instance_count(), and destroyed().
    """

    def __init__(self):
        super().__init__()


class HunterPropagator(Propagator):
    """ Hunters and LittleHunters always give birth to LittleHunters. """

    def make_child(self):
        return LittleHunter()
