import math

from christofides import christofides_tsp


def integer_solution(distance_matrix, m, p, connections):
    floor_tour, floor_tour_length = christofides_tsp(distance_matrix)

    splits = {}

    # Calculation of the two base cases

    # Base case 1: only one floor
    for i in range(p):
        for k in range(1, m+1):
            value = __base_case_1_floor(i, connections, floor_tour_length)
            splits[(i, i, k)] = Split(value, i, i, i, k)

    # Base case 2: only one robot
    k = 1
    for i in range(p):
        for j in range(i, p):
            value = __base_case_1_robot(i, j, connections, floor_tour_length)
            splits[(i, j, k)] = Split(value, None, i, j, k)

    # Actual computation of all the other cases
    while k < math.ceil(m/2):
        k += 1
        for i in range(p):
            for j in range(i, p):
                __calculate_split(i, j, k, splits)  # splits dict is automatically updated

    # calculate final split
    __calculate_split(0, p-1, m, splits)

    return splits
    # TODO: return a list of tours then list recursively all split_points


def __base_case_1_floor(floor, connections, floor_tour_length):
    return floor_tour_length + 2*sum(connections[:floor])


def __base_case_1_robot(lower_floor, upper_floor, connections, floor_tour_length):
    return (upper_floor - lower_floor + 1) * floor_tour_length + 2*sum(connections[:upper_floor])


def __calculate_split(i, j, k, splits):
    if (i, j, k) in splits:
        return splits[(i, j, k)]

    # this must be true, otherwise there's something very wrong. All values for k = 1 must have been already computed
    assert k > 1

    min_value = None
    min_split = None
    for x in range(i, j):
        l = splits[(i, x, k // 2)].get_value()
        u = splits[(x + 1, j, math.ceil(k / 2))].get_value()
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


class Split:
    def __init__(self, value, split_point, i, j, k):
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
