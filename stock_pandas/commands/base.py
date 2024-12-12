from typing import (
    Tuple,
    Optional,
    Callable,
    List,
    Union,
    Dict
)

from numpy import ndarray

from stock_pandas.common import (
    period_to_int
)


ReturnType = Tuple[ndarray, int]
CommandFormula = Callable[..., ReturnType]
CommandArg = Union[str, int, float]
CommandArgs = List[
    Union[
        Tuple[
            Optional[CommandArg],
            Optional[Callable[..., CommandArg]]
        ],
        CommandArg
    ]
]


class CommandPreset:
    __slots__ = (
        'formula',
        'args'
    )

    formula: CommandFormula
    args: CommandArgs

    def __init__(
        self,
        formula: CommandFormula,
        args: CommandArgs
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
