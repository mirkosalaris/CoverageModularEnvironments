__all__ = ["matrix_to_file", "parse_file"]

import re

import numpy as np


def matrix_to_file(distance_matrix, file):
    """
    :param distance_matrix: a matrix with nodes as indexes and distances as values
    :param file: either a filename or an open file
    """
    opened = False  # keep track of whether we opened the file (the function input was a filename) or not

    try:
        if type(file) == str:
            file = open(file, 'w')
            opened = True

        file.seek(0)

        n = len(distance_matrix)
        file.write("VERTICES = {}\n;\n\n".format(n))

        file.write("DISTANCE_MATRIX = \n")
        for i in range(0, n):
            for j in range(0, n):
                file.write("{}\t{}\t{}\n".format(i, j, distance_matrix[i][j]))

        file.write(";")

    except OSError as err:
        print("Error in writing file: {0}".format(err))
    finally:
        if opened:
            file.close()


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


def parse_file(filename):
    num_vertices = None
    matrix = None
    with open(filename, 'r') as fp:
        first_line = fp.readline()
        num_vertices = re.findall(r'\d+', first_line)
        assert len(num_vertices) == 1, 'Error in parsing file {}. First line should be VERTICES = ##\n'.format(filename)
        num_vertices = int(num_vertices[0])

        line = fp.readline()
        while ("DISTANCE_MATRIX" not in line):
            line = fp.readline()

        """ from next line all lines are
            # # #
            -> three numbers, which are 'i, j, distance between i and j'
        """
        matrix = np.zeros((num_vertices, num_vertices))
        line = fp.readline()
        while has_numbers(line):
            # read_i, read_j, read_distance
            ri, rj, rd = re.findall(r'^(\d+)\s*(\d+)\s*(\d+(?:\.\d+)?)', line)[0]

            matrix[int(ri), int(rj)] = float(rd)
            line = fp.readline()

    return num_vertices, matrix
