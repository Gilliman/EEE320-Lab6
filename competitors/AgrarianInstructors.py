"""
An example creature.

version 1.13
2021-11-23

Python implementation: Greg Phillips
Based on an original design by Scott Knight and a series of
implementations in C++ and Java by Scott Knight and Greg Phillips
"""

from shared import Creature, Propagator, PhotoGland, Direction


class SuperPlant(Creature):
    """
    Grows one womb (Propagator) and the maximum number of leaves(PhotoGlands).
    On each turn, if it has enough strength, gives birth to as many new SuperPlants
    as possible, in random directions.
    """

    minimum_baby_strength = Propagator.CREATION_COST + PhotoGland.CREATION_COST + 1
    __instance_count = 0

    def __init__(self):
        super().__init__()
        SuperPlant.__instance_count += 1
        self.womb = None
        self.leaf_count = 0
        self.all_leaves_grown = False

    def do_turn(self):
        if not (self.womb and self.all_leaves_grown):
            self.grow_organs()
        else:
            self.make_babies()

    @classmethod
    def instance_count(cls):
        return SuperPlant.__instance_count

    @classmethod
    def destroyed(cls):
        SuperPlant.__instance_count -= 1

    def grow_organs(self):
        if not self.womb and self.strength() > Propagator.CREATION_COST:
            self.womb = SuperPlantPropagator(self)
        while self.leaf_count < Creature.MAX_ORGANS - 1 and self.strength() > PhotoGland.CREATION_COST:
            PhotoGland(self)
            self.leaf_count += 1
        if self.leaf_count == Creature.MAX_ORGANS - 1:
            self.all_leaves_grown = True

    def make_babies(self):
        while self.strength() > self.minimum_baby_strength + Propagator.USE_COST:
            self.womb.give_birth(self.minimum_baby_strength, Direction.random())


class SuperPlantPropagator(Propagator):

    def make_child(self):
        return SuperPlant()
