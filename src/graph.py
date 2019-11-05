import math
from itertools import product
from math import inf


class Node:
    def __init__(self, node_id, coords):
        self.node_id = node_id
        self.x = coords[0]
        self.y = coords[1]

    def __hash__(self):
        return hash((self.node_id, self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.x == other.x and self.y == other.y


class Edge:
    EUCLIDEAN = 0
    MANHATTAN = 1

    def __init__(self, edge_id, n1, n2, edge_type=EUCLIDEAN):
        self.edge_id = edge_id
        self.n1 = n1
        self.n2 = n2
        if edge_type != Edge.EUCLIDEAN and edge_type != Edge.MANHATTAN:
            raise ValueError("Edge type should be either Edge.EUCLIDEAN or Edge.MANHATTAN"
                             ", {} found instead".format(edge_type))
        self.edge_type = edge_type

    @property
    def length(self):
        if self.edge_type == Edge.EUCLIDEAN:
            return math.sqrt((self.n1.x - self.n2.x) ** 2 + (self.n1.y - self.n2.y) ** 2)
        elif self.edge_type == Edge.MANHATTAN:
            return abs(self.n1.x - self.n2.x) + abs(self.n1.y - self.n2.y)


class Graph:

    def __init__(self):
        self.nodes = dict()
        self.next_node_id = 0

        self.edges = dict()  # store edges by id
        self.__edges_by_node = dict()  # store edges by node
        self.next_edge_id = 0

    def add_node(self, coords):
        """coords: (x,y) or [x,y]
        returns the id of the inserted node"""

        new_node = Node(self.next_node_id, coords)

        if new_node not in self.nodes.values():
            self.nodes[new_node.node_id] = new_node
            self.next_node_id += 1

            node_id = new_node.node_id
            self.__edges_by_node[node_id] = []

        else:
            # get key by value
            node_id = list(self.nodes.keys())[list(self.nodes.values()).index(new_node)]

        return node_id

    def add_nodes(self, coords):
        """coords: list of (x,y) tuples
        returns a list of the ids of the newly inserted nodes"""
        ids = []
        for c in coords:
            ids.append(self.add_node(c))

        return ids

    def add_edge(self, n1, n2, dist_type=Edge.EUCLIDEAN):
        """
        Add and edge between the two nodes
        Raises an exception if one of the nodes in input is not already in the graph

        :param n1: either a node_id or a node (in both cases, already in the graph)
        :param n2: either a node_id or a node (in both cases, already in the graph)
        :param dist_type: Either Edge.EUCLIDEAN or Edge.MANHATTAN
        :return: the id of the new edge
        """
        if type(n1) is int:
            n1 = self.nodes[n1]
        if type(n2) is int:
            n2 = self.nodes[n2]

        if n1 not in self.nodes.values() or n2 not in self.nodes.values():
            raise Exception("The nodes in input must already be in the graph before inserting an edge")

        new_edge = Edge(self.next_edge_id, n1, n2, dist_type)
        self.edges[new_edge.edge_id] = new_edge
        self.__edges_by_node[n1.node_id].append(new_edge)

        self.next_edge_id += 1

        return new_edge.edge_id

    def get_incidents_on_node(self, node):
        return list(self.__edges_by_node[node.node_id])


def floyd_warshall(n, edges):
    """ Calculate the distances between each pair of nodes.
    Assumption: the graph is undirected (and edges are listed only in one direction)

    :param n: number of nodes
    :param edges: list of tuples in the form (node1, node2, distance)

    :returns a 2d-matrix with nodes as indexes and distances as values"""

    # function adapted from https://rosettacode.org/wiki/Floyd-Warshall_algorithm#Python in Sept 2019

    rn = range(n)
    dist = [[inf] * n for _ in rn]  # matrix of distances
    # nxt = [[0] * n for _ in rn]  # matrix to retrieve the optimal path

    for i in rn:
        dist[i][i] = 0

    for u, v, w in edges:
        dist[u][v] = w
        dist[v][u] = w
        # nxt[u][v] = v
        # nxt[v][u] = v

    for k, i, j in product(rn, repeat=3):
        sum_ik_kj = dist[i][k] + dist[k][j]
        if dist[i][j] > sum_ik_kj:
            dist[i][j] = sum_ik_kj
            dist[j][i] = sum_ik_kj
            # nxt[i][j] = nxt[i][k]
            # nxt[j][i] = nxt[i][k]

    return dist


def edges_to_tuples(edges):
    """take a list of edges and return a list of tuples in the form (id_n1, id_n2, distance)"""
    tuples = []
    for e in edges:
        tuples.append((e.n1.node_id, e.n2.node_id, e.length))

    return tuples


def graph_to_distance_matrix(graph):
    n = len(graph.nodes)
    edges = edges_to_tuples(list(graph.edges.values()))
    return floyd_warshall(n, edges)
