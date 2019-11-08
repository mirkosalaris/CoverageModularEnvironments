import math
import pickle

from fileio import parse_file

SOURCES_FOLDER = "../resources/environments/extracted/"
SAVE_FOLDER = "../Notebooks/saved_results/comparison_v1/"


def get_building_matrix(building, source_folder=SOURCES_FOLDER):
    filename = source_folder + building + ".txt"
    _, matrix = parse_file(filename)
    return matrix


def save_variables(variables, filename, folder=SAVE_FOLDER):
    with open(folder + filename, 'wb') as f:
        pickle.dump(variables, f)


def load_variables(filename, folder=SAVE_FOLDER):
    with open(folder + filename, 'rb') as f:
        return pickle.load(f)


def max_length(tours, environment):
    """
    :returns a tuple (max_value, max_tour), where 'max_value' is the distance covered by the robot
    that covers the maximum distance and 'max_tour' is the correspondent tour
    """
    max_tour = None
    max_value = 0
    for t in tours:
        t_length = environment.get_distance_along_path(t[0], t[-1], t)
        if t_length > max_value:
            max_value = t_length
            max_tour = t

    return max_value, max_tour


def avg_length(tours, environment):
    length_sum = 0
    for t in tours:
        length_sum += environment.get_distance_along_path(t[0], t[-1], t)

    return length_sum / len(tours)


def std_length(tours, environment):
    avg = avg_length(tours, environment)

    std_sum = 0
    for t in tours:
        length = environment.get_distance_along_path(t[0], t[-1], t)
        std_sum += (length - avg) ** 2

    std = math.sqrt(std_sum / len(tours))

    return std


def count_modules(tours, env):
    modules_visited = []
    for tour in tours:
        modules = [env.get_module_and_index(tour[i])[0].index for i in range(len(tour))]
        number_of_modules_visited = len(set(modules[1:-1]))
        modules_visited.append(number_of_modules_visited)

    return modules_visited