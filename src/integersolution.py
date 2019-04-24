__all__ = ["integer_solution"]

import math

from christofides import christofides_tsp
from modularmatrix import ModularMatrix


def integer_solution(distance_matrix, m, p, connections):
    """
    It returns a list of tours, one for each of the ``m`` agents.

    Args:
        distance_matrix (2d array): the matrix describing the distances between all the nodes in a single module
        m (int): number of agents
        p (int): number of modules
        connections (array of int): distances between modules
    """

    module_tour, module_tour_length = christofides_tsp(distance_matrix)

    splits = _calculate_split_points(m, p, connections, module_tour_length)
    intervals = _intervals_from_split_points(splits, m, p)

    modular_matrix = ModularMatrix(distance_matrix, connections, p)
    tours = _calculate_tours(intervals, modular_matrix, module_tour, origin_node=module_tour[0])
    return tours


def _calculate_tours(intervals, modular_matrix, module_tour, origin_node):
    trimmed_module_tour = module_tour[1:-1]

    tours = []
    for inter in intervals:
        tour = [origin_node]
        for i in range(inter[0], inter[1] + 1):
            displacement = modular_matrix.get_module_entrance_node(i)
            shifted_module_tour = [node + displacement for node in trimmed_module_tour]
            tour.extend(shifted_module_tour)
        tour.append(origin_node)

        tours.append(tour)

    return tours


def _intervals_from_split_points(splits, m, p):
    """
    Compute a list of pairs (2-tuples) "start_module, last_module", one pair for each agent
    :param splits: a list of `Split`s
    :param m: (int) the number of agents
    :param p: (int) the number of modules
    :return: a list of 2-tuples, each one representing the first and last module to explore for the corresponding agent
    """

    def __recursive_interesting_split_points(agents_number, lower, upper, interesting_split_points):
        if agents_number == 1:
            return

        main_split = splits[(lower, upper, agents_number)].get_split_point()

        # lower part
        __recursive_interesting_split_points(
            __lower_m(agents_number), lower, main_split - 1, interesting_split_points)

        interesting_split_points.append(main_split)

        # upper part
        __recursive_interesting_split_points(
            __upper_m(agents_number), main_split, upper, interesting_split_points)

        # end of nested function

    # calculate active ("used") split points
    active_split_points = []
    # in place modification of `active_split_points`
    __recursive_interesting_split_points(m, 0, p - 1, active_split_points)

    # calculate intervals starting from the active split points
    intervals = []
    first_interval = (0, active_split_points[0] - 1)
    intervals.append(first_interval)

    for i in range(0, len(active_split_points) - 1):
        new_interval = (active_split_points[i], active_split_points[i + 1] - 1)
        intervals.append(new_interval)

    last_interval = (active_split_points[-1], p - 1)
    intervals.append(last_interval)

    # shift and return (because modules are indexed starting by 1)
    return [(ab[0] + 1, ab[1] + 1) for ab in intervals]


def _calculate_split_points(m, p, connections, tour_length):
    splits = {}

    # Calculation of the two base cases

    # Base case 1: only one module
    for i in range(p):
        for k in range(1, m + 1):
            value = _base_case_1_module(i, connections, tour_length)
            splits[(i, i, k)] = Split(value, i, i, i, k)

    # Base case 2: only one robot
    k = 1
    for i in range(p):
        for j in range(i, p):
            value = _base_case_1_robot(i, j, connections, tour_length)
            splits[(i, j, k)] = Split(value, None, i, j, k)

    # Actual computation of all the other cases
    while k < math.ceil(m / 2):
        k += 1
        for i in range(p):
            for j in range(i, p):
                _calculate_split(i, j, k, splits)  # splits dict is automatically updated

    # calculate final split
    _calculate_split(0, p - 1, m, splits)

    return splits


def _base_case_1_module(module, connections, module_tour_length):
    return module_tour_length + 2 * sum(connections[:module])


def _base_case_1_robot(lower_module, upper_module, connections, module_tour_length):
    return (upper_module - lower_module + 1) * module_tour_length + 2 * sum(connections[:upper_module])


def _calculate_split(i, j, k, splits):
    if (i, j, k) in splits:
        return splits[(i, j, k)]

    # this must be true, otherwise there's something very wrong. All values for k = 1 must have been already computed
    assert k > 1

    min_value = None
    min_split = None
    for x in range(i, j):
        l = splits[(i, x, __lower_m(k))].get_value()
        u = splits[(x + 1, j, __upper_m(k))].get_value()
        if l > u:
            value = l
            split = x
        else:
            value = u
            split = x + 1

        if x == i or value < min_value:
            min_value = value
            min_split = split

    splits[(i, j, k)] = Split(min_value, min_split, i, j, k)
    return splits[(i, j, k)]


def __lower_m(m):
    """Number of agents in the lower split"""
    return m // 2


def __upper_m(m):
    """Number of agents in the upper part"""
    return math.ceil(m / 2)


class Split:
    """
    Store a split point and the corresponding parameters
    """

    def __init__(self, value, split_point, i, j, k):
        """

        :param value: cost of the solution with uses the current split point
        :param split_point: (int) the number of the module
        :param i:
        :param j:
        :param k:
        """
        self.__value = value
        self.__split_point = split_point
        self.__i = i
        self.__j = j
        self.__k = k

    def get_value(self):
        return self.__value

    def get_split_point(self):
        return self.__split_point

    def get_parameters(self):
        return self.__i, self.__j, self.__k
