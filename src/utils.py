import pickle

from fileio import parse_file

SOURCES_FOLDER = "../resources/environments/extracted/"
SAVE_FOLDER = "../Notebooks/saved_results/comparison_v1/"


def get_building_matrix(building, source_folder=SOURCES_FOLDER):
    filename = source_folder + building + ".txt"
    _, matrix = parse_file(filename)
    return matrix


def save_variables(variables, filename, folder=SAVE_FOLDER):
    with open(folder + filename, 'wb') as f:
        pickle.dump(variables, f)


def load_variables(filename, folder=SAVE_FOLDER):
    with open(folder + filename, 'rb') as f:
        return pickle.load(f)
