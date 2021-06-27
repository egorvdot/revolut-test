import sys
import unittest

from nest import (
    FlatDictsTransformation,
    IterativeFlatDictsTransformation,
    RecursiveFlatDictsTransformation,
    RecursiveFlatDictsTransformationError,
)


class TestFlatDictsTransformation(unittest.TestCase):

    def test_create_empty_nesting_level(self):
        with self.assertRaises(RecursiveFlatDictsTransformationError):
            FlatDictsTransformation.create(
                nesting_levels=[],
                flat_dicts=[],
            )

    def test_create_correct_values(self):
        with self.assertRaises(TypeError):
            FlatDictsTransformation.create(
                nesting_levels=['a'],
                flat_dicts=[
                    {'a': 1, 'b': 2},
                ],
            )


class CommonTestFlatDictsTransformation:

    transformation_class = None

    def test_transformation_unexpected_nesting_level(self):
        transformation = self.transformation_class(
            nesting_levels=['a', 'B'],
            flat_dicts=[
                {'a': 1, 'b': 2},
            ],
        )
        with self.assertRaises(RecursiveFlatDictsTransformationError):
            transformation()

    def test_transformation_one_nesting_level(self):
        transformation = self.transformation_class(
            nesting_levels=['a'],
            flat_dicts=[
                {'a': 1, 'b': 2},
            ],
        )
        transformed = transformation()
        expected = {1: [{'b': 2}]}
        self.assertEqual(transformed, expected)

    def test_transformation_two_nesting_levels(self):
        transformation = self.transformation_class(
            nesting_levels=['a', 'b'],
            flat_dicts=[
                {'a': 1, 'b': 2},
            ],
        )
        transformed = transformation()
        expected = {1: {2: [{}]}}
        self.assertEqual(transformed, expected)

    def test_transformation_three_nesting_levels(self):
        transformation = self.transformation_class(
            nesting_levels=['a', 'b', 'c'],
            flat_dicts=[
                {'a': 1, 'b': 2, 'c': 3},
            ],
        )
        transformed = transformation()
        expected = {1: {2: {3: [{}]}}}
        self.assertEqual(transformed, expected)

    def test_transformation_four_nesting_levels(self):
        transformation = self.transformation_class(
            nesting_levels=['a', 'b', 'c', 'd'],
            flat_dicts=[
                {'a': 1, 'b': 2, 'c': 3, 'd': 4},
            ],
        )
        transformed = transformation()
        expected = {1: {2: {3: {4: [{}]}}}}
        self.assertEqual(transformed, expected)

    def test_transformation_task_example(self):
        transformation = self.transformation_class(
            nesting_levels=['currency', 'country', 'city'],
            flat_dicts=[
                {'country': 'US', 'city': 'Boston', 'currency': 'USD', 'amount': 100},
                {'country': 'FR', 'city': 'Paris', 'currency': 'EUR', 'amount': 20},
                {'country': 'FR', 'city': 'Lyon', 'currency': 'EUR', 'amount': 11.4},
                {'country': 'ES', 'city': 'Madrid', 'currency': 'EUR', 'amount': 8.9},
                {'country': 'UK', 'city': 'London', 'currency': 'GBP', 'amount': 12.2},
                {'country': 'UK', 'city': 'London', 'currency': 'FBP', 'amount': 10.9},
            ],
        )
        transformed = transformation()
        expected = {
            'USD': {'US': {'Boston': [{'amount': 100}]}},
            'EUR': {'FR': {'Paris': [{'amount': 20}], 'Lyon': [{'amount': 11.4}]}, 'ES': {'Madrid': [{'amount': 8.9}]}},
            'GBP': {'UK': {'London': [{'amount': 12.2}]}}, 'FBP': {'UK': {'London': [{'amount': 10.9}]}},
        }
        self.assertEqual(transformed, expected)


class TestRecursiveFlatDictsTransformation(unittest.TestCase, CommonTestFlatDictsTransformation):
    transformation_class = RecursiveFlatDictsTransformation

    def test_transformation_recursion_limitation(self):
        recursion_limit = 500
        flat_dict_for_error = {f'field{index}': index for index in range(recursion_limit)}
        flat_dict = flat_dict_for_error.copy()

        nesting_levels_for_error = list(flat_dict.keys())
        transformation_raised_error = self.transformation_class(
            nesting_levels=nesting_levels_for_error,
            flat_dicts=[flat_dict_for_error],
        )

        sys.setrecursionlimit(recursion_limit)

        with self.assertRaises(RecursionError):
            transformation_raised_error()


class TestIterativeFlatDictsTransformation(unittest.TestCase, CommonTestFlatDictsTransformation):
    transformation_class = IterativeFlatDictsTransformation


if __name__ == '__main__':
    unittest.main()
