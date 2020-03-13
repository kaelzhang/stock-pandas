import re
from typing import (
    Union,
    Tuple
)

from .tokenizer import (
    Tokenizer,
    STR_COLON,
    STR_COMMA,
    STR_PARAN_L,
    STR_PARAN_R,
    EOF
)

from .types import (
    Directive,
    Command,
    Argument,
    Operator
)

from stock_pandas.exceptions import (
    DirectiveSyntaxError,
    DirectiveValueError,
    unexpected_token
)

from stock_pandas.common import (
    ARGS_SEPARATOR,
    DEFAULT_ARG_VALUE,
    command_full_name
)

from .operators import OPERATORS
from .commands import COMMANDS


REGEX_DOT_WHITESPACES = re.compile('\.\s*', re.A)

class Parser:
    def __init__(
        self,
        directive_str: str, /,
        cache
    ):
        self._input = directive_str.strip()
        self._tokens = None
        self._token = None
        self._cache = cache

    def parse(self):
        self._tokens = Tokenizer(self._input)

        self._next_token()

        # Why we do not support?
        #   (directive) operator (directive)
        #
        # If a directive has operator,
        # then the result of directive must be of bool type,
        # comparison of two bool series makes no sense.
        #
        # So, to make it simple, we expect directive from the beginning
        directive = self._expect_directive(True)

        self._expect_eof()

        self._cache.set(str(directive), directive)
        self._cache = None

        return directive

    # An _expect_<type> method
    # - should NOT next_token at the begining
    # - should next_token at the end
    def _expect_directive(
        self,
        returns_object: bool
    ) -> Union[Directive, str]:
        directive = self._real_expect_directive()
        directive_str = str(directive)

        self._cache.set(directive_str, directive)

        return directive if returns_object else directive_str

    def _real_expect_directive(self) -> Directive:
        command = self._expect_command()

        if self._token is EOF or self._is(STR_PARAN_R):
            # There is no operator
            return Directive(command, None, None)

        operator = self._expect_operator()

        expression = self._expect_expression()

        return Directive(command, operator, expression)

    def _expect_command(self) -> Command:
        name, sub, preset = self._expect_command_name()

        self._next_token()

        if self._is(STR_COLON):
            self._next_token()
            args = self._expect_arg(
                [],
                0,
                command_full_name(name, sub),
                preset.args
            )
        else:
            args = []

        return Command(name, sub, args, preset.formula)

    def _expect_command_name(self):
        self._check_normal()

        text = self._token.value
        loc = self._token.loc

        m = REGEX_DOT_WHITESPACES.search(text)

        if m is None:
            # There is no dot
            name, sub = text, None
            sub_loc = (None, None)
        else:
            start, end = m.span()
            name, sub = text[:start], text[end:]
            sub_loc = (loc[0], loc[1] + start)

        preset = COMMANDS.get(name, None)

        if not preset:
            raise DirectiveValueError(
                self._input,
                f'unknown command "{name}"',
                loc
            )

        if sub is None:
            if preset.formula is None:
                raise DirectiveValueError(
                    directive_str,
                    f'sub command should be specified for command "{name}"',
                    loc
                )

            return name, sub, preset

        sub_aliases_map = preset.sub_aliases_map
        subs_map = preset.subs_map

        # apply sub aliases
        sub = sub if sub_aliases_map is None else sub_aliases_map.get(sub, sub)

        # macd.dif -> macd
        if sub is None:
            return Command(name, sub, args, preset)

        if subs_map is None:
            raise DirectiveValueError(
                self._input,
                f'command "{name}" has no sub commands',
                sub_loc
            )

        if sub not in subs_map:
            raise DirectiveValueError(
                directive_str,
                f'unknown sub command "{sub}" for command "{name}"',
                sub_loc
            )

        return name, sub, subs_map.get(sub)

    def _check_normal(self):
        self._no_end()

        if self._token.special:
            raise self._unexpected()

    def _no_end(self):
        if self._token is EOF:
            raise DirectiveSyntaxError(
                self._input,
                'unexpected EOF',
                self._token
            )

    def _expect_arg(self, args, index, command_name, preset_args) -> list:
        self._no_end()

        max_lenth = len(preset_args)
        if index == max_lenth:
            msg = f'command "{command_name}" accepts max {max_lenth} args'

            raise DirectiveValueError(self._input, msg, self._loc)

        # ( directive )
        if self._is(STR_PARAN_L):
            self._next_token()
            argument = Argument(
                self._expect_directive(False),
                True
            )

            self._expect(STR_PARAN_R)
            self._next_token()

        # normal arg
        elif not self._token.special:
            argument = Argument(self._token.value, False)
            self._next_token()


        else:
            raise self._unexpected()

        default, setter = preset_args[index]
        arg = argument.value

        if arg == DEFAULT_ARG_VALUE:
            arg = default

        # Setter could be optional
        elif setter:
            try:
                arg = setter(arg)
            except ValueError as e:
                raise DirectiveValueError(
                    self._input,
                    str(e),
                    self._loc
                )

        if arg is None:
            raise DirectiveValueError(
                self._input,
                f'args[{index}] is required for command "{command_name}"',
                self._loc
            )

        argument.value = arg
        args.append(argument)

        if self._is(STR_COMMA):
            self._next_token()
            return self._expect_arg(
                args,
                index + 1,
                command_name,
                preset_args
            )

        return args

    def _is(self, value: str) -> bool:
        return self._token.value == value

    def _unexpected(self):
        return unexpected_token(self._input, self._token)

    def _expect(self, value):
        self._no_end()

        if not self._is(value):
            raise self._unexpected()

    def _next_token(self):
        self._token = next(self._tokens)

    def _expect_operator(self):
        self._no_end()

        token = self._token
        text = token.value

        if not token.special or text not in OPERATORS:
            raise DirectiveSyntaxError(
                self._input,
                '"{}" is an invalid operator',
                token
            )

        self._next_token()

        return Operator(text, OPERATORS.get(text))

    def _expect_expression(self):
        self._check_normal()

        try:
            num = float(self._token.value)
            self._next_token()
            return num

        except ValueError:
            return self._expect_command()

    def _expect_eof(self):
        if self._token is EOF:
            return

        raise DirectiveSyntaxError(
            self._input,
            'expect EOF, but got `{}`',
            self._token
        )
