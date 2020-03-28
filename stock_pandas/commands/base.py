from typing import (
    Tuple,
    Optional,
    Callable,
    List,
    Dict,
    Any
)

from numpy import ndarray

from stock_pandas.common import (
    period_to_int
)


ReturnType = Tuple[ndarray, int]


class CommandPreset:
    __slots__ = (
        'formula',
        'args'
    )

    def __init__(
        self,
        formula: Callable[..., ReturnType],
        args: List[
            Tuple[
                Optional[Any],
                Optional[Callable]
            ]
        ]
    ) -> None:
        self.formula = formula
        self.args = args


SubCommandsMap = Optional[
    Dict[
        str,
        CommandPreset
    ]
]
AliasesMap = Optional[
    Dict[
        str,
        Optional[str]
    ]
]


COMMANDS: Dict[
    str,
    Tuple[
        Optional[CommandPreset],
        SubCommandsMap,
        AliasesMap
    ]
] = {}


arg_period = (
    # Default value for the first argument,
    # `None` indicates that it is not an optional argument
    None,
    # Validator and setter for the first argument.
    # The function could throw
    period_to_int
)
