from __future__ import annotations
from typing import (
    Tuple,
    Optional,
    Callable,
    List,
    Dict,
    TypeVar,
    Generic
)
from dataclasses import dataclass, field

from stock_pandas.exceptions import DirectiveValueError

from .cache import DirectiveCache
from .tokenizer import Loc
from .types import (
    PrimativeType,
    CommandArgInputType,
    CommandFormula,
    CommandLookback
)


def DEFAULT_ARG_COERCE(x: PrimativeType) -> PrimativeType:
    return x


@dataclass(frozen=True, slots=True)
class Context:
    input: str
    loc: Loc
    cache: DirectiveCache
    commands: Commands


@dataclass(frozen=True, slots=True)
class CommandArg:
    """
    The definition of a command argument

    Args:
        default (Optional[PrimativeType] = None): The default value for the argument. `None` indicates that it is NOT an optional argument
        coerce (Optional[Callable[..., PrimativeType]]): The function to coerce the argument to the correct type and value range. The function is throwable.
    """

    default: Optional[PrimativeType] = None
    coerce: Callable[[CommandArgInputType], PrimativeType] = DEFAULT_ARG_COERCE


@dataclass(frozen=True, slots=True)
class CommandPreset:
    """
    A command preset defines the formula and arguments for a command

    Args:
        formula (CommandFormula): The formula of the command
        args (List[CommandArg]): The arguments of the command
    """

    formula: CommandFormula
    lookback: CommandLookback
    args: List[CommandArg] = field(default_factory=list)
    series: List[str] = field(default_factory=list)


SubCommands = Dict[
    str,
    CommandPreset
]

CommandAliases = Dict[
    str,
    Optional[str]
]


PT = TypeVar('PT', bound=PrimativeType)


@dataclass(frozen=True, slots=True)
class ScalarNode(Generic[PT]):
    loc: Loc
    value: PT

    def create(self, _: Context) -> PT:
        return self.value


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """
    A CommandDefinition is a collection of a command preset, sub commands and aliases

    Args:
        preset (Optional[CommandPreset]): The command preset. `None` indicates that there are only sub commands, such as "kdj.k".
        sub_commands (Optional[Dict[str, CommandPreset]]): The sub commands. `None` indicates that there are no sub commands
        aliases (Optional[Dict[str, Optional[str]]]): The alias command names. `None` indicates that there are no aliases.
    """

    preset: Optional[CommandPreset] = None
    sub_commands: Optional[SubCommands] = None
    aliases: Optional[CommandAliases] = None

    def get_preset(
        self,
        main: ScalarNode[str],
        sub: Optional[ScalarNode[str]],
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

    def _sub_name(self, sub: Optional[ScalarNode[str]]) -> Optional[str]:
        if sub is None:
            return None

        name = sub.value

        if self.aliases is not None:
            return self.aliases.get(name, name)

        return name


Commands = Dict[str, CommandDefinition]
