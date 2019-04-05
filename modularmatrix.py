from common import logger
from errors import IllegalParameterError


class ModularMatrix:
    """A Modular Matrix is like a usual distance matrix but it consists of repeated modules, meaning that it can be
    efficiently represented by a base matrix, that represent a module, repeated many times, connected by an edge"""

    def __init__(self, module_matrix, distance_between_modules, number_of_modules, connection_node=0):
        assert isinstance(distance_between_modules, int) and distance_between_modules >= 0
        assert isinstance(number_of_modules, int) and number_of_modules > 0

        self.base_matrix = module_matrix
        self.distance_between_modules = distance_between_modules
        self.number_of_modules = number_of_modules
        self.connection_node = connection_node

        self.base_size = len(module_matrix)

    def __getitem__(self, item):
        if isinstance(item, slice):
            raise NotImplementedError("Slicing not yet implemented")
            # return [self[i, j, k] for i in range(*item.indices(len(self)))
            #         for j in range(*item.indices(len(self[i])))
            #         for k in range(*item.indices(len(self[i][j])))]
        elif isinstance(item, tuple):

            if len(item) != self.ndim():
                raise IndexError("Tuple length not consistent with matrix dimensions. Expected: ",
                                 self.ndim(), ", got: ", len(item))

            if isinstance(item[0], slice) or isinstance(item[1], slice):
                raise NotImplementedError("Slicing not yet implemented")

            return self.__get_single_item(item)

        else:  # integer index
            # TODO: this should return a vector
            raise NotImplementedError("Currently only support single element indexing, using tuple")

    def __len__(self):
        return len(self.base_matrix) * self.number_of_modules

    def __get_single_item(self, item):
        """
        :param item: tuple of int. Its length must coincide with the number of dimensions of the matrix.
        :return: int The distance between the elements in the tuple
        """
        #                   i
        # |_________________.______          _
        # |  ^                                |
        # |  d_upper_to_conn_node             |
        # |                                   | modules that separate node i and node j
        # |                                   | ---> d_conn_to_conn
        # |     j                             |
        # |_____.__________________          _|
        # |  ^
        # |  d_lower_to_conn_node
        #
        # j is the 'lower_index'
        # i is the 'upper_index'

        assert isinstance(item, tuple)
        assert len(item) == self.ndim()

        lower_index = min(item)
        upper_index = max(item)
        logger.debug("lower: " + str(lower_index) + " upper: " + str(upper_index))

        # number of modules that separate the two nodes
        number_of_modules = self.get_module(upper_index) - self.get_module(lower_index)
        logger.debug("number of modules: " + str(number_of_modules))

        if number_of_modules == 0:
            return self.base_matrix[lower_index % self.base_size][upper_index % self.base_size]

        # else, the two nodes are in different modules -> should pass through the connection node

        # distance from the lower node to the connection node of the respective module
        d_lower_to_conn_node = self.base_matrix[lower_index % self.base_size][self.connection_node]
        logger.debug("lower to conn: " + str(d_lower_to_conn_node))

        # distance from connection node of one module to the connection node of the other
        d_conn_to_conn = self.distance_between_modules * number_of_modules
        logger.debug("conn to conn: " + str(d_conn_to_conn))

        # distance from the upper node to the connection node of the respective module
        d_upper_to_conn = self.base_matrix[self.connection_node][upper_index % self.base_size]
        logger.debug("upper to conn: " + str(d_upper_to_conn))

        return d_lower_to_conn_node + d_conn_to_conn + d_upper_to_conn

    def ndim(self):
        return 2

    def get_module(self, node_index):
        return node_index // self.base_size

    def get_distance_along_path(self, i, j, path):
        # flags
        i_found = False
        j_found = False

        # indexes of the two nodes in the path
        i_index = None
        j_index = None
        for index, node in enumerate(path):
            if (not i_found) and i == node:
                i_index = index
                i_found = True

            if i_found and j == node:
                j_index = index
                j_found = True

        if not (i_found and j_found):  # 'j' is unreachable from 'i', going along path
            raise LookupError(
                "The node " + str(j) + " is unreachable starting from " + str(i) + " and going along path " + str(path))

        # ok, proceed
        previous = i_index
        cost = 0
        for k in range(i_index + 1, j_index + 1):
            cost += self.__get_distance(path[previous], path[k])
            previous = k

        return cost

    def get_tour_length(self, tour):
        if len(tour) == 0:
            return 0

        last_node = tour[0]
        distance = 0
        for i in range(1, len(tour)):
            distance += self.__get_distance(last_node, tour[i])
            logger.debug("get distance between " + str(last_node) + " and " + str(tour[i]))
            logger.debug("Which is: " + str(self.__get_distance(last_node, tour[i])))
            last_node = tour[i]

        return distance

    def get_nodes_in_module(self, module):
        if not isinstance(module, int):
            raise IllegalParameterError("Expected an integer, got " + str(type(module)))
        elif module <= 0:
            raise IllegalParameterError("Module must be a positive integer")

        base_nodes = list(range(0, self.base_size))
        displacement = self.base_size * (module - 1)  # module - 1 because module indexes start from 1
        return [node + displacement for node in base_nodes]

    def get_module_entrance_node(self, module):
        if not isinstance(module, int):
            raise IllegalParameterError("Expected an integer, got " + str(type(module)))
        elif module <= 0:
            raise IllegalParameterError("Module must be a positive integer")

        displacement = self.base_size * (module - 1)  # module - 1 because module indexes start from 1

        return self.connection_node + displacement

    def __get_distance(self, i, j):
        return self[i, j]
