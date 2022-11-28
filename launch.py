"""
Configures and launches the BugBattle application.

Competitors live in the `competitors` module. To add a competitor
to the game, import its class and add it to the  `COMPETITOR_CLASSES`
tuple.

version 1.13
2021-11-23

Python implementation: Greg Phillips
Based on an original design by Scott Knight and a series of
implementations in C++ and Java by Scott Knight and Greg Phillips
"""


import tkinter as tk

from competitors.HuntingInstructors import Hunter
from competitors.AgrarianInstructors import SuperPlant

from framework import BugBattle

WORLD_WIDTH = 100
COMPETITOR_CLASSES = (Hunter, SuperPlant)

if __name__ == '__main__':
    root = tk.Tk()
    bb = BugBattle(root, WORLD_WIDTH, COMPETITOR_CLASSES)
    bb.master.title('BugBattle Multiprocess')
    bb.master.wm_resizable(0, 0)
    bb.mainloop()
