from christofides import christofides_tsp
from errors import *


class Frederickson:

    def __init__(self, distance_matrix, m):
        self.distance_matrix = distance_matrix
        self.m = m
        self.__global_tour_calculated = False
        self.__global_tour = None

    def get_global_tour(self):
        if self.__global_tour_calculated:
            return self.__global_tour
        else:
            raise IllegalStateError("The global tour has not been calculated yet")

    def calculate(self):
        # Step 1: find a 1-tour
        tour, length = self.__find_1_tour()
        self.__global_tour = tour
        self.__global_tour_calculated = True

        # Step 2
        # For each agent, find the last vertex such that the cost from the origin, along its path,
        # is not greater than (j/m) * (length - 2*cmax)+cmax
        last_vertex = self.__last_vertices(tour, length)

        # Step 3
        # Obtain the j-tour by forming a subtour that:
        # - starts in the origin node reaching last_vertex[j-1]
        # - follows the global solution up to last_vertex[j]
        # - returns to the origin_node
        paths = self.__calculate_paths(last_vertex, tour)

        return paths

    def __find_1_tour(self):
        return christofides_tsp(self.distance_matrix)

    def __last_vertices(self, tour, length):
        origin_node = tour[0]
        cmax = max([self.distance_matrix[origin_node, i] for i in range(len(self.distance_matrix))])

        next_i = 1
        next_vertex = tour[0]

        last_vertex_index = [None] * self.m
        for j in range(0, self.m - 1):  # iterate on agents
            for i in range(next_i, len(tour)):
                path_cost = self.distance_matrix[origin_node, next_vertex] \
                            + self.distance_matrix.get_distance_along_path(next_vertex, tour[i], tour)
                if path_cost <= (j / self.m) * (length - 2 * cmax) + cmax:
                    last_vertex_index[j] = i

            next_i = last_vertex_index[j] + 1
            next_vertex = tour[next_i]

        last_vertex_index[-1] = len(tour) - 1  # the last element
        return last_vertex_index

    def __calculate_paths(self, last_vertex_indexes, tour):
        origin_node = tour[0]
        paths = []
        path_0 = tour[0:last_vertex_indexes[0] + 1]
        path_0.append(origin_node)
        paths.append(path_0)
        j = 0
        for j in range(1, self.m - 1):
            path_j = [origin_node]
            path_j.extend(tour[last_vertex_indexes[j - 1] + 1:last_vertex_indexes[j] + 1])
            path_j.append(origin_node)

            paths.append(path_j)

        # last agent
        path_last = [origin_node]
        path_last.extend(tour[last_vertex_indexes[j] + 1:])
        paths.append(path_last)

        return paths
