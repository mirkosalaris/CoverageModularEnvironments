from environment import Environment

__all__ = ["integer_solution"]

import math

from christofides import christofides_tsp


def modules_tours_and_costs(environment: Environment, agnostic_mode=False) -> tuple:
    """
    Calculate the base tours and their costs

    :param environment: a representation of the environment to explore. It contains information on the distances
    between nodes and information on the structure of the environment in terms of modules.
    :param agnostic_mode: if False (default), the algorithm is efficient and compute the tsp approximation once for
    each type of module. If True, the algorithm computes the tsp approximation for each module.
    :return (modules_tours, modules_cost)
     modules_tours is a list of the "base tours" (where each  tour is a list of nodes), one for each type of module
        in the environment
      modules_cost is a list of costs of the "base tours" both variables have the same length and the elements in the
        same position correspond to each other
    """
    # use christofides_tsp to get the path and its cost for each module
    tours = []
    costs = []

    # we make the computation once for each type, if we encounter a repeated module we re-use values
    # Notice: tours[i], costs[i], modules_type[i] refer to the same module
    modules_type = []

    for module in environment.modules:
        if agnostic_mode or module.type not in modules_type:
            tour, cost = christofides_tsp(module.distance_matrix)
        else:
            # find the first index that refers to a module of the same type
            module_index = modules_type.index(module.type)
            tour, cost = tours[module_index], costs[module_index]

        tours.append(tour)
        costs.append(cost)
        modules_type.append(module.type)

    return tours, costs


def integer_solution(environment: Environment, m: int, agnostic_mode=False) -> list:
    """
    It returns a list of tours, one for each of the `m` agents.

    :param environment: the modular matrix describing the structure of the environment
    :param m: number of agents
    :param agnostic_mode: if False (default), the algorithm is efficient and compute the tsp approximation once for
    each type of module. If True, the algorithm computes the tsp approximation for each module.
    :return: a list of tours, where each tour has to be covered by its corresponding agent
    """

    # single-module-tours and their costs
    modules_tours, modules_costs = modules_tours_and_costs(environment, agnostic_mode)
    splits = _calculate_split_points(m, environment.number_of_modules, environment.connections, modules_costs)
    intervals = _intervals_from_split_points(environment.origin_node, splits, m, environment.number_of_modules)

    tours = _calculate_tours(intervals, environment, modules_tours)
    return tours


def _calculate_tours(intervals, environment, modules_tours):
    """Calculate the tours, one for each agent, in terms of nodes to visit, in the right order in which they should
    be visited

    :param intervals: a list of 2-tuples where the first element represents the start of the interval and the last
    represents the end. Each tuple represents the interval of modules that should be explored by one agent alone.
    :param environment: an object that represent the environment to explore. It contains information on the distances
    between nodes and information on the structure of the environment in terms of modules.
    :param modules_tours:
    :return: a list of tours, one for each agent, where each tour is a list of nodes that the correspondent agent
    should explore, in the order in which they (the nodes) appear.
     """

    origin_node = environment.origin_node

    tours = []
    for inter in intervals:  # inter is a tuple (start_module, end_module)
        tour = [origin_node]

        if inter[0] == 1:  # if we are in the first module, the origin node should not be included again
            tour = []

        for i in range(inter[0], inter[1] + 1):
            module_tour = modules_tours[i-1]
            # trim the last node at the end of the tour: it is visited once, entering the node. There is no need to
            # pass again (explicitly)
            trimmed_module_tour = module_tour[:-1]

            # displacement needed to shift the indexes of the "base tour" to the proper indexes
            displacement = environment.get_module_entrance_node(i)
            shifted_module_tour = [node + displacement for node in trimmed_module_tour]
            tour.extend(shifted_module_tour)

        # make sure the last node is the origin node
        # Notice: it should be ok to always just add it, but it may be a problem if we are in the first module,
        # where, sometimes, the tour might naturally ends in the origin_node. To avoid too many considerations,
        # we can just check and add it if needed.
        if tour[-1] != origin_node:
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


def _calculate_split_points(m, p, connections, tours_lengths):
    """Calculate, and return, all the split points of the current problem

    :param m: the number of robots
    :param p: the number of modules
    :param connections: an array containing the distances between consequent modules
    :param tours_lengths: a list of the length of the path inside a single module, for each module
    :return: a dict of `Split`s indexed with tuples (lower_module, upper_module, number of agents)
    """
    splits = {}

    # Calculation of the two base cases
    # Base case 1: only one module
    for i in range(p):  # iterate on the modules
        value = _base_case_1_module(i, connections, tours_lengths[i])
        for k in range(1, m + 1):  # iterate on the number of robots
            splits[(i, i, k)] = Split(value, i, i, i, k)

    # Base case 2: only one robot
    k = 1
    for i in range(p):
        for j in range(i, p):
            value = _base_case_1_robot(i+1, j+1, connections, tours_lengths)
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


def _base_case_1_robot(lower_module, upper_module, connections, tours_lengths):
    # if we have 1 robot, the cost of the path will be the module length multiplied by the number of modules,
    # summed to (twice) the cost to reach the farthest module

    cost_to_farthest_module = sum(connections[:upper_module])  # no -1 because modules are indexed from 1
    cost_of_modules_exploration = sum(tours_lengths[lower_module - 1:upper_module])  # same reason
    return cost_of_modules_exploration + 2 * cost_to_farthest_module


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
