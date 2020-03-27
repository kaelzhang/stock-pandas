from typing import (
    Tuple,
    Optional,
    Callable,
    List,
    Dict
)

from numpy import ndarray

from stock_pandas.common import (
    period_to_int
)


ReturnType = Tuple[ndarray, int]


class CommandPreset:
    __slots__ = (
        'formula',
        'args',
        'subs_map',
        'sub_aliases_map'
    )

    def __init__(
        self,
        formula: Optional[Callable[..., ReturnType]] = None,
        args: Optional[List[Tuple]] = None,
        subs_map: Optional[Dict[str, 'CommandPreset']] = None,
        sub_aliases_map: Optional[
            Dict[
                str,
                Optional[str]
            ]
        ] = None
    ) -> None:
        self.formula = formula
        self.args = args
        self.subs_map = subs_map
        self.sub_aliases_map = sub_aliases_map


COMMANDS = {}


arg_period = (
    # Default value for the first argument,
    # `None` indicates that it is not an optional argument
    None,
    # Validator and setter for the first argument.
    # The function could throw
    period_to_int
)
