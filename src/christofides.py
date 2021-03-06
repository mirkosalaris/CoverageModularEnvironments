__all__ = ["christofides_tsp"]

### imports ###
import random


### Solve the TSP by means of Christofides' algorithm
#
# INPUT:	"data" is a distance matrix in the form D[i, j].
#           It can be a ModularMatrix or a numpy matrix
#
# OUTPUT:	"tour" is the final TSP solution, while "length"
#			is the solution length (i.e. the cost)
#
# NOTE:		"tour" may not start from 0, i.e., it could be
#			that tour[0] != 0. You can shift the result,
#           i.e., 1->0->2->1 can be rearrenged as 0->2->1->0
###
def christofides_tsp(data):

    random.seed(0)  # to ensure reproducibility

    # build a graph
    G = _build_graph(data)

    # build a minimum spanning tree
    MSTree = _minimum_spanning_tree(G)

    # find odd vertexes
    odd_vertexes = _find_odd_vertexes(MSTree)

    # add minimum weight matching edges to MST
    _minimum_weight_matching(MSTree, G, odd_vertexes)

    # find an eulerian tour
    eulerian_tour = _find_eulerian_tour(MSTree, G)

    current = eulerian_tour[0]
    tour = [current]
    visited = [False] * len(eulerian_tour)
    visited[current] = True

    length = 0

    for v in eulerian_tour[1:]:
        if not visited[v]:
            tour.append(v)
            visited[v] = True

            length += G[current][v]
            current = v

    length += G[tour[-1]][tour[0]]

    # make it circular
    tour.append(eulerian_tour[0])

    tour = _shift_tour(tour)

    return tour, length


def _build_graph(data):
    graph = {}
    for this in range(len(data)):
        for another_point in range(len(data)):
            if this != another_point:
                if this not in graph:
                    graph[this] = {}

                graph[this][another_point] = data[this, another_point]

    return graph


class _UnionFind:
    def __init__(self):
        self.weights = {}
        self.parents = {}

    def __getitem__(self, object):
        if object not in self.parents:
            self.parents[object] = object
            self.weights[object] = 1
            return object

        # find path of objects leading to the root
        path = [object]
        root = self.parents[object]
        while root != path[-1]:
            path.append(root)
            root = self.parents[root]

        # compress the path and return
        for ancestor in path:
            self.parents[ancestor] = root
        return root

    def __iter__(self):
        return iter(self.parents)

    def union(self, *objects):
        roots = [self[x] for x in objects]
        heaviest = max([(self.weights[r], r) for r in roots])[1]
        for r in roots:
            if r != heaviest:
                self.weights[heaviest] += self.weights[r]
                self.parents[r] = heaviest


def _minimum_spanning_tree(G):
    tree = []
    subtrees = _UnionFind()
    for W, u, v in sorted((G[u][v], u, v) for u in G for v in G[u]):
        if subtrees[u] != subtrees[v]:
            tree.append((u, v, W))
            subtrees.union(u, v)

    return tree


def _find_odd_vertexes(MST):
    tmp_g = {}
    vertexes = []
    for edge in MST:
        if edge[0] not in tmp_g:
            tmp_g[edge[0]] = 0

        if edge[1] not in tmp_g:
            tmp_g[edge[1]] = 0

        tmp_g[edge[0]] += 1
        tmp_g[edge[1]] += 1

    for vertex in tmp_g:
        if tmp_g[vertex] % 2 == 1:
            vertexes.append(vertex)

    return vertexes


def _minimum_weight_matching(MST, G, odd_vert):
    random.shuffle(odd_vert)

    while odd_vert:
        v = odd_vert.pop()
        length = float("inf")
        u = 1
        closest = 0
        for u in odd_vert:
            if v != u and G[v][u] < length:
                length = G[v][u]
                closest = u

        MST.append((v, closest, length))
        odd_vert.remove(closest)


def _find_eulerian_tour(MatchedMSTree, G):
    # find neigbours
    neighbours = {}
    for edge in MatchedMSTree:
        if edge[0] not in neighbours:
            neighbours[edge[0]] = []

        if edge[1] not in neighbours:
            neighbours[edge[1]] = []

        neighbours[edge[0]].append(edge[1])
        neighbours[edge[1]].append(edge[0])

    # finds the hamiltonian circuit
    start_vertex = MatchedMSTree[0][0]
    EP = [neighbours[start_vertex][0]]

    while len(MatchedMSTree) > 0:
        for i, v in enumerate(EP):
            if len(neighbours[v]) > 0:
                break

        while len(neighbours[v]) > 0:
            w = neighbours[v][0]

            _remove_edge_from_matchedMST(MatchedMSTree, v, w)

            del neighbours[v][(neighbours[v].index(w))]
            del neighbours[w][(neighbours[w].index(v))]

            i += 1
            EP.insert(i, w)

            v = w

    return EP


def _remove_edge_from_matchedMST(MatchedMST, v1, v2):
    for i, item in enumerate(MatchedMST):
        if (item[0] == v2 and item[1] == v1) or (item[0] == v1 and item[1] == v2):
            del MatchedMST[i]

    return MatchedMST


def _shift_tour(tour, origin_node=0):
    """Shift the tour representation such that it starts from the origin_node"""
    assert tour[0] == tour[-1]

    if tour[0] != origin_node:
        tour.pop(0)  # remove first element
        shift = tour.index(origin_node)  # calculate how much to shift

        # shift and add at the end the origin_node
        return tour[shift:] + tour[:shift] + [origin_node]