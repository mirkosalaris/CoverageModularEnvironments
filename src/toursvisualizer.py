__all__ = ["FredToursVisualizer", "IntToursVisualizer"]

import math
import matplotlib.pyplot as plt
import numpy as np

from common import logger
from modularmatrix import ModularMatrix


class ToursVisualizer:
    """
    Class used to visualize the computed complex of tours.

    'tours': an array whose element are the single tours of the agents.
    'length': total length. Sum of the lengths of all the single tours.
    'distances': matrix of distances between the nodes
    """

    def __init__(self, tours, distances):
        assert isinstance(distances, ModularMatrix), "The distance matrix must be a modular matrix"
        # the two concrete classes initialize this attribute before calling super.__init__
        assert self.length is not None, "ToursVisualizer has not been initialized properly. Attribute length is None"

        self.tours = tours
        self.distances = distances

    def _get_distance(self, i, j):
        return self.distances[i, j]

    def draw(self, radius=1):
        """
        Draw the whole tour spreading the nodes on a circle according to their relative distances.
        Color differently the single tours to understand the divisions between different agents.

        INPUT:      "radius" is the radius of the circle
        """

        # setup colors of the drawing
        plt.gca().set_prop_cycle(plt.cycler('color', plt.cm.gist_ncar(np.linspace(0, 0.95, len(self.tours)))))

        theta = - math.pi / 2  # first point is at six o'clock w.r.t. the others

        origin_node = self.tours[0][0]
        # last_node will be the last visited node, apart from the origin node
        last_node = origin_node  # initialize last_node as the origin_node
        D = 0
        for tour in self.tours:
            logger.debug("tour: " + str(tour))
            # add coordinate of first point
            coordinates = [(0, 0)]
            for i in range(1, len(tour) - 1):  # index 0 and last index are just the origin node
                logger.debug("get distance between " + str(last_node) + " and " + str(tour[i]))
                d = self._get_distance(last_node, tour[i])
                logger.debug("Which is: " + str(d))
                D += d
                delta_theta = d / self.length * 2 * math.pi
                theta += delta_theta

                x = radius * math.cos(theta)
                y = radius * math.sin(theta) + radius

                coordinates.append((x, y))
                last_node = tour[i]

            coordinates.append((0, 0))  # add coordinate of last point
            xs, ys = zip(*coordinates)
            plt.plot(xs, ys, 'k+')  # black pluses representing nodes
            plt.plot(xs, ys, label="tour n° " + str(self.tours.index(tour)))

        logger.debug("Theta: " + str(theta))
        logger.debug("D: " + str(D) + " Length: " + str(self.length))
        plt.plot(0, 0, 'ro')  # a red dot to show the starting point
        plt.legend(loc='best')
        plt.axis('off')

    def _spread_on_circle(self, tour, origin, radius=1):
        """
        :param tour: list of nodes that represents a circular (start=end) tour
        :param origin: start node
        :param radius: int Optional, the radius of the circle on which to spread the nodes.
        :return: a list of 2-tuples representing the x,y coordinates, one tuple for each node.
        """

        if len(tour) == 0:
            return [(0, 0)]

        assert tour[0] == tour[-1], "The module tour must be circular"

        tour_length = self.distances.get_distance_along_path(origin, origin, tour)
        coordinates = []
        last_node = origin  # initialize last_node as the origin_node

        theta = - math.pi / 2  # first point is at six o'clock w.r.t. the others
        D = 0
        for node in tour:
            logger.debug("get distance between " + str(last_node) + " and " + str(node))
            d = self._get_distance(last_node, node)
            D += d
            delta_theta = d / tour_length * 2 * math.pi
            theta += delta_theta

            x = radius * math.cos(theta)
            y = radius * math.sin(theta) + radius

            coordinates.append((x, y))
            last_node = node

        return coordinates

    def _map_node_agents(self, coordinates, module_inside_tour):
        """

        :param coordinates: a list of 2-tuples
        :param module_inside_tour: a list of nodes
        :return: a list of list of coordinates and a list of agents. The coordinates are exactly the coordinates in
        input but split according to which agent visits which node. The agents list is the list of agents who visit
        the module
        """
        assert len(coordinates) == len(module_inside_tour) + 2, \
            "Coordinates and module tour's length are not compatible" \
            + "\nCoordinates: " + str(coordinates) + "(len: " + str(len(coordinates)) + ")" \
            + "\nmodule_inside_tour: " + str(module_inside_tour) + "(len: " + str(len(module_inside_tour)) + ")"

        # ### IMPORTANT ###: remove first and last element (module entrance)
        # this will be added as first and last element (respectively of the first and last used agent)
        entrance = module_inside_tour[0]
        coordinates.pop(0)
        coordinates.pop(-1)

        split_coordinates = []

        first_agent, node_index = self._find_first_in_tour(module_inside_tour)

        # last used index for array coordinates (and 'module_inside_tour')
        c_index = 0
        agent = first_agent
        finished = False
        # cycle and split
        while agent < len(self.tours) and not finished:
            split_coordinates.append([])  # prepare empty list to insert coordinates

            tour = self.tours[agent]

            # This is useful only in the first iteration
            sliced_tour = tour[node_index:]

            node_index = 0

            i = 0
            while i < len(sliced_tour) and c_index < len(module_inside_tour):
                node = sliced_tour[i]

                # just skip the node if it is the entrance
                if node == entrance:
                    i += 1
                    if module_inside_tour[c_index] == entrance:
                        c_index += 1
                    continue

                assert node == module_inside_tour[c_index], \
                    "Something very wrong happened. single tour node %d, module tour node %d, c_index %d" \
                    % (node, module_inside_tour[c_index], c_index)

                split_coordinates[agent - first_agent].append(coordinates[c_index])
                c_index += 1
                i += 1

            agent += 1

            # If we have exhausted all the module then we have finished
            if c_index >= len(module_inside_tour):
                finished = True

        return split_coordinates, list(range(first_agent, agent))

    def _find_first_in_tour(self, module_inside_tour):
        agent = 0
        node_index = 0
        found_first = False
        while agent < len(self.tours) and not found_first:
            tour = self.tours[agent]
            node_index = 0
            while node_index < len(tour) and not found_first:
                if tour[node_index] in module_inside_tour:
                    found_first = True

                node_index += 1
            agent += 1

        # this must happen. If it doesn't there's something very very wrong
        assert found_first, "Module tour and agents' tours are not compatible"

        # decrement indexes to return to the right ones
        agent = agent - 1
        node_index = node_index - 1

        return agent, node_index

    def _fix(self, xs, ys, entrance_coords):
        xs = (entrance_coords[0],) + xs + (entrance_coords[0],)
        ys = (entrance_coords[1],) + ys + (entrance_coords[1],)

        return xs, ys


class FredToursVisualizer(ToursVisualizer):
    def __init__(self, tours, global_tour, distances):
        self.global_tour = global_tour
        self.length = distances.get_tour_length(global_tour)
        super().__init__(tours, distances)

    def draw_module(self, module):
        nodes = self.distances.get_nodes_in_module(module)
        # assumption: the global tour doesn't jump from a module to the other
        start = None
        end = None
        logger.debug("Nodes:" + str(nodes))
        logger.debug("Global tour:" + str(self.global_tour))

        # find the indexes between which there are the nodes of the current module
        for i in range(0, len(self.global_tour) - 1):  # NB: NOT the final node!
            if start is None and self.global_tour[i] in nodes:
                start = i
            elif self.global_tour[i] in nodes:
                end = i

        logger.debug("Start: " + str(start))
        logger.debug("End: " + str(end))
        module_entrance = self.distances.get_module_entrance_node(module)
        module_inside = self.global_tour[start:end + 1]
        module_tour = [module_entrance] + module_inside + [module_entrance]

        # calculate coordinates of the points
        coordinates = self._spread_on_circle(module_tour, module_entrance)
        entrance_coords = coordinates[0]

        # split the coordinates in different sets to get the mapping agents-coordinates
        split_coordinates, agents = self._map_node_agents(coordinates, module_inside)

        logger.debug("Split coordinates: " + str(split_coordinates))

        ### PLOT ###

        # slice the linspace to use only the colors corresponding to the agents
        linspace = np.linspace(0, 0.95, len(self.tours))
        sliced_linspace = linspace[agents]
        cycler = plt.cycler('color', plt.cm.gist_ncar(sliced_linspace))

        plt.gca().set_prop_cycle(cycler)
        for i in range(len(split_coordinates)):
            coords = split_coordinates[i]
            xs, ys = zip(*coords)
            xs, ys = self._fix(xs, ys, entrance_coords)
            plt.plot(xs, ys, label="Tour of agent n° " + str(agents[i]) + " in module " + str(module))
            plt.plot(xs, ys, 'k+')

        plt.plot(*entrance_coords, 'ro')  # a red dot to show the starting point
        plt.legend(loc='best')
        plt.axis('off')


class IntToursVisualizer(ToursVisualizer):
    # TODO: come up with a different visualization for this case.
    # Example:        _
    #  |----------     |
    #  |----------     |
    #  |----------     | --> blue
    #  |----------     |
    #  |----------    _|
    #  |----------     |
    #  |----------     | --> red
    #  |----------    _|

    def __init__(self, tours, distances):
        self.length = self.__calculate_length(distances, tours)
        super().__init__(tours, distances)

    @staticmethod
    def __calculate_length(distances, tours):
        trimmed_tours = [t[1:-1] for t in tours]
        origin = tours[0][0]

        global_tour = [origin] + sum(trimmed_tours, []) + [origin]

        length = distances.get_tour_length(global_tour)
        return length
