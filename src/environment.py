import numpy as np

from errors import IllegalParameterError


class Environment:
    def __init__(self, modules_matrices, modules_sequence, distances_between_modules, connection_nodes=None):
        """An Environment represent the structure of an actual environment in terms of a graph representation and it
        stores information on the modularity of the environment.

        Notice: it efficiently stores the distance matrix of the whole environment, provided that some modules are
        repeated

        :param modules_matrices: a list of 2d matrices of float, where the indexes are the nodes indexes and the
        value is the distance between the two nodes
        :param modules_sequence: a list that represent the sequence of modules in the environment. The modules are
        referred by the index they have in the modules_matrices parameter.
        :param distances_between_modules: an array of distances. It has length == number_of_modules - 1. Each value
        is the distance between the 'current' module and the next one
        :param connection_nodes: list of the entrance nodes. One node for each (type of) module. Default to [0,..,0]
        Notice: len(connection_nodes) == len(modules_matrices)
        """

        self.modules_matrices = modules_matrices
        # make sure that we use numpy to store the matrices
        self.__matrices_with_numpy()
        self.types = range(len(modules_matrices))
        self.modules_sequence = modules_sequence
        assert len(distances_between_modules) == len(modules_sequence) - 1, \
            "Distances between modules length is not coherent with the other parameters"
        self.distances_between_modules = distances_between_modules

        if connection_nodes is None:
            connection_nodes = [0] * len(modules_matrices)

        self.connection_nodes = connection_nodes

        self.__compute_length()

        # the mapping between local and global indexes will be used multiple times.
        #  It has to be as fast as possible: pre-compute it once and for all.
        self.__compute_mapping_global_local()
        self.__compute_mapping_local_global()

    def __compute_length(self):
        lengths = [len(type_matrix) for type_matrix in self.modules_matrices]
        length = 0
        for module_type in self.modules_sequence:
            length += lengths[module_type]
        self._length = length

    def __compute_mapping_global_local(self):
        # glob_to_loc[global_index] returns the local index
        self.__glob_to_loc = np.empty(self._length, dtype=int)
        # glob_to_loc[global_index] returns the module index containing the node with the specified global index
        self.__glob_to_module = np.empty(self._length, dtype=int)
        top = -1  # last index filled in glob_to_loc

        for i in range(len(self.modules_sequence)):
            m_type = self.modules_sequence[i]
            module_length = len(self.modules_matrices[m_type])
            index_mapping = np.arange(module_length)
            self.__glob_to_loc[top + 1:top + module_length + 1] = index_mapping

            # This works because of numpy broadcasting
            # Notice: +1 because modules are indexed starting from 1
            self.__glob_to_module[top + 1:top + module_length + 1] = i + 1

            # DO NOT PUT +1. Using "top + module_length + 1" in the slicing, that index is excluded. So the last one
            # occupied is the previous one, the one without the +1
            top = top + module_length

        assert top == self._length - 1, "The mapping global to local has not been done properly"

    def __compute_mapping_local_global(self):
        """compute the mapping from local values (module index and node_local_index) to the global node index"""

        # we only need one displacement value for each module (that is the number of nodes that precede it
        self.__displacement = np.empty(len(self.modules_sequence), dtype=int)
        top = -1  # last index filled in displacement

        self.__displacement[0] = 0
        top = 0

        for m_type in self.modules_sequence[:-1]:
            module_length = len(self.modules_matrices[m_type])
            self.__displacement[top + 1] = self.__displacement[top] + module_length
            top += 1

    def __getitem__(self, item):
        if isinstance(item, slice):  # example variable[0:5] -> returns a list of lists of int
            raise IndexError("Slicing not implemented")
        elif isinstance(item, int):  # example variable[0] -> returns a list of int
            raise IndexError("Access by rows not implemented")
        elif isinstance(item, tuple):
            if len(item) != self.ndim():
                raise IndexError("Tuple length not consistent with environment dimensionality. Expected: ",
                                 self.ndim(), ", got: ", len(item))

            # TODO: change. This only works when ndim returns 2
            if not (isinstance(item[0], (int, np.integer)) and isinstance(item[1], (int, np.integer))):
                raise IndexError("Environment can only be indexed via tuple of integers")

            return self.__get_single_item(item)

        else:  # waat?
            raise IndexError("Cannot index using type ", type(item))

    def __len__(self):
        if not hasattr(self, "_length"):
            raise RuntimeError("Object environment not completely initialized. There is no attribute length")

        return self._length

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

        upper_module, local_upper_index = self.get_module_and_index(upper_index)
        lower_module, local_lower_index = self.get_module_and_index(lower_index)

        if upper_module.index == lower_module.index:
            return upper_module.distance_matrix[local_lower_index][local_upper_index]

        # else, the two nodes are in different modules -> should pass through the connection node

        # distance from the lower node to the connection node of the respective module
        d_lower_to_conn_node = lower_module.distance_matrix[local_lower_index][lower_module.connection_node]

        # distance from connection node of one module to the connection node of the other
        # notice: the '-1' is needed because modules are indexed starting from 1
        d_conn_to_conn = sum(self.distances_between_modules[lower_module.index - 1:upper_module.index - 1])

        # distance from the upper node to the connection node of the respective module
        d_upper_to_conn = upper_module.distance_matrix[upper_module.connection_node][local_upper_index]

        return d_lower_to_conn_node + d_conn_to_conn + d_upper_to_conn

    def ndim(self):
        return 2

    def get_module_and_index(self, node_index: int) -> tuple:
        """Return both the module (class Module), to which the node belongs, and the local index correspondent to the
                global node index"""
        assert 0 <= node_index < len(self), "Node index out of bound. Node index: " + str(node_index)
        module_index = self.__glob_to_module[node_index]
        module_type = self.modules_sequence[module_index - 1]
        module_matrix = self.modules_matrices[module_type]
        connection_node = self.connection_nodes[module_type]

        module = self.Module(module_matrix, module_type, connection_node, index=module_index)
        return module, self.__glob_to_loc[node_index]

    def get_global_index(self, module_index, local_index):
        """Return the global index of the node given the module index and the local (to the module) index of the node"""
        assert module_index > 0, "Module index should be a positive integer (not 0)"
        assert module_index <= len(self.modules_sequence), "Module index out of bound"

        module_type = self.modules_sequence[module_index - 1]
        assert 0 <= local_index < len(self.modules_matrices[module_type]), \
            "There is no node {} in module {}".format(local_index, module_index)

        # -1 because modules are indexed starting from 1
        return self.__displacement[module_index - 1] + local_index

    def get_distance_along_path(self, i, j, path):
        """Calculate the distance from node i to node j, traveling along the 'path'"""

        # first search for the nodes 'i' and 'j' in the 'path' (probably they are inside and not the start and the end)
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

            # 'i' has to appear BEFORE 'j' in the path. If we have found 'i', we can start to look for 'j'
            if i_found and j == node:
                j_index = index
                j_found = True

        if not (i_found and j_found):  # 'j' is unreachable from 'i', going along path
            raise LookupError(
                "The node " + str(j) + " is unreachable starting from " + str(i) + " and going along path " + str(path))

        # ok, proceed
        # trim the path and just calculate the length of the trimmed path
        return self.get_tour_length(path[i_index:j_index + 1])

    def get_tour_length(self, tour):
        if len(tour) == 0:
            return 0

        last_node = tour[0]
        distance = 0
        for i in range(1, len(tour)):
            distance += self.__get_distance(last_node, tour[i])
            last_node = tour[i]

        return distance

    def get_nodes_in_module(self, module):
        if not isinstance(module, int):
            raise IllegalParameterError("Expected an integer, got " + str(type(module)))
        elif module <= 0:
            raise IllegalParameterError("Module must be a positive integer (not 0)")

        # module - 1 because module indexes start from 1
        m_type = self.modules_sequence[module - 1]
        module_matrix = self.modules_matrices[m_type]
        base_nodes = list(range(len(module_matrix)))
        displacement = self.__displacement[module - 1]
        return [node + displacement for node in base_nodes]

    def get_module_entrance_node(self, module):
        if not isinstance(module, int):
            raise IllegalParameterError("Expected an integer, got " + str(type(module)))
        elif module <= 0:
            raise IllegalParameterError("Module must be a positive integer")

        # module - 1 because module indexes start from 1
        module_type = self.modules_sequence[module - 1]
        local_connection_node = self.connection_nodes[module_type]

        return self.get_global_index(module, local_connection_node)

    def __get_distance(self, i, j):
        return self[i, j]

    def generate_matrix(self, for_real=False):
        if not for_real:
            raise NotImplemented("The matrix generated could be very large. Call the function with parameter "
                                 "'for_real'==True")

        distances = np.empty((len(self), len(self)), dtype=int)
        for i in range(len(self)):
            for j in range(len(self)):
                distances[i, j] = self[i, j]

        return distances

    def get_base_matrices(self, module):
        m_type = self.modules_sequence[module - 1]
        return self.modules_matrices[m_type].copy()

    @property
    def base_modules(self):
        modules = []
        for i in range(len(self.modules_matrices)):
            module_matrix = self.modules_matrices[i]
            module_type = i
            connection_node = self.connection_nodes[i]

            module = self.Module(module_matrix, module_type, connection_node)

            modules.append(module)

        return modules

    @property
    def modules(self):
        modules = []
        base_modules = self.base_modules

        for module_type in self.modules_sequence:
            module = base_modules[module_type]
            modules.append(module)

        return modules

    @property
    def origin_node(self):
        """Return the node that represents the entrance of the environment"""
        # the entrance of the environment is the entrance node of the first module
        return self.connection_nodes[0]

    @property
    def number_of_modules(self):
        return len(self.modules_sequence)

    @property
    def connections(self):
        return self.distances_between_modules

    def __matrices_with_numpy(self):
        for i in range(len(self.modules_matrices)):
            matrix = self.modules_matrices[i]
            if not isinstance(matrix, np.ndarray):
                self.modules_matrices[i] = np.array(matrix)

    class Module:
        def __init__(self, distance_matrix, type, connection_node, index=None):
            self.distance_matrix = distance_matrix
            self.type = type
            self.connection_node = connection_node
            self.index = index
