from math import floor


def compute_path(x1, y1, x2, y2):
    dist_x = abs(x2 - x1)
    dist_y = abs(y2 - y1)
    if dist_x == dist_y == 0:
        return

    if dist_x > dist_y:
        if y1 <= y2:
            step_y = dist_y / dist_x
        else:
            step_y = -dist_y / dist_x

        if x1 <= x2:
            x_values = range(x1 + 1, x2 + 1)
        else:
            x_values = range(x1 - 1, x2 - 1, -1)

        for x in x_values:
            y1 += step_y
            yield x, floor(y1 + 0.5)
    else:
        if x1 < x2:
            step_x = dist_x / dist_y
        else:
            step_x = -dist_x / dist_y

        if y1 <= y2:
            y_values = range(y1 + 1, y2 + 1)
        else:
            y_values = range(y1 - 1, y2 - 1, -1)

        for y in y_values:
            x1 += step_x
            yield floor(x1 + 0.5), y
