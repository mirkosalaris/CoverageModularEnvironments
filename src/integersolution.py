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
    intervals = _intervals_from_split_points(module_tour[0], splits, m, p)

    modular_matrix = ModularMatrix(distance_matrix, connections, p)
    tours = _calculate_tours(intervals, modular_matrix, module_tour, origin_node=module_tour[0])
    return tours


def _calculate_tours(intervals, modular_matrix, module_tour, origin_node):
    # trim the origin_node at the start and end of the tour
    trimmed_module_tour = module_tour[1:-1]

    tours = []
    for inter in intervals:  # inter is a tuple (start, end)
        tour = [origin_node]
        for i in range(inter[0], inter[1] + 1):
            displacement = modular_matrix.get_module_entrance_node(i)
            shifted_module_tour = [node + displacement for node in trimmed_module_tour]
            tour.extend(shifted_module_tour)
        tour.append(origin_node)

        tours.append(tour)

    return tours


def _recursive_interesting_split_points(splits, agents_number, lower, upper, interesting_split_points):
    """
    In-place modification of `interesting_split_points`, adding, in increasing order of index, all the split
    points that we will be using.

    :param splits: the complete list of splits points
    :param agents_number: the number of agents to consider
    :param lower: index of lower module to consider
    :param upper: index of higher module to consider
    :param interesting_split_points: the array of split points we used/are using
    :return: void. The function has in-place modification of `interesting_split_points`
    """

    if agents_number == 1:
        # add the split point (the last module to explore for the current agent) and return: no further splits needed
        interesting_split_points.append(upper)
        return

    # index of module that split in (about) half the two parts (lower and upper)
    main_split = splits[(lower, upper, agents_number)].get_split_point()

    # add to the array all the split points that come BEFORE the main one
    _recursive_interesting_split_points(
        splits, _lower_m(agents_number), lower, main_split, interesting_split_points)

    # if there still is an "upper" part to visit (if the "lower" part does NOT coincide with the whole part)
    if main_split != upper:
        # add to the array all the split points that come AFTER the main one
        _recursive_interesting_split_points(
            splits, _upper_m(agents_number), main_split + 1, upper, interesting_split_points)


def _intervals_from_split_points(origin_node: int, splits: dict, m: int, p: int) -> list:
    """
    Compute a list of pairs (2-tuples) "start_module, last_module", one pair for each agent
    :param splits: a list of `Split`s
    :param m: (int) the number of agents
    :param p: (int) the number of modules
    :return: a list of 2-tuples, each one representing the first and last module to explore for the corresponding agent
    """

    # list of split points that we will actually be using (from the long list of all possible split points)
    active_split_points = []
    # in place modification of `active_split_points`
    _recursive_interesting_split_points(splits, m, 0, p - 1, active_split_points)

    # calculate intervals starting from the active split points
    intervals = []
    first_interval = (origin_node, active_split_points[0])
    intervals.append(first_interval)

    # NOTICE: with m = len(active_split_pints), the LAST iteration will have i==m-2 (consider both the -1 and the
    # range() exclusion of the second value
    for i in range(0, len(active_split_points) - 1):
        new_interval = (active_split_points[i] + 1, active_split_points[i + 1])
        # if new_interval[0] > new_interval[1]: the interval will be correctly handled (ignored) later,
        # when calculating the tours. DO NOT PUT here (0, 0) to indicate it doesn't have to move. It would be
        # interpreted as an exploration of the first module.

        intervals.append(new_interval)

    # shift and return (because modules are indexed starting by 1)
    return [(ab[0] + 1, ab[1] + 1) for ab in intervals]


def _calculate_split_points(m, p, connections, tour_length):
    """Calculate, and return, all the split points of the current problem

    :param m: the number of robots
    :param p: the number of modules
    :param connections: an array containing the distances between consequent modules
    :param tour_length: the length of the path inside a single module
    :return: a dict of `Split`s indexed with tuples (lower_module, upper_module, number of agents)
    """
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
            splits[(i, j, k)] = Split(value, j, i, j, k)

    # Actual computation of all the other cases
    while k < math.ceil(m / 2):
        k += 1
        for i in range(p):
            for j in range(i + 1, p):  # case j==i already computed as base case
                _calculate_split(i, j, k, splits)  # in-place update of `splits`

    # calculate final split
    _calculate_split(0, p - 1, m, splits)

    return splits


def _base_case_1_module(module_index, connections, module_tour_length):
    # if we explore only one robot the cost of the path will be the length of the module we have to explore,
    # summed to (twice) the cost to reach the module
    return module_tour_length + 2 * sum(connections[:module_index])


def _base_case_1_robot(lower_module, upper_module, connections, module_tour_length):
    # if we have 1 robot, the cost of the path will be the module length multiplied by the number of modules,
    # summed to (twice) the cost to reach the farthest module
    return (upper_module - lower_module + 1) * module_tour_length + 2 * sum(connections[:upper_module])


def _calculate_split(i: int, j: int, k: int, splits: dict) -> int:
    """Calculate the split for the case (i,j,k) given the splits for all the "intermediate" cases.

    **Side effect**: add the new split to the 'splits' dictionary

    :param i: index of lower module
    :param j: index of higher module
    :param k: number of robots
    :param splits: dictionary containing splits for all the cases (i', j', k') with k' < k and any i < i' < j' < j
    :return: the split calculated. Notice: the split calculated is also added to the dict passed as argument
    """

    # if we already know it, just return it
    if (i, j, k) in splits:
        return splits[(i, j, k)]

    # this must be true, otherwise there's something very wrong. All values for k = 1 must have been already computed
    assert k > 1, "There is not split value for k <= 1. This should never ever happen"

    min_value, min_split = _search_optimal_split(i, j, k, splits)

    splits[(i, j, k)] = Split(min_value, min_split, i, j, k)
    return splits[(i, j, k)]


def _search_optimal_split(i: int, j: int, k: int, splits: dict, x_left: int = None, x_right: int = None) -> tuple:
    """Recursive function that search for the optimal split point between i and j modules considering k robots
    :param i: first module to consider
    :param j: last module to consider
    :param k: the number of robots
    :param splits: the dict of split points
    :param x_left: left extreme of the interval in which the split point has to be (filled during the recursion)
    :param x_right: right extreme of the interval in which the split point has to be (filled during the recursion)
    :return: (value of the min split, min_split)
    """

    # if this is the first invocation of the recursive function
    if x_left is None:
        x_left = i
    if x_right is None:
        x_right = j

    # take the point in the middle of the extremes (approx.)
    x = x_left + (x_right - x_left) // 2  # x is the candidate split point

    l = splits[(i, x, _lower_m(k))].get_value()

    if x == x_right:  # iff x_left==x_right
        return l, x  # min_value, min_split

    u = splits[(x + 1, j, _upper_m(k))].get_value()

    l_prime = splits[(i, x + 1, _lower_m(k))].get_value()
    u_prime = splits[(x + 2, j, _upper_m(k))].get_value() if x + 2 <= x_right else 0

    if l <= u and l_prime >= u_prime:  # then at least one between `x` and `x+1` is a split point
        # the optimal split is the one that yields the minimum value: [ min( max(l,u), max(l_prime, u_prime) ) ]
        if u >= l_prime:
            return l_prime, x + 1
        else:
            return u, x

    elif l >= u:  # we should explore the left part
        return _search_optimal_split(i, j, k, splits, x_left=x_left, x_right=x)
    else:  # we should explore the right part
        return _search_optimal_split(i, j, k, splits, x_left=x + 1, x_right=x_right)


def _lower_m(m):
    """Number of agents in the lower split"""
    return m // 2


def _upper_m(m):
    """Number of agents in the upper part"""
    return math.ceil(m / 2)


class Split:
    def __init__(self, value: float, split_point: int, i: int, j: int, k: int):
        """
        Store a split point and the corresponding parameters from which it has been computed (start, finish, #robots)

        :param value: cost of the solution which uses the current split point
        :param split_point: the index of the module that splits in (about) half the robots, into the upper and
            lower part. Notice, the split_point is considered to be part of the lower part.
        :param i: start module
        :param j: last module
        :param k: number of robots
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
