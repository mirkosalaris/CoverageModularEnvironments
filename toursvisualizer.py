import math

import matplotlib.pyplot as plt
import numpy as np

from common import logger


class ToursVisualizer:
    """
    Class used to visualize the computed complex of tours. 
    
    'tours': an array whose element are the single tours of the agents.
    'length': total length. Sum of the lengths of all the single tours.
    'distances': matrix of distances between the nodes
    """

    def __init__(self, tours, length, distances):
        self.tours = tours
        self.length = length
        self.distances = distances

    def __get_distance(self, i, j):
        return self.distances[i][j]

    def draw(self, radius=1):
        """
        Draw the whole tour spreading the nodes on a circle according to their relative distances.
        Color differently the single tours to understand the divisions between different agents.
        INPUT:    "radius" is the radius of the circle
        
        """

        # setup colors of the drawing
        plt.gca().set_prop_cycle(plt.cycler('color', plt.cm.gist_ncar(np.linspace(0, 0.95, len(self.tours)))))

        theta = - math.pi / 2  # first point is at six o'clock w.r.t. the others

        origin_node = self.tours[0][0]
        # last_node will be the last visited node, apart from the origin node
        last_node = origin_node  # initialize last_node as the origin_node
        D = 0
        for tour in self.tours:
            logger.debug("tour: ", tour)
            # add coordinate of first point
            coordinates = [(0, 0)]
            for i in range(1, len(tour) - 1):  # index 0 and last index are just the origin node
                logger.debug("get distance between " + str(last_node) + " and " + str(tour[i]))
                d = self.__get_distance(last_node, tour[i])
                D += d
                delta_theta = d / self.length * 2 * math.pi
                theta += delta_theta

                x = radius * math.cos(theta)
                y = radius * math.sin(theta) + radius

                coordinates.append((x, y))
                last_node = tour[i]

            coordinates.append((0, 0))  # add coordinate of last point
            xs, ys = zip(*coordinates)
            plt.plot(xs, ys, label="tour n° " + str(self.tours.index(tour)))
            plt.plot(xs, ys, 'k+')  # black pluses representing nodes

        logger.debug("Theta: " + str(theta))
        logger.debug("D: " + str(D))
        plt.plot(0, 0, 'ro')  # a red dot to show the starting point
        plt.legend(loc='best')
        plt.axis('off')
