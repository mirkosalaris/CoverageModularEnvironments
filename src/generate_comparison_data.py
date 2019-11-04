# coding: utf-8

# In[3]:


import sys

sys.path.insert(0, '../src')
import numpy as np

from frederickson import Frederickson
from environment import Environment
from integersolution import integer_solution
from utils import *
import time

# Import heuristic AHP-mTSP
# Details of the heuristic can be found in "Balanced task allocation by partitioning the
# minmax multiple traveling salesperson" by Isaac Vandermeulen, Roderich Gross, and 
# Andreas Kolling which was published in the proceedings of AAMAS 2019.
sys.path.insert(0, "../ahp_mtsp")
import tsp as ahp

# In[4]:


# to save variables on file along to way
# (Notice: the calculations are sometimes very long. We should minimize the risk of losing information)
SAVE_FOLDER = "./saved_results/comparison/"
import os

os.makedirs(SAVE_FOLDER, exist_ok=True)

# the three base modules
little_module = "battle_creekhs_1"
middle_module = "Valleceppi_P0"
big_module = "scuola_3"

# the possible types of structures
# - random: modules are chosen randomly between the three base modules (uniform distribution)
# - decreasing: first third of the modules is composed by big modules, second third by middle
#               ones and the third by the little ones
# - increasing: inverse of "decreasing"
STRUCTURE_TYPES = ["random", "decreasing", "increasing"]

# distance between modules [fixed, for simplicity]
CONNECTION_DISTANCE = 20


# In[261]:


def random_module_sequence(types, number_of_modules):
    np.random.seed(0)  # seed to ensure reproducibility

    # being N = number_of_modules and being len(types) == 3
    # first generate a list of (N//3)*3 modules, just replicating the base modules
    # Notice: the list is not long N unless N % 3 == 0
    modules_list = types * (number_of_modules // len(types))

    # Now complete the list adding N % 3 modules (choosing randomly from the possible modules)
    missing_modules = np.random.permutation(types)[:number_of_modules % len(types)]
    modules_list.extend(missing_modules)

    # Permutate the modules and get the modules sequence
    modules_sequence = np.random.permutation(modules_list)
    return modules_sequence


def decreasing_module_sequence(types, number_of_modules):
    # initizialize to the last type [little] (then overwrite ONLY the lower parts)
    modules_sequence = [max(types)] * number_of_modules
    section_size = int(np.ceil(number_of_modules / len(types)))

    for i in range(min(len(types) - 1, number_of_modules)):
        modules_sequence[i * section_size:(i + 1) * section_size] = [types[i]] * section_size

    return modules_sequence


def increasing_module_sequence(types, number_of_modules):
    # initizialize to the first type (then overwrite ONLY the lower parts)
    modules_sequence = [min(types)] * number_of_modules
    section_size = int(np.ceil(number_of_modules / len(types)))

    for i in range(min(len(types) - 1, number_of_modules)):
        modules_sequence[i * section_size:(i + 1) * section_size] = [types[len(types) - 1 - i]] * section_size

    return modules_sequence


# In[272]:


big_matrix = get_building_matrix(big_module)
middle_matrix = get_building_matrix(middle_module)
little_matrix = get_building_matrix(little_module)

matrices = [big_matrix, middle_matrix, little_matrix]
types = list(range(len(matrices)))


def env_builder(structure_type, number_of_modules):
    modules_sequence = [max(types)] * number_of_modules

    if structure_type == "random":
        modules_sequence = random_module_sequence(types, number_of_modules)
    elif structure_type == "decreasing":
        modules_sequence = decreasing_module_sequence(types, number_of_modules)
    elif structure_type == "increasing":
        modules_sequence = increasing_module_sequence(types, number_of_modules)
    else:
        raise ValueError("Allowed values for structure type are: ", STRUCTURE_TYPES)

    distances = [CONNECTION_DISTANCE] * (number_of_modules - 1)

    env = Environment(matrices, modules_sequence, distances)

    return env


# # Batch calculations for different scenarios

# In[4]:


structures = ["random", "decreasing", "increasing"]
robots_numbers = [5, 10, 20]
modules_numbers = [30, 60, 120]


# #### DO NOT EXECUTE NEXT CELL
# The computation could be extremely slow and the results have been saved in files, so there is no need to recompute them unless you want to change parameters. Execute the cells after this to load the results from the files.

# In[423]:


# be sure to have logger level set to CRITICAL, to avoid slowdowns

smN = []

fred_max_len_list = []
int_max_len_list = []
#ahp_max_len_list = []

fred_time_list = []
int_time_list = []
mat_time_list = []
ahp_time_list = []

for N in modules_numbers:
    for m in robots_numbers:
        for s in structures:
            if m==10 and s!="increasing":
                print("skipped")
                continue
            smN.append((s, m, N))

            env = env_builder(s, N)

            print("Computing case s={}, m={}, N={}".format(s, m, N))

            ## FREDERICKSON CALCULATION ##
            fred_start_time = time.time()
            fred = Frederickson(env, m)
            fred_tours = fred.calculate()
            fred_max_len, fred_max_tour = max_length(fred_tours, env)
            fred_end_time = time.time()

            fred_time = fred_end_time - fred_start_time

            # speed optimization
            del fred
            del fred_tours
            del fred_max_tour

            ## INTEGER SOLUTION CALCULATION ##
            int_start_time = time.time()
            int_tours = integer_solution(env, m)
            int_max_len, int_max_tour = max_length(int_tours, env)
            int_end_time = time.time()

            int_time = int_end_time - int_start_time

            # speed optimization
            del int_tours
            del int_max_tour

            ## AHP SOLUTION CALCULATION ##
            #ahp_start_time = time.time()
            #mat_start_time = time.time()
            #mat = env.generate_matrix(for_real=True)
            #mat_end_time = time.time()
            #weights = [0] * len(mat)
            #start_depot = [0] * m
            #end_depot = start_depot
            #ahp_tours = ahp.minmax_mTSP(mat, weights, start_depot, end_depot)
            #ahp_max_len, ahp_max_tour = max_length(ahp_tours, env)
            #ahp_end_time = time.time()

            # speed optimization
            #del mat
            #del ahp_tours
            #del env

            #mat_time = mat_end_time - mat_start_time
            #ahp_time = ahp_end_time - ahp_start_time

            # Save in the lists for later analysis
            fred_max_len_list.append(fred_max_len)
            int_max_len_list.append(int_max_len)
            #ahp_max_len_list.append(ahp_max_len)

            fred_time_list.append(fred_time)
            int_time_list.append(int_time)
            #mat_time_list.append(mat_time)
            #ahp_time_list.append(ahp_time)

            save_variables(fred_max_len_list, "fred_max_len_list.dump", folder=SAVE_FOLDER)
            save_variables(int_max_len_list, "int_max_len_list.dump", folder=SAVE_FOLDER)
            #save_variables(ahp_max_len_list, "ahp_max_len_list.dump", folder=SAVE_FOLDER)
            save_variables(fred_time_list, "fred_time_list.dump", folder=SAVE_FOLDER)
            save_variables(int_time_list, "int_time_list.dump", folder=SAVE_FOLDER)
            #save_variables(mat_time_list, "mat_time_list.dump", folder=SAVE_FOLDER)
            #save_variables(ahp_time_list, "ahp_time_list.dump", folder=SAVE_FOLDER)
            save_variables(smN, "smN.dump", folder=SAVE_FOLDER)

# In[424]:


for i in range(len(smN)):
    print("Case (structure, number of robots, number of modules):", smN[i])
    print("len fred:", fred_max_len_list[i])
    print("len int:", int_max_len_list[i])
    #print("len ahp:", ahp_max_len_list[i])
    print("time fred:", fred_time_list[i])
    print("time int:", int_time_list[i])
    #print("time mat:", mat_time_list[i])
    #print("time ahp:", ahp_time_list[i])
    print()

save_variables("finito", "finito.dump", folder=SAVE_FOLDER)

