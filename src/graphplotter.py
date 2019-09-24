__all__ = ["plot_graph"]

from PIL import Image, ImageDraw

BOX_COLOR = "blue"
CENTROIDS_COLOR = "red"
PORTALS_COLOR = "green"

CENTROIDS_SIZE = 4
PORTALS_SIZE = 4

EDGES_WIDTH = 2

BASE_SCALE_FACTOR = 1


def scale(arr, scale_factor=BASE_SCALE_FACTOR):
    if type(arr[0]) is tuple:
        return list(map(lambda t: tuple(k * scale_factor for k in t), arr))

    elif type(arr[0]) in [float, int]:
        return list(map(lambda k: k * scale_factor, arr))

    else:
        raise Exception("The input parameters must be an array of numbers (int or float) or an array of tuples")


def dots(draw, points, scale_factor=BASE_SCALE_FACTOR, size=4, color="red"):
    points = scale(points, scale_factor)
    for p in points:
        x0 = p[0] - size // 2
        y0 = p[1] - size // 2
        x1 = p[0] + size // 2 + 1
        y1 = p[1] + size // 2 + 1
        draw.rectangle([x0, y0, x1, y1], fill=color)


def rectangles(draw, points, scale_factor=BASE_SCALE_FACTOR, color="blue"):
    points = scale(points, scale_factor)
    for rect in points:
        draw.rectangle(rect, outline=color)


def lines(draw, lines_coords, scale_factor=BASE_SCALE_FACTOR, width=EDGES_WIDTH, color="yellow"):
    lines_coords = scale(lines_coords, scale_factor)
    for pp in lines_coords:
        draw.line(pp, fill=color, width=width)


def draw_boxes(draw, points, color=BOX_COLOR):
    rectangles(draw, points, color)


def draw_centroids(draw, points, size=CENTROIDS_SIZE, color=CENTROIDS_COLOR):
    dots(draw, points, size, color)


def draw_portals(draw, points, size=PORTALS_SIZE, color=PORTALS_COLOR):
    dots(draw, points, size, color)


def draw_nodes(drawing, graph, scale_factor=BASE_SCALE_FACTOR):
    nodes = list(map(lambda v: (v.x, v.y), list(graph.nodes.values())))
    dots(drawing, nodes, scale_factor)


def draw_edges(drawing, graph, scale_factor=BASE_SCALE_FACTOR):
    edges = list(map(lambda e: (e.n1.x, e.n1.y, e.n2.x, e.n2.y), list(graph.edges.values())))
    lines(drawing, edges, scale_factor)


def draw_graph(drawing, graph, scale_factor=BASE_SCALE_FACTOR):
    draw_nodes(drawing, graph, scale_factor)
    draw_edges(drawing, graph, scale_factor)


def plot_graph(graph, filename, scale_factor=BASE_SCALE_FACTOR):
    """graph: a Graph object
    filename: the filename of the image on which to plot the graph"""
    im = Image.open(filename)
    drawing = ImageDraw.Draw(im)

    draw_graph(drawing, graph, scale_factor)

    return im
