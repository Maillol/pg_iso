import unittest
from pg_iso.algo import compute_path


class TestComputePathToXY(unittest.TestCase):

    def test_dist_x_lt_dist_y(self):
        result = tuple(compute_path(1, 1, 2, 4))
        expected = ((1, 2), (2, 3), (2, 4))
        self.assertEqual(expected, result)

    def test_dist_x_gt_dist_y(self):
        result = tuple(compute_path(1, 1, 8, 2))
        expected = ((2, 1), (3, 1), (4, 1),
                    (5, 2), (6, 2), (7, 2), (8, 2))
        self.assertEqual(expected, result)

    def test_dist_x_eq_dist_y(self):
        result = tuple(compute_path(1, 1, 4, 4))
        expected = ((2, 2), (3, 3), (4, 4))
        self.assertEqual(expected, result)


class TestComputePathToMinusXY(unittest.TestCase):

    def test_dist_x_lt_dist_y(self):
        result = tuple(compute_path(2, 1, 1, 4))
        expected = ((2, 2), (1, 3), (1, 4))
        self.assertEqual(expected, result)

    def test_dist_x_gt_dist_y(self):
        result = tuple(compute_path(8, 1, 1, 2))
        expected = ((7, 1), (6, 1), (5, 1),
                    (4, 2), (3, 2), (2, 2), (1, 2))
        self.assertEqual(expected, result)

    def test_dist_x_eq_dist_y(self):
        result = tuple(compute_path(4, 1, 1, 4))
        expected = ((3, 2), (2, 3), (1, 4))
        self.assertEqual(expected, result)


class TestComputePathToXMinusY(unittest.TestCase):

    def test_dist_x_lt_dist_y(self):
        result = tuple(compute_path(1, 4, 2, 1))
        expected = ((1, 3), (2, 2), (2, 1))
        self.assertEqual(expected, result)

    def test_dist_x_gt_dist_y(self):
        result = tuple(compute_path(1, 2, 8, 1))
        expected = ((2, 2), (3, 2), (4, 2),
                    (5, 1), (6, 1), (7, 1), (8, 1))
        self.assertEqual(expected, result)

    def test_dist_x_eq_dist_y(self):
        result = tuple(compute_path(1, 4, 4, 1))
        expected = ((2, 3), (3, 2), (4, 1))
        self.assertEqual(expected, result)


class TestComputePathToMinusXMinusY(unittest.TestCase):

    def test_dist_x_lt_dist_y(self):
        result = tuple(compute_path(2, 4, 1, 1))
        expected = ((2, 3), (1, 2), (1, 1))
        self.assertEqual(expected, result)

    def test_dist_x_gt_dist_y(self):
        result = tuple(compute_path(8, 2, 1, 1))
        expected = ((7, 2), (6, 2), (5, 2),
                    (4, 1), (3, 1), (2, 1), (1, 1))
        self.assertEqual(expected, result)

    def test_dist_x_eq_dist_y(self):
        result = tuple(compute_path(4, 4, 1, 1))
        expected = ((3, 3), (2, 2), (1, 1))
        self.assertEqual(expected, result)


class TestComputePath(unittest.TestCase):

    def test_to_x(self):
        result = tuple(compute_path(2, 4, 6, 4))
        expected = ((3, 4), (4, 4), (5, 4), (6, 4))
        self.assertEqual(expected, result)

    def test_to_minus_x(self):
        result = tuple(compute_path(6, 4, 2, 4))
        expected = ((5, 4), (4, 4), (3, 4), (2, 4))
        self.assertEqual(expected, result)

    def test_to_y(self):
        result = tuple(compute_path(4, 2, 4, 6))
        expected = ((4, 3), (4, 4), (4, 5), (4, 6))
        self.assertEqual(expected, result)

    def test_to_minus_y(self):
        result = tuple(compute_path(4, 6, 4, 2))
        expected = ((4, 5), (4, 4), (4, 3), (4, 2))
        self.assertEqual(expected, result)

    def test_to_none(self):
        result = tuple(compute_path(4, 4, 4, 4))
        expected = ()
        self.assertEqual(expected, result)
