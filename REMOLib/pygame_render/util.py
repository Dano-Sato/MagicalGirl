from math import radians, cos, sin
import math
import numpy as np


# Convert from 0-255 to 0-1, and also process the different ways
# in which arguments may be given (an int tuple vs four separate ints)
def normalize_color_arguments(R: (int | tuple[int]), G: int, B: int, A: int):
    if isinstance(R, tuple):
        if len(R) == 3:
            R, G, B = R
        elif len(R) == 4:
            R, G, B, A = R
        else:
            raise ValueError(
                'Error: The tuple must contain either RGB or RGBA values.')

    return (R/255., G/255., B/255., A/255.)


# Convert from 0-1 to 0-255
def denormalize_color(col):
    return (int(x * 255) for x in col)



def create_rotated_rect(position, width, height, scale, angle, flip):
    # Scale and rotation parameters
    w, h = scale[0] * width, scale[1] * height
    angle_rad = radians(angle)
    cos_a, sin_a = cos(angle_rad), sin(angle_rad)

    # Half dimensions to minimize redundant divisions
    half_w, half_h = w / 2, h / 2

    # Calculate corner points using a numpy array for batch processing
    corners = np.array([
        [half_w, half_h],
        [-half_w, half_h],
        [-half_w, -half_h],
        [half_w, -half_h]
    ])

    # Apply rotation matrix to all corners
    rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    rotated_corners = corners @ rotation_matrix.T

    # Flip if necessary
    if flip[0]:  # Horizontal flip
        rotated_corners[:, 0] *= -1
    if flip[1]:  # Vertical flip
        rotated_corners[:, 1] *= -1

    # Translate based on position
    x, y = position
    rotated_corners[:, 0] += x + half_w
    rotated_corners[:, 1] += y + half_h

    return [(float(px), float(py)) for px, py in rotated_corners]



def to_dest_coords(p: tuple[float, float], dest_width: float, dest_height: float):
    return (2. * p[0] / dest_width - 1., 1. - 2. * p[1] / dest_height)


def to_source_coords(p: tuple[float, float], source_width: float, source_height: float):
    return (p[0] / source_width, p[1] / source_height)



def get_bounding_rectangle(vertices: list[tuple[float, float]]) -> tuple[int, int, int, int]:
    """
    Calculate the axis-aligned bounding rectangle for a set of vertices as an integer rectangle.

    Parameters:
    - vertices (list[tuple[float, float]]): A list of 4 points (x, y) representing the vertices.

    Returns:
    - tuple[int, int, int, int]: The bounding rectangle in the format (min_x, min_y, width, height) with integer values.
    """

    # Extract min and max directly from vertices without separate lists
    min_x = math.floor(min(v[0] for v in vertices))
    max_x = math.ceil(max(v[0] for v in vertices))
    min_y = math.floor(min(v[1] for v in vertices))
    max_y = math.ceil(max(v[1] for v in vertices))

    # Calculate width and height
    width = max_x - min_x
    height = max_y - min_y

    return min_x, min_y, width, height
