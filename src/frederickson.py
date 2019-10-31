from christofides import christofides_tsp
from errors import *
from common import logger


class Frederickson:

    def __init__(self, environment, m):
        """Store parameters and compute the Frederickson path given a distance matrix of an environment and the
        number of agents available

        :param environment: a representation of the environment in terms of distance matrix
        :param m: number of agents"""
        self.environment = environment
        self.m = m
        self.__global_tour_calculated = False
        self.__global_tour = None

    def get_global_tour(self):
        """
        Returns the complete, single, tour, if available. Otherwise raise IllegalStateError

        :return: the complete, single, tour
        """
        if self.__global_tour_calculated:
            return self.__global_tour
        else:
            raise IllegalStateError("The global tour has not been calculated yet")

    def calculate(self):
        """
        Calculate the Frederickson list of paths, one for each agent.

        :return: paths, a list of lists of nodes
        """
        # Step 1: find a 1-tour
        tour, length = self._find_1_tour()
        self.__global_tour = tour
        self.__global_tour_calculated = True

        # Step 2
        # For each agent, find the last vertex such that the cost from the origin, along its path,
        # is not greater than (j/m) * (length - 2*cmax)+cmax
        last_vertices = self._last_vertices(tour, length)
        #logger.debug("last vertices: " + str(last_vertices))

        # Step 3
        # Obtain the j-tour by forming a subtour that:
        # - starts in the origin node reaching last_vertex[j-1]
        # - follows the global solution up to last_vertex[j]
        # - returns to the origin_node
        paths = self._calculate_paths(last_vertices, tour)

        return paths

    def _find_1_tour(self):
        return christofides_tsp(self.environment)

    def _last_vertices(self, tour, length):
        """For each agent, find the last vertex it has to visit

        That vertex has to be such that the cost to reach it from the origin to the first vertex of the path and from
        there following the complete tour path, is not greater than (j/m) * (length - 2*cmax)+cmax, where m is the
        number of agents, j is the incremental number of the agent under calculation and cmax is the cost to reach
        the most distant node
        :param tour: the complete, single, tour
        :param length: the length of the complete tour
        :return: a list of vertexes, each one being the last vertex that the corresponding agent has to visit
        """
        origin_node = tour[0]
        cmax = max([self.environment[origin_node, i] for i in range(len(self.environment))])
        #logger.debug("cmax" + str(cmax) + "length" + str(length))

        # tour[1] if available, otherwise tour[0]. This is just to avoid index out of bound exception
        subtour_first_vertex = tour[1 if len(tour) > 1 else 0]
        next_i = 1  # index of the next vertex (the subtour_first_vertex)

        # initialize the array that will store the results of the calculation (the last vertex for each agent)
        last_vertex_index = [None] * self.m
        for j in range(0, self.m - 1):  # iterate on agents, finding the "last vertex" for each path

            j_cost_limit = (j / self.m) * (length - 2 * cmax) + cmax

            # we will calculate this path cost incrementally. This is the base, from the origin to the first vertex.
            path_cost = self.environment[origin_node, subtour_first_vertex]

            for i in range(next_i, len(tour)-1):  # the -1 is because the origin node is duplicated!
                # incrementally calculate the path cost (if i==next_i no need to update the calculation)
                if i != next_i:
                    path_cost += self.environment[tour[i-1], tour[i]]

                if path_cost <= j_cost_limit:
                    last_vertex_index[j] = i

            # This happens when the previous agents already covered the whole graph
            if last_vertex_index[j] is None:
                # -1 because we start counting from 0 and another -1 because the origin node is repeated twice
                last_vertex_index[j] = len(tour)-2

            next_i = last_vertex_index[j] + 1
            subtour_first_vertex = tour[next_i]

        # make sure the last_vertex visited by the last agent is the LAST vertex.
        # notice: -2 and not -1 because we don't want to consider the origin_node as the last vertex.
        last_vertex_index[-1] = tour[len(tour) - 2] if len(tour) > 2 else 0  # index of the last element
        return last_vertex_index

    def _calculate_paths(self, last_vertex_indexes, tour):
        """
        Given the tour and the list of last vertices (one for each agent), calculate the paths, one for each agent.

        :param last_vertex_indexes: list of vertices, where each vertex is the last vertex that the corresponding
        agent has to visit
        :param tour: the complete, single, tour
        :return: paths, a list of lists of vertex. Each list is a path for the corresponding agent
        """
        origin_node = tour[0]
        paths = []
        path_0 = tour[0:last_vertex_indexes[0] + 1]
        path_0.append(origin_node)  # make the path come back to the origin
        paths.append(path_0)
        j = 0
        for j in range(1, self.m - 1):  # here the last agent is left out
            path_j = [origin_node]  # start in the origin
            path_j.extend(tour[last_vertex_indexes[j - 1] + 1:last_vertex_indexes[j] + 1])
            path_j.append(origin_node)  # make the path come back to the origin

            paths.append(path_j)

        # last agent
        path_last = [origin_node]
        path_last.extend(tour[last_vertex_indexes[j] + 1:])
        paths.append(path_last)

        return paths

