from __future__ import annotations
from typing import (
    Tuple,
    Optional,
    Dict,
    TypeVar,
    Generic
)
from dataclasses import dataclass

from stock_pandas.exceptions import DirectiveValueError

from .cache import DirectiveCache
from .tokenizer import Loc
from .types import (
    PrimativeType,
    ReturnType,
    CommandPreset,
    CommandArg
)


@dataclass(frozen=True, slots=True)
class Context:
    input: str
    cache: DirectiveCache
    commands: Commands


SubCommands = Dict[
    str,
    CommandPreset
]

CommandAliases = Dict[
    str,
    Optional[str]
]


PT = TypeVar('PT', bound=PrimativeType)

# TODO:
# In Python 3.10, we can't use slots=True with Generic,
# add slots=True if we drop support for Python 3.10 in the future
@dataclass(frozen=True)
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
                    f'command "{main_name}" supports no sub commands',
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

def _column(series: ReturnType) -> ReturnType:
    """Gets the series of the column named `column`
    """
    return series


def lookback_zero(*args) -> int:
    return 0


COMMAND_COLUMN_PRESET = CommandPreset(
    formula=_column,
    lookback=lookback_zero,
    args=[],
    series=[CommandArg(default='close')]
)
