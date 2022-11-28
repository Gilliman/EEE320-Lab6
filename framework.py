"""
The BugBattle competition framework, including the graphical user
interface and simulation engine. The simulation engine runs in a separate
process to improve performance.

version 1.13
2021-11-23

Python implementation: Greg Phillips
Based on an original design by Scott Knight and a series of
implementations in C++ and Java by Scott Knight and Greg Phillips
"""

import random
import time
import re
import tkinter as tk
from multiprocessing import Pipe, Process

from shared import Soil

COLOURS = ['#e6194b', '#0082c8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#fabebe',
           '#008080', '#e6beff', '#aa6e28', '#800000', '#aaffc3', '#808000', '#ffd8b1',
           '#000080', '#808080', '#e6194b', '#0082c8', '#f58231', '#911eb4', '#46f0f0',
           '#f032e6', '#fabebe', '#008080', '#e6beff', '#aa6e28', '#800000', '#aaffc3',
           '#808000', '#ffd8b1', '#000080', '#808080']
EMPTY_COLOUR = '#fffac8'


def create_simulation(sim_end, world_width):
    simulation = Simulation(sim_end, world_width)
    simulation.run()


class Receiver:

    def __init__(self, connection, event_loop, listeners):
        self.connection, self.event_loop, self.listeners = connection, event_loop, listeners

    def receive(self):
        snapshot = None
        while self.connection.poll():
            snapshot = self.connection.recv()
        if snapshot:
            for listener in self.listeners:
                if snapshot.turn_count == 0:
                    listener.initialize(snapshot)
                else:
                    listener.changed(snapshot)
        self.event_loop.after(10, self.receive)


class BugBattle(tk.Frame):
    """
    The main window, including components, event handling, and the main
    simulation event loop.
    """

    def __init__(self, root, world_width, competitor_classes):
        tk.Frame.__init__(self, master=root)
        self.root = root
        self.grid()
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        world_view = WorldView(self, world_width)
        scoreboard = ScoreBoard(self)
        sim_end, gui_end = Pipe()
        proxy = SimulationProxy(gui_end)
        control_panel = ControlPanel(self, proxy, competitor_classes)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        control_panel.grid(row=0, column=0, sticky=tk.N)
        scoreboard.grid(row=1, column=0, sticky=tk.N, pady=20)
        world_view.grid(row=0, column=1, rowspan=2)
        receiver = Receiver(gui_end, self, [world_view, scoreboard, control_panel])
        self.simulation = Process(target=create_simulation, args=(sim_end, world_width))
        self.simulation.start()
        receiver.receive()
        sim_end.close()

    def on_closing(self):
        self.simulation.terminate()
        self.root.destroy()


class WorldView(tk.Canvas):
    """
    Displays the BugBattle world on a tk.Canvas.
    The World is represented as a square grid of cells, each CELL_SIZE wide, and each
    displaying the colour of the creature found at that location in the World.
    """

    CELL_SIZE = 7  # 11 is 1080p

    def __init__(self, master, world_width):
        width = self.CELL_SIZE * world_width
        super().__init__(master, width=width, height=width, background=EMPTY_COLOUR, borderwidth=0,
                         highlightthickness=0)
        self.tiles = []
        self.initialize_tiles(world_width)
        self.previous = [None] * world_width * world_width

    def initialize(self, snapshot):
        self.update_tiles(snapshot.colours)

    def changed(self, snapshot):
        self.update_tiles(snapshot.colours)

    def initialize_tiles(self, world_width):
        """Create the tiles representing the world, setting each to transparent."""
        w = self.CELL_SIZE
        for row in range(world_width):
            for column in range(world_width):
                tile = self.create_oval(column * w, row * w,
                                        (column + 1) * w, (row + 1) * w,
                                        fill='', width=0)
                self.tiles.append(tile)

    def update_tiles(self, colours):
        for index, colour in enumerate(colours):
            if colour != self.previous[index]:
                self.itemconfigure(self.tiles[index], fill=colour)
        self.previous = colours


class SimulationProxy:

    def __init__(self, connection):
        self.connection = connection

    def reset(self, competitor_classes, interval):
        self.connection.send(ResetCommand(competitor_classes, interval))

    def set_interval(self, interval):
        self.connection.send(SetIntervalCommand(interval))

    def start(self):
        self.connection.send(StartCommand())

    def pause(self):
        self.connection.send(PauseCommand())


class StartCommand:

    @staticmethod
    def run_on(simulation):
        simulation.start()


class PauseCommand:

    @staticmethod
    def run_on(simulation):
        simulation.pause()


class SetIntervalCommand:

    def __init__(self, interval):
        self.interval = interval / 1000

    def run_on(self, simulation):
        simulation.set_interval(self.interval)


class ResetCommand:

    def __init__(self, competitor_classes, interval):
        self.competitor_classes, self.interval = competitor_classes, interval / 1000

    def run_on(self, simulation):
        simulation.reset(self.competitor_classes, self.interval)


class Snapshot:

    def __init__(self, simulation):
        self.tps = simulation.tps
        self.turn_count = simulation.turn_count
        self.game_over = simulation.game_over
        self.competitor_classes = simulation.competitor_classes
        self.counts = [competitor.instance_count() for competitor in simulation.competitor_classes]
        self.colours = [creature.colour for creature in simulation.world.locations]


class Simulation:
    INITIAL_PLANT_PROBABILITY = 0.12
    START_STRENGTH = 1500
    N_CREATURES = 3

    def __init__(self, connection, world_width):
        super().__init__()
        self.connection = connection
        self.competitor_classes = []
        self.interval = 0.5
        self.running = False
        self.game_over = False
        self.world = World(world_width)
        self.last_start = self.turn_count = self.tps = self.after_id = 0
        self.latest_snapshot_sent = None

    def reset(self, competitor_classes, interval):
        self.competitor_classes = competitor_classes
        self.set_interval(interval)
        self.running = False
        self.game_over = False
        self.last_start = None
        self.turn_count = 0
        self.tps = 0
        self.world.reset()
        self.grow_initial_plants()
        for index, competitor in enumerate(competitor_classes):
            setattr(competitor, '_{}__instance_count'.format(competitor.__name__), 0)
            competitor.colour = COLOURS[index]
            self.populate(competitor, self.N_CREATURES)
        self.connection.send(Snapshot(self))

    def set_interval(self, interval):
        self.interval = interval

    def create_snapshot(self):
        self.latest_snapshot_sent = Snapshot(self)

    def run(self):
        while True:
            if self.running and not self.game_over:
                start = time.time()
                self.calculate_tps(start)
                self.world.do_turn()
                self.turn_count += 1
                self.check_win()
                self.connection.send(Snapshot(self))
                turn_time = time.time() - start
                time.sleep(max(0.0, self.interval - turn_time))
                self.process_commands()
            else:
                self.connection.poll(0.5)
                self.process_commands()

    def process_commands(self):
        while self.connection.poll():
            command = self.connection.recv()
            command.run_on(self)

    def check_win(self):
        live_competitors = 0
        for competitor in self.competitor_classes:
            if competitor.instance_count() != 0:
                live_competitors += 1
        if live_competitors == 1:
            self.game_over = True

    def start(self):
        self.last_start = None
        self.running = True

    def pause(self):
        self.running = False

    def calculate_tps(self, start):
        if self.last_start:
            latest_tps = 1 / (start - self.last_start)
            self.tps = (0.8 * self.tps + latest_tps) / 1.8
        else:
            self.tps = 4
        self.last_start = start

    def grow_initial_plants(self):
        for soil in self.world.locations:
            if random.random() < self.INITIAL_PLANT_PROBABILITY:
                soil.become_plant()

    def populate(self, creature_class, n):
        """
        Put n instances of the creature_class at randomly-chosen locations in
        the world, possibly stepping on creatures that were already there.
        """
        for index in range(n):
            c = creature_class()
            c.f_feed(self.START_STRENGTH)
            self.world.place(c, random.randrange(len(self.world.locations)))


class World:
    """
    Looks after the location of all creatures in the World and allows
    each to perform its turn. Empty locations are represented by instances
    of Soil.
    """

    def __init__(self, width):
        self.width = width
        self.locations = []
        self.reset()

    def reset(self):
        if self.locations:
            for location in self.locations:
                location.destroyed()
        self.locations = [None for _ in range(self.width * self.width)]
        for index in range(len(self.locations)):
            self.place(Soil(), index)

    def place(self, creature, destination):
        creature.f_set_location(destination)
        self.locations[destination] = creature
        creature.f_set_world(self)

    def replace(self, original, replacement):
        try:
            destination = self.location_of(original)
            self.place(replacement, destination)
        except ValueError:
            pass

    def location_of(self, creature):
        loc = creature.f_location()
        if self.locations[loc] == creature:
            return loc
        else:
            raise ValueError()

    def creature_at(self, index):
        return self.locations[index]

    def creature_at_offset_from(self, creature, bearing):
        try:
            start = self.location_of(creature)
            target = self._location_offset(start, bearing)
            return self.creature_at(target)
        except ValueError:
            return Soil()

    def do_turn(self):
        """
        Executes the metabolic cycle for all creatures then permits each to
        do its turn.

        One subtlety: since creatures can move, if we simply iterated
        over the locations list for do_turn, it's possible that a creature moving
        west or south would get more than one turn in a single world turn (since
        it could have moved into a location whose turn had not yet come up). So,
        we call do_turn over a copy of the locations list.
        """
        for creature in self.locations:
            creature.f_metabolic_cycle()
        for ix, creature in enumerate(self.locations[:]):
            creature.do_turn()
            creature.f_cap_strength()
        for creature in self.locations[:]:
            if not creature.is_alive():
                self.replace(creature, Soil())

    def move(self, attacker, bearing):
        """
        If the creature is in the world, attempts to move it by attacking
        the location at the bearing from its initial location, back-filling
        the location it moved out of with a NullCreature.

        A creature might not be in the world if it has already been attacked on this turn
        but is now being permitted to have its turn; see the note on World.do_turn.
        """
        try:
            start = self.location_of(attacker)
        except ValueError:
            return
        self.place(Soil(), start)
        self.launch_attack(start, bearing, attacker)

    def launch_attack(self, start, bearing, attacker):
        battleground = self._location_offset(start, bearing)
        winner = attacker.f_attack(self.locations[battleground])
        self.place(winner, battleground)

    def drop_beside(self, origin_creature, dropped, bearing):
        try:
            start = self.location_of(origin_creature)
            self.launch_attack(start, bearing, dropped)
        except ValueError:
            pass

    def _location_offset(self, start, bearing):
        """Returns the start location offset by bearing, accounting for edge wrapping."""
        new_x = (start % self.width + bearing.dx) % self.width
        new_y = (start // self.width + bearing.dy) % self.width
        return new_y * self.width + new_x


class ScoreBoard(tk.Frame):
    DOT_SIZE = 20
    BORDER = 5
    CANVAS_SIZE = DOT_SIZE + 2 * BORDER
    FONT = ('Arial', 18)
    SMALL_FONT = ('Arial', 14)

    def __init__(self, master):
        super().__init__(master)
        self.grid(ipadx=20)
        self.columnconfigure(2, minsize=100)

        turn_label = tk.Label(self, text='Simulation turn:', font=self.FONT)
        turn_label.grid(row=0, column=1, sticky=tk.E)
        self.turn = tk.Label(self, text='{:8d}'.format(0), font=self.FONT)
        self.turn.grid(row=0, column=2, sticky=tk.E)

        tps_label = tk.Label(self, text='Turns per second:', font=self.SMALL_FONT)
        tps_label.grid(row=1, column=1, sticky=tk.E)
        self.tps = tk.Label(self, text='{:8.1f}'.format(0), font=self.SMALL_FONT)
        self.tps.grid(row=1, column=2, sticky=tk.E)

        spacer = tk.Label(self, text=' ', font=self.FONT)
        spacer.grid()
        self.boards = []

    def initialize(self, snapshot):
        self.grid_propagate(True)
        self.turn.config(text='{:8d}'.format(snapshot.turn_count))
        self.tps.config(text='{:8.1f}'.format(0))
        for row in self.boards:
            for widget in row:
                widget.grid_forget()
                widget.destroy()
        self.boards = []
        for ix, competitor in enumerate(snapshot.competitor_classes):
            dot = tk.Canvas(self, width=self.CANVAS_SIZE, height=self.CANVAS_SIZE, borderwidth=0,
                            highlightthickness=0, background=EMPTY_COLOUR)
            b = self.BORDER
            row = 3 + ix
            dot.create_oval(b, b, b + self.DOT_SIZE, b + self.DOT_SIZE, fill=COLOURS[ix], width=0)
            dot.create_rectangle(0, 0, self.CANVAS_SIZE - 1, self.CANVAS_SIZE - 1, fill='', outline='#cccccc', width=1)
            dot.grid(row=row, column=0, padx=10, pady=5, sticky=tk.NW)
            name = tk.Label(self, text=competitor.__name__, font=self.FONT)
            name.grid(row=row, column=1, sticky=tk.W)
            group = tk.Label(self, text=self.group_name(competitor), font=self.SMALL_FONT)
            group.grid(row=row, column=2, sticky=tk.W)
            score = tk.Label(self, text='{:8d}'.format(snapshot.counts[ix]), font=self.FONT)
            score.grid(row=row, column=3, sticky=tk.E)
            self.boards.append((dot, name, group, score))

    @staticmethod
    def group_name(competitor):
        name = competitor.__module__.split('.')[-1]
        return re.sub('([A-Z][a-z]*)', r'\1 ', name).strip()

    def changed(self, snapshot):
        self.grid_propagate(False)
        self.turn.config(text='{:8d}'.format(snapshot.turn_count))
        self.tps.config(text='{:8.1f}'.format(snapshot.tps))
        for ix, competitor in enumerate(snapshot.competitor_classes):
            label = self.boards[ix][3]
            label.config(text='{:8d}'.format(snapshot.counts[ix]))


class ControlPanel(tk.Frame):

    def __init__(self, master, simulation, competitor_classes):
        super().__init__(master)
        self.competitor_classes = competitor_classes
        self.chosen = []
        self.grid()
        self.simulation = simulation
        self.start_button = tk.Button(self, text='Start', command=self.start_simulation)
        self.pause_button = tk.Button(self, text='Pause', command=self.pause_simulation)
        self.same_button = tk.Button(self, text='Same again', command=self.choose_same)
        self.choose_button = tk.Button(self, text='Choose competitors', command=self.choose)
        self.simulation_interval = tk.DoubleVar()
        self.simulation_interval.set(250)
        self.speed_slider = tk.Scale(self, variable=self.simulation_interval, orient=tk.HORIZONTAL, length=200,
                                     label='simulation interval', from_=0, to_=1000, command=self.set_speed)
        self.start_button.grid(row=0, column=0)
        self.pause_button.grid(row=0, column=1)
        self.choose_button.grid(row=1, column=0)
        self.same_button.grid(row=1, column=1)
        self.speed_slider.grid(columnspan=2)
        self.buttons_none_chosen()

    def initialize(self, snapshot):
        pass

    def changed(self, snapshot):
        if snapshot.game_over:
            self.buttons_game_over()

    def choose(self):
        win_x = self.master.winfo_rootx() + 200
        win_y = self.master.winfo_rooty() + 50
        CompetitorSelector(self, self.competitor_classes, self.set_chosen, win_x, win_y)

    def set_chosen(self, chosen):
        self.chosen = chosen
        if chosen:
            self.buttons_ready()
        else:
            self.buttons_none_chosen()
        self.simulation.reset(chosen, self.simulation_interval.get())

    def choose_same(self):
        self.simulation.reset(self.chosen, self.simulation_interval.get())
        self.buttons_ready()

    def set_speed(self, _):
        self.simulation.set_interval(self.simulation_interval.get())

    def start_simulation(self):
        self.buttons_running()
        self.simulation.start()

    def pause_simulation(self):
        self.simulation.pause()
        self.buttons_ready()

    def buttons_none_chosen(self):
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED)
        self.choose_button.config(state=tk.NORMAL)
        self.same_button.config(state=tk.DISABLED)

    def buttons_ready(self):
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.choose_button.config(state=tk.NORMAL)
        self.same_button.config(state=tk.NORMAL)

    def buttons_running(self):
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.choose_button.config(state=tk.DISABLED)
        self.same_button.config(state=tk.DISABLED)

    def buttons_game_over(self):
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED)
        self.choose_button.config(state=tk.NORMAL)
        self.same_button.config(state=tk.NORMAL)


class CompetitorSelector(tk.Toplevel):

    def __init__(self, parent, competitor_classes, callback, win_x, win_y):
        super().__init__(parent)
        self.competitor_classes = competitor_classes
        self.callback = callback
        self.transient(parent)
        self.grab_set()
        self.grid()
        self.vars = []
        row = 0
        for row, competitor in enumerate(competitor_classes):
            v = tk.IntVar()
            self.vars.append(v)
            tk.Checkbutton(self, variable=v,
                           text=competitor.__name__).grid(sticky=tk.W, row=row, padx=10, columnspan=3)
        row += 1
        tk.Button(self, text='Cancel', command=self.destroy).grid(row=row, column=0, padx=10)
        tk.Button(self, text='All', command=self.everyone).grid(row=row, column=1, padx=10)
        tk.Button(self, text='None', command=self.no_one).grid(row=row, column=2, padx=10)
        tk.Button(self, text='Go', command=self.select_competitors).grid(row=row, column=3, padx=10, pady=10)
        self.geometry(f'+{win_x}+{win_y}')
        self.wait_window(self)

    def everyone(self):
        for v in self.vars:
            v.set(True)

    def no_one(self):
        for v in self.vars:
            v.set(False)

    def select_competitors(self):
        chosen = []
        for ix, v in enumerate(self.vars):
            if v.get():
                chosen.append(self.competitor_classes[ix])
        self.destroy()
        self.callback(chosen)
