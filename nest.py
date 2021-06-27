import argparse
import json
import sys
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Union, Any

DESCRIPTION = """
Parse input json array and return a nested dictionary of dictionaries of arrays,
with keys specified in command line arguments.
"""

USAGE = """
python3 nest.py  [-h] [--pretty] [--recursive] nesting_level_1 [... nesting_level_n]

1. input from console
    #> python nest.py currency
    >>> [{"currency": "GBR", "amount": 100}, {"currency": "EUR", "amount": 90}]
    {"GBR": {"amount": 100"}, "EUR": {"amount": 90"}}

2. input from pipeline
    #> cat input.json | python nest.py currency country
    {"GBR": {"UK": {"amount": 100"}}, "EUR": {"ES": {"amount": 90"}}}
"""

FlatDicts = List[Dict[str, Any]]
Nested = Union[FlatDicts, Dict[str, 'Nested']]


class RecursiveFlatDictsTransformationError(Exception):
    """Error in the transformation."""


class FlatDictsTransformation(metaclass=ABCMeta):
    """Base for any realizations of transforming."""

    def __init__(self, nesting_levels: List[str], flat_dicts: FlatDicts):
        self._nesting_levels = nesting_levels
        self._flat_dicts = flat_dicts

    @abstractmethod
    def __call__(self):
        """Do transforming."""

    @classmethod
    def create(cls, nesting_levels: List[str], flat_dicts: FlatDicts):
        """Transformation factory."""
        if len(nesting_levels) == 0:
            raise RecursiveFlatDictsTransformationError('[]', 'empty nesting levels')
        return cls(nesting_levels, flat_dicts)


class RecursiveFlatDictsTransformation(FlatDictsTransformation):
    """Transformer from list of flat dicts to dict of dicts by nesting levels.

    Uses recursive way for calculations.
    """

    def __call__(self) -> Nested:
        """Do transforming."""
        try:
            return self._transform_to_nested(self._nesting_levels, self._flat_dicts)
        except KeyError as err:
            raise RecursiveFlatDictsTransformationError(err.args[0], 'no such nesting level')

    @staticmethod
    def _transform_to_nested(nesting_levels: List[str], nested_entity: Nested) -> Nested:
        nested = RecursiveFlatDictsTransformation._transform_to_dict(nesting_levels[0], nested_entity)
        if len(nesting_levels) != 1:
            for keys, values in nested.items():
                nested[keys] = RecursiveFlatDictsTransformation._transform_to_nested(nesting_levels[1:], values)
        return nested

    @staticmethod
    def _transform_to_dict(nesting_level: str, flat_dicts: FlatDicts):
        nested = {}
        for flat_dict in flat_dicts:
            key = flat_dict[nesting_level]
            del flat_dict[nesting_level]
            if key in nested:
                nested[key].append(flat_dict)
            else:
                nested[key] = [flat_dict]
        return nested


class IterativeFlatDictsTransformation(FlatDictsTransformation):
    """Transformer from list of flat dicts to dict of dicts by nesting levels.

    Uses iterative way for calculations.
    """

    def __call__(self) -> Nested:
        """Do transforming."""
        try:
            return self._transform_to_nested(self._nesting_levels, self._flat_dicts)
        except KeyError as err:
            raise RecursiveFlatDictsTransformationError(err.args[0], 'no such nesting level')

    @staticmethod
    def _transform_to_nested(nesting_levels: List[str], flat_dicts: FlatDicts) -> Nested:
        nested = {}
        for flat_dict in flat_dicts:
            current_dict = nested
            for nesting_level in nesting_levels:
                level_value = flat_dict[nesting_level]
                if level_value in current_dict:
                    current_dict = current_dict[level_value]
                else:
                    if nesting_level == nesting_levels[-1]:
                        current_dict[level_value] = []
                    else:
                        current_dict[level_value] = {}
                    current_dict = current_dict[level_value]
                del flat_dict[nesting_level]
            current_dict.append(flat_dict)
        return nested


transformations_map = {
    True: RecursiveFlatDictsTransformation,
    False: IterativeFlatDictsTransformation,
}


def _main(parsed_args: argparse.Namespace):
    if sys.stdin.isatty():
        raw_flat = input()
    else:
        raw_flat = sys.stdin.read()
    try:
        flat_dicts = json.loads(raw_flat)
    except json.decoder.JSONDecodeError as err:
        print(f'nest: {err.args[0]}: incorrect format of flat dictionaries', file=sys.stderr)
        exit(1)

    transformation_factory = transformations_map[parsed_args.recursive]

    try:
        transformation = transformation_factory.create(parsed_args.nesting_levels, flat_dicts)
        transformed = transformation()
    except RecursiveFlatDictsTransformationError as err:
        print(f'nest: {err.args[0]}: {err.args[1]}', file=sys.stderr)
        exit(1)

    if parsed_args.pretty:
        indent = 2
        sort_keys = True
    else:
        indent = None
        sort_keys = False
    print(json.dumps(transformed, indent=indent, sort_keys=sort_keys))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=USAGE, description=DESCRIPTION)
    parser.add_argument(
        'nesting_levels',
        nargs=argparse.REMAINDER,
        help='dictionary keys indicating the level of nesting',
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='pretty print of nested entity',
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='use recursive realization of transformation',
    )
    parsed_args = parser.parse_args()

    _main(parsed_args)
