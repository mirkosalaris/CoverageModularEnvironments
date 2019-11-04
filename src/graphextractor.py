__all__ = ['get_graph']

import numpy as np
from bs4 import BeautifulSoup

from graph import Graph


def find_centroid(space, scaling_factor):
    x = float(space.centroid.point["x"]) * scaling_factor
    y = float(space.centroid.point["y"]) * scaling_factor

    return [x, y]


def find_portals(space, soup, scaling_factor):
    portals = []  # it will contain tuples (x, y)

    for portal in space.find_all("portal"):
        segment_id = portal.linesegment.string
        segments = soup.find_all("linesegment", id=segment_id)
        if len(segments) > 0:  # ... otherwise if there's no data associated we can't do nothing about it
            xs = []
            ys = []
            for s in segments:
                xs.append(float(s.point["x"])*scaling_factor)
                ys.append(float(s.point["y"])*scaling_factor)

            x = sum(xs) / len(xs)
            y = sum(ys) / len(ys)

            portals.append((x, y))

    return portals


def connect_centroids_portals(graph, centroid_id, portals_ids):
    for portal_id in portals_ids:
        graph.add_edge(centroid_id, portal_id)


def connect_portals(graph, portals_ids):
    for por1_id in portals_ids:
        for por2_id in portals_ids:
            if por1_id != por2_id:
                graph.add_edge(por1_id, por2_id)


def get_graph(file, scaling_factor):
    """ Given an xml file of an environment calculate and return its graph representation

    :param file: either a filename string or an open file
    :param scaling_factor: the scale factor of the environment representation w.r.t. the desired measurement unit
    :return: a Graph, and a tuple containing the list of centroids and the list of portals
    """

    opened = False  # keep track of whether we opened the file (the function input was a filename) or not
    try:
        if type(file) == str:
            file = open(file, 'r')
            opened = True

        file.seek(0)
        soup = BeautifulSoup(file, 'xml')

        graph = Graph()

        centroids_list = []
        portals_list = []

        for space in soup.find_all("space", id=True):  # id=True to filter only spaces with an id (see poli.xml)
            centroid = find_centroid(space, scaling_factor)
            centroids_list.append(centroid)

            portals = find_portals(space, soup, scaling_factor)
            portals_list.append(portals)

            centroid_id = graph.add_node(centroid)
            portals_ids = graph.add_nodes(portals)

            # add edges between centroids and portals
            connect_centroids_portals(graph, centroid_id, portals_ids)

            # add edges between portals of the same space ("room")
            connect_portals(graph, portals_ids)

        return graph, (centroids_list, portals_list)

    except OSError as err:
        print("Cannot open the file", "OS error: {0}".format(err))

    finally:
        if opened:
            file.close()
