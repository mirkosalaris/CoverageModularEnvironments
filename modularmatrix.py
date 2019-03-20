import common

class ModularMatrix:
    """A Modular Matrix is like a usual distance matrix but it consists of repeated modules, meaning that it can be
    efficiently represented by a base matrix, that represent a module, repeated many times, connected by an edge"""

    def __init__(self, module_matrix, distance_between_modules, number_of_modules, connection_node=0):
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

            return self.__get_single_item__(item)

        else:  # integer index
            # TODO: this should return a vector
            raise NotImplementedError("Currently only support single element indexing, using tuple")

    def __len__(self):
        return len(self.base_matrix) * self.number_of_modules

    def __get_single_item__(self, item):

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

        common.debug("lower: ", lower_index, " upper: ", upper_index)

        # number of modules that separate the two nodes
        number_of_modules = (upper_index // self.base_size) - (lower_index // self.base_size)
        common.debug("number of modules: ", number_of_modules)

        if number_of_modules == 0:
            return self.base_matrix[lower_index % self.base_size][upper_index % self.base_size]

        # else, the two nodes are in different modules -> should pass through the connection node

        # distance from the lower node to the connection node of the respective module
        d_lower_to_conn_node = self.base_matrix[lower_index % self.base_size][self.connection_node]
        common.debug("lower to conn: ", d_lower_to_conn_node)

        # distance from connection node of one module to the connection node of the other
        d_conn_to_conn = self.distance_between_modules * number_of_modules
        common.debug("conn to conn: ", d_conn_to_conn)

        # distance from the upper node to the connection node of the respective module
        d_upper_to_conn = self.base_matrix[self.connection_node][upper_index % self.base_size]
        common.debug("upper to conn: ", d_upper_to_conn)

        return d_lower_to_conn_node + d_conn_to_conn + d_upper_to_conn

    def ndim(self):
        return 2
