import random
import tkinter as tk
import numpy as np
import time
from tkinter.ttk import Progressbar


NUM_GENES = 3

ATTACK = 0
REPRODUCTION = 1
BASE_HEALTH = 2
HEALTH = 3


def make_tree(parent_genomes):
    """
    Takes parent genes and returns slightly mutated children genes.
    A tree's genes sum to 1
    :param parent_genomes: the genome of the parents
    :return: the children's attributes
    """
    # store genes in an array
    num_parents = parent_genomes.shape[1]
    child_genomes = np.array(parent_genomes)
    # choose the gene to decrease
    loss = np.random.randint(low=0, high=NUM_GENES, size=num_parents)
    # chose the gene to increase
    gain = np.random.randint(low=0, high=NUM_GENES, size=num_parents)
    # generate the value of the change in genes
    val = np.random.random(size=num_parents) / 50

    # if the mutation brings a gene's value to below zero pass on a clone instead
    mutation_mask = child_genomes[loss, range(num_parents)] - val > 0
    val = val[mutation_mask]
    child_genomes[loss[mutation_mask], mutation_mask] -= val
    child_genomes[gain[mutation_mask], mutation_mask] += val
    healths = 1000 / (1.1 - child_genomes[BASE_HEALTH]) - 1000
    child_attributes = np.concatenate([child_genomes, healths[None, :]], axis=0)

    return child_attributes


class Grid:
    def __init__(self, side_length):
        assert side_length >= 1
        # this creates an array representing the four characteristics of the trees
        # the ij space in each matrix represents the ijth tree
        # matrices are more efficient as a datatype

        # health starts high and decreases over time
        # The remaining three represent a tree's genome and sum to 1 for each tree
        self.attributes = np.zeros((4, side_length, side_length))

        # this stores the side length of the square for later use
        self.side = side_length
        # this stores whether or not the top half of the grid contains holes
        self.holes = False

    def reset(self):
        # clear the grid and put the first tree down
        self.attributes[:] = 0
        self.attributes[[ATTACK, REPRODUCTION, BASE_HEALTH, HEALTH], 0, 0] = [0.0, 0.5, 0.5, 1000]

    def get_average_reproduction(self):
        alive_mask = self.attributes[BASE_HEALTH] > 0
        alive_count = np.prod(alive_mask.shape)
        return np.mean(self.attributes[REPRODUCTION, alive_mask]) if alive_count else 0

    def cycle(self, number_of_cycles):
        # for each cycle
        for i in range(number_of_cycles):
            # for each tree, if it has negative health then kill it
            kill_mask = self.attributes[HEALTH] < 0
            self.attributes[:, kill_mask] = 0

            base_healths = self.attributes[BASE_HEALTH]
            healths = self.attributes[HEALTH]
            attacks = self.attributes[ATTACK]
            reproductions = self.attributes[REPRODUCTION]

            # choose one of the four directions for reproduction to potentially occur in this cycle
            # (this is efficient and doesn't really effect the behaviour of the trees)
            zeros = np.zeros(4, dtype=int)
            zeros[random.randint(0, 3)] = 1
            # for each space if it is empty then see if a surrounding tree corresponding to the randomly
            # chosen direction wants to reproduce
            min_j, max_j = zeros[0], self.side - zeros[2]
            min_k, max_k = zeros[1], self.side - zeros[3]
            empty_mask = base_healths[min_j:max_j, min_k:max_k] == 0
            min_j1, max_j1 = zeros[2], self.side - zeros[0]
            min_k1, max_k1 = zeros[3], self.side - zeros[1]
            alive_mask = base_healths[min_j1:max_j1, min_k1:max_k1] > 0
            chance_mask = np.random.uniform(low=0, high=5, size=alive_mask.shape) < reproductions[min_j1:max_j1, min_k1:max_k1] ** 2
            reproduction_mask = empty_mask & alive_mask & chance_mask
            if self.holes:
                j_grid, k_grid = np.meshgrid(np.arange(empty_mask.shape[1]), np.arange(empty_mask.shape[0]))
                coords = np.stack([j_grid, k_grid], axis=2)
                hole_mask = ~((np.sum(coords, axis=2) < self.side) & (j_grid % 2 == 1) & (k_grid % 2 == 1))
                reproduction_mask &= hole_mask

            self.attributes[:, min_j:max_j, min_k:max_k][:, reproduction_mask] = make_tree(
                self.attributes[:, min_j1:max_j1, min_k1:max_k1][:NUM_GENES, reproduction_mask]
            )

            # for each direction of attack:right,left,down,up
            for offset in (np.array([1, 0, 0, 0]), np.array([0, -1, 0, 0]), np.array([0, 0, 1, 0]), np.array([0, 0, 0, -1])):
                # set defender location
                jmin, jmax, kmin, kmax = np.array([0, self.side, 0, self.side]) + offset
                # sed attacker location
                mmax, mmin, nmax, nmin = np.array([self.side, 0, self.side, 0]) - offset
                # calculate an attack vector based
                life_change = (attacks[mmin:mmax, nmin:nmax]) * (5 * reproductions[jmin:jmax, kmin:kmax])

                # remove zeroes
                life_change = life_change * (base_healths[jmin:jmax, kmin:kmax] != 0)
                healths[jmin:jmax, kmin:kmax] -= life_change
                healths[mmin:mmax, nmin:nmax] += life_change

            # for each slot decrease tree lifespan by 1 if there is a tree there
            healths -= base_healths != 0


class SimulationVisualization:
    def __init__(self, side):
        self.window = tk.Tk()

        self.window.title("Evolution Simulator")
        self.canvas = tk.Canvas(self.window, width=1000, height=600)
        self.canvas.pack()
        self.side = side
        self.grid = Grid(self.side)
        self.frame = tk.Frame(self.window)

        btn1 = tk.Button(self.frame, text="reset", bg="orange", fg="red", command=self.reset)
        btn1.config(width=12)
        btn1.pack(side="left")

        self.play = True
        self.play_switch = tk.Button(self.frame, text="", bg="orange", fg="red", command=self.switch_play)
        self.play_switch.config(width=12)
        self.play_switch.pack(side="left")
        self.switch_play()

        self.grid.holes = True
        self.holes_switch = tk.Button(self.frame, text="", bg="orange", fg="red", command=self.switch_holes)
        self.holes_switch.config(width=12)
        self.holes_switch.pack(side="left")
        self.switch_holes()

        self.spin = tk.Spinbox(self.frame, from_=1, to=100, width=5)
        self.spin.pack(side="left")

        self.bar = Progressbar(self.frame, length=200)
        self.bar.pack(side="left")

        self.frame.pack()
        self.reset()
        self.window.mainloop()

    def reset(self):
        self.grid.reset()
        self.play = True
        self.switch_play()
        self.print_grid()

    def switch_play(self):
        self.play = not self.play
        self.play_switch["text"] = "pause" if self.play else "resume"
        while self.play:
            self.print_grid()
            self.cycle(int(self.spin.get()))

    def switch_holes(self):
        self.grid.holes = not self.grid.holes
        self.holes_switch["text"] = "remove holes" if self.grid.holes else "add holes"

    def print_grid(self):
        self.canvas.delete("all")

        alive_mask = self.grid.attributes[HEALTH] > 0
        healths = self.grid.attributes[HEALTH, alive_mask]
        attacks = self.grid.attributes[ATTACK, alive_mask]
        reproductions = self.grid.attributes[REPRODUCTION, alive_mask]
        increments = np.minimum(5, ((healths / 10) ** 0.5) // 2)[:, None]

        # draw the grid
        width = 10
        side_range = np.arange(self.side)
        centers = 50 + width * np.stack(np.meshgrid(side_range, side_range), axis=2)[alive_mask]
        min_points = centers - increments
        max_points = centers + increments
        points = np.concatenate([min_points, max_points], axis=1)
        for (x0, y0, x1, y1), attack, reproduction in zip(points, attacks, reproductions):
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill="#ff{:02x}{:02x}".format(int((1 - attack) * 255), int(reproduction * 255)))

        # print the graph
        attributes = np.stack([reproductions, attacks], axis=1)
        rectangle_coords = np.array([580 + 1, 250 - 1]) + np.array([2, -2]) * (attributes * 100).astype(np.int)
        for x, y in rectangle_coords:
            self.canvas.create_rectangle(x, y, x, y)

        self.canvas.create_rectangle(580, 50, 580, 250)
        self.canvas.create_rectangle(580, 250, 780, 250)
        self.canvas.create_text(630, 270, text="Reproduction factor --->")
        self.canvas.create_text(540, 200, text="Vampirism^")

        # update the reproduction rate bar
        self.bar["value"] = self.grid.get_average_reproduction() * 100

        self.window.update_idletasks()
        self.window.update()

    def cycle(self, num_cycles):
        time1 = time.time()
        self.grid.cycle(num_cycles)
        print(time.time() - time1)


if __name__ == "__main__":
    SimulationVisualization(45)
