from __future__ import annotations
from typing import (
    Tuple,
    Optional,
    Callable,
    List,
    Union,
    Dict,
    Protocol,
    TYPE_CHECKING
)

from numpy import ndarray

if TYPE_CHECKING:
    from stock_pandas.dataframe import StockDataFrame # pragma: no cover


ReturnType = Tuple[ndarray, int]
CommandArgType = Union[str, int, float]


def DEFAULT_ARG_COERCE(x: CommandArgType) -> CommandArgType:
    return x


class CommandArg:
    """
    The definition of a command argument

    Args:
        default (Optional[CommandArgType] = None): The default value for the argument. `None` indicates that it is NOT an optional argument
        coerce (Optional[Callable[..., CommandArgType]]): The function to coerce the argument to the correct type and value range. The function is throwable.
    """

    __slots__ = (
        'default',
        'coerce'
    )

    default: Optional[CommandArgType]
    coerce: Callable[..., CommandArgType]

    def __init__(
        self,
        default: Optional[CommandArgType] = None,
        coerce: Optional[Callable[..., CommandArgType]] = DEFAULT_ARG_COERCE
    ) -> None:
        self.default = default
        self.coerce = coerce


class CommandFormula(Protocol):
    def __call__(
        self,
        df: 'StockDataFrame',
        s: slice,
        *args: CommandArgType
    ) -> ReturnType:
        ... # pragma: no cover


class CommandPreset:
    """
    A command preset defines the formula and arguments for a command

    Args:
        formula (CommandFormula): The formula of the command
        args (List[CommandArg]): The arguments of the command
    """

    __slots__ = (
        'formula',
        'args'
    )

    formula: CommandFormula
    args: List[CommandArg]

    def __init__(
        self,
        formula: CommandFormula,
        args: List[CommandArg]
    ) -> None:
        self.formula = formula
        self.args = args


SubCommandsMap = Dict[
    str,
    CommandPreset
]

AliasesMap = Dict[
    str,
    Optional[str]
]


class CommandDefinition:
    """
    A CommandDefinition is a collection of a command preset, sub commands and aliases

    Args:
        preset (Optional[CommandPreset]): The command preset. `None` indicates that there are only sub commands, such as "kdj.k".
        sub_commands (Optional[Dict[str, CommandPreset]]): The sub commands. `None` indicates that there are no sub commands
        aliases (Optional[Dict[str, Optional[str]]]): The alias command names. `None` indicates that there are no aliases.
    """

    __slots__ = (
        'preset',
        'sub_commands',
        'aliases'
    )

    preset: Optional[CommandPreset]
    sub_commands: Optional[SubCommandsMap]
    aliases: Optional[AliasesMap]

    def __init__(
        self,
        preset: Optional[CommandPreset] = None,
        sub_commands: Optional[SubCommandsMap] = None,
        aliases: Optional[AliasesMap] = None
    ) -> None:
        # self.name = name
        self.preset = preset
        self.sub_commands = sub_commands
        self.aliases = aliases


COMMANDS: Dict[str, CommandDefinition] = {}
