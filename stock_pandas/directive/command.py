from __future__ import annotations
from typing import (
    Tuple,
    Optional,
    Callable,
    List,
    Dict
)
from dataclasses import dataclass

from stock_pandas.exceptions import DirectiveValueError

from .cache import DirectiveCache
from .tokenizer import Loc
from .types import (
    CommandArgType,
    CommandFormula
)


def DEFAULT_ARG_COERCE(x: CommandArgType) -> CommandArgType:
    return x


@dataclass
class Context:
    input: str
    loc: Loc
    cache: DirectiveCache
    commands: Commands


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


SubCommands = Dict[
    str,
    CommandPreset
]

CommandAliases = Dict[
    str,
    Optional[str]
]


@dataclass
class ScalarNode:
    value: str
    loc: Loc

    def create(self, _: Context) -> str:
        return self.value


@dataclass
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

    preset: Optional[CommandPreset] = None
    sub_commands: Optional[SubCommands] = None
    aliases: Optional[CommandAliases] = None

    def get_preset(
        self,
        main: ScalarNode,
        sub: Optional[ScalarNode],
        context: Context
    ) -> Tuple[CommandPreset, Optional[str]]:
        main_name = main.value
        sub_name = self._sub_name(sub)

        if sub_name is not None:
            if self.sub_commands is None:
                raise DirectiveValueError(
                    context.input,
                    f'command "{main_name}" has no sub commands',
                    main.loc
                )

            preset = self.sub_commands.get(sub_name)

            if preset is None:
                raise DirectiveValueError(
                    context.input,
                    f'unknown sub command "{sub_name}" for command "{main_name}"',
                    sub.loc
                )

            return preset, sub_name

        if self.preset is None:
            raise DirectiveValueError(
                context.input,
                f'sub command should be specified for command "{main_name}"',
                main.loc
            )

        return self.preset, None

    def _sub_name(self, sub: Optional[ScalarNode]) -> Optional[str]:
        if sub is None:
            return None

        name = sub.value

        if self.aliases is not None:
            return self.aliases.get(name, name)

        return name


Commands = Dict[str, CommandDefinition]
