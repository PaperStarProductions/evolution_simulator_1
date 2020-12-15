import random
import tkinter as tk
import numpy as np
import time
import copy
import math
from tkinter.ttk import Progressbar

def make_tree(parent_attack,parent_reproduction,parent_base_health):
    """
    Takes parent genes and returns slightly mutated children genes.
    A tree's genes sum to 1
    :param parent_attack: the attack of the parent
    :param parent_reproduction: the reproduction of the parent
    :param parent_base_health: the health stat of the parent
    :return: a tupple of:
    (child_attack,
    child_reproduction,
    child_base_health,
    child_health)
    """
    num_genes = 3
    #store genes in an array
    gene_mutation = np.array([parent_attack, parent_reproduction, parent_base_health,0])
    # choose the gene to decrease
    loss = random.randint(0,num_genes-1)
    # chose the gene to increase
    gain = random.randint(0,num_genes-1)
    # generate the value of the change in genes
    val = (random.random()) / 50

    # if the mutation brings a gene's value to below zero pass on a clone instead
    if gene_mutation[loss] - val > 0:
        gene_mutation[loss] -= val
        gene_mutation[gain] += val
    return((gene_mutation[0],gene_mutation[1],gene_mutation[2],1000/(1.1-gene_mutation[2])-1000))




class Grid:
    def __init__(self,side_length,holes = False):
        assert side_length>=1
        #this creates four arrays which each represent one of the four characteristics of the trees
        #the ij space in each matrix represents the ijth tree
        #matricies are more efficent as a datatype

        #health starts high and decreases over time
        self.health = np.zeros((side_length,side_length))
        #The remaining three represent a tree's genome and sum to 1 for each tree
        self.attack = np.zeros((side_length,side_length))
        self.reproduction = np.zeros((side_length,side_length))
        self.base_health = np.zeros((side_length,side_length))

        #this stores the side length of the square for later use
        self.side=side_length
        #this stores whether or not the top half of the grid contains holes
        self.holes = holes

    def __getitem__(self, item):
        #index a tree's stats that are relevant to the graphics
        return (self.health[item],self.attack[item],self.reproduction[item])
    def set_holes(self,bool):
        #set whether there are holes (not implemented)
        self.holes = bool
    def Start_Simulation(self):
        #put the first tree down
        self.base_health[0, 0] = 0.5
        self.health[0,0]=1000
        self.attack[0, 0] = 0.0
        self.reproduction[0, 0] = 0.5
    def get_average_reproduction(self):
        #generate the numper of empty spaces in empty.spaces
        empty_spaces = np.sum(1*(0==self.base_health))

        #the 1 is added to not divide by 0
        return np.sum(self.reproduction)/(self.side*self.side-empty_spaces+1)
    def Cycle(self,number_of_cycles):
        #for each cycle

        for i in range(number_of_cycles):
            #for each tree, if it has negative health then kill it
            for j in range(self.side):
                for k in range(self.side):
                    if self.health[j,k] <0:
                        self.health[j,k]=0
                        self.attack[j, k] = 0
                        self.reproduction[j, k] = 0
                        self.base_health[j, k] = 0

            #choose one of the four directions for reproduction to potentially occur in this cycle
            #(this is efficient and doesnt really effect the behaviour of the trees)
            zeros = np.zeros(4,dtype=int)
            zeros[random.randint(0, 3)] = 1
            #for each space if it is empty then see if a surrounding tree corresponding to the randomly
            #chosen direction wants to reproduce
            for j in range(zeros[0],self.side-zeros[2]):
                for k in range(zeros[1],self.side-zeros[3]):
                    #if the space is empty
                    temp_tree = self.base_health[j,k]

                    if temp_tree == 0 :




                        j1,k1=np.array([j,k])-zeros[0:2]+zeros[2:4]

                        j1=int(j1)
                        k1=int(k1)
                        #the tree has a (reproduction**2)/5 chance of reproducing

                        if self.base_health[j1,k1]!=0:
                            prob = 5 * random.random()

                            if prob<(self.reproduction[j1,k1])**2 and not (self.holes==True and k+j<self.side and ((j%2)==1 and (k%2) == 1)):
                                self.attack[j,k],self.reproduction[j,k],self.base_health[j,k],self.health[j,k]=make_tree(self.attack[j1,k1],self.reproduction[j1,k1],self.base_health[j1,k1])

            # for eah direction of attack:right,left,down,up

            for offset in (np.array([1,0,0,0]),np.array([0,-1,0,0]),np.array([0,0,1,0]),np.array([0,0,0,-1])):
                #set defender location
                jmin,jmax,kmin,kmax=np.array([0,self.side,0,self.side])+offset
                #sed attacker location
                mmax,mmin,nmax,nmin=np.array([self.side,0,self.side,0])-offset
                #calculate an attack vector based
                life_change=(self.attack[mmin:mmax,nmin:nmax])*(5*self.reproduction[jmin:jmax, kmin:kmax])

                #remove zeroes
                life_change=life_change*(0!=(self.base_health[jmin:jmax, kmin:kmax]))
                self.health[jmin:jmax, kmin:kmax]-=life_change
                self.health[mmin:mmax,nmin:nmax]+= life_change


            #for each slot decrease tree lifespan by 1 if there is a tree there
            self.health=self.health-1*(0!=(self.base_health))

class simulation_visualisation:
    def __init__(self,side):


        self.window = tk.Tk()

        self.window.title("Evolution Simulator")
        self.canvas = tk.Canvas(self.window, width=1000, height=600)
        self.canvas.pack()
        self.side = side
        self.the_simulation = Grid(self.side)
        self.Play = True
        self.frame = tk.Frame(self.window)

        btn1 = tk.Button(self.frame, text="start_loop", bg="orange", fg="red", command = self.begin_simulation)
        btn1.pack(side = "left")
        btn2 = tk.Button(self.frame, text="pause", bg="orange", fg="red", command=self.pause)
        btn2.pack(side = "left")
        btn2 = tk.Button(self.frame, text="play", bg="orange", fg="red", command=self.play)
        btn2.pack(side = "left")
        btn3 = tk.Button(self.frame, text="add holes", bg="orange", fg="red", command=self.add_holes)
        btn3.pack(side="left")
        btn4 = tk.Button(self.frame, text="remove holes", bg="orange", fg="red", command=self.remove_holes)
        btn4.pack(side="left")
        self.spin = tk.Spinbox(self.frame, from_=1, to=100, width=5)
        self.spin.pack(side = "left")

        self.bar = Progressbar(self.frame, length=200)
        self.bar.pack(side="left")



        self.frame.pack()
        self.window.mainloop()
    def add_holes(self):
        self.the_simulation.set_holes(True)
    def remove_holes(self):
        self.the_simulation.set_holes(False)
    def pause(self):
        self.Play = False

    def play(self):
        self.Play = True
        while self.Play:
            self.print_grid()
            self.cycle(int(self.spin.get()))
            self.bar["value"]=self.the_simulation.get_average_reproduction()*100
    def begin_simulation(self):
        self.the_simulation.Start_Simulation()
        while self.Play:
            self.print_grid()
            self.cycle(int(self.spin.get()))
            self.bar["value"] = self.the_simulation.get_average_reproduction()*100
    def print_grid(self):

        self.canvas.delete("all")
        for i in range(self.side):
            for j in range(self.side):
                temp_health,temp_attack,temp_reproduction = self.the_simulation[i,j]
                if temp_health != 0:

                    increment = min(5,((max(temp_health/10,0))**0.5)//2)
                    width = 10
                    self.canvas.create_rectangle(50+width*i-increment,50+width*j-increment,50+width*i+increment,50+width*j+increment,fill="#ff{:02x}{:02x}".format(int(((1-temp_attack)*255)//1),int((temp_reproduction*255)//1)))
        #print the graph
        temp_print = []
        for i in range(100):
            temp_print.append([None]*100)
        for i in range(self.side):
            for j in range(self.side):
                temp_health,temp_attack,temp_reproduction = self.the_simulation[i,j]
                if not temp_health is None:
                    x= int(((temp_reproduction)*100)//1)
                    y= int(((temp_attack)*100)//1)
                    temp_print[x][y]=1
        for i in range(100):
            for j in range(100):
                if temp_print[i][j]==1:
                    self.canvas.create_rectangle(580+2*i,250-2*j,580+2*i,250-2*j)

        self.canvas.create_rectangle(580, 50, 580, 250)
        self.canvas.create_rectangle(580, 250, 780, 250)
        self.canvas.create_text(630,270,text="Reproduction factor --->")
        self.canvas.create_text(540, 200, text="Vampirism^")

        self.window.update_idletasks()
        self.window.update()

    def cycle(self,num_cycles):
        time1 = time.time()
        self.the_simulation.Cycle(num_cycles)
        print(time.time()-time1)


a = simulation_visualisation(45)






