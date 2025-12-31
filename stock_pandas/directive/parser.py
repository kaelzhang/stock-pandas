import re
from typing import (
    Tuple,
    List,
    Optional,
    Union
)

from .tokenizer import (
    Token,
    # Loc,
    Tokenizer,
    STR_COLON,
    STR_COMMA,
    STR_PARAN_L,
    STR_PARAN_R
)

from .node import (
    # MetaNode,
    # Node,
    # RootNode,
    DirectiveNode,
    CommandNode,
    ArgumentNode,
    OperatorNode,
    ScalarNode
)

from stock_pandas.exceptions import (
    DirectiveSyntaxError,
    unexpected_token
)

# from stock_pandas.common import (
#     TYPE_DIRECTIVE,
#     TYPE_COMMAND,
#     TYPE_OPERATOR,
#     TYPE_ARGUMENT,
#     TYPE_SCALAR
# )

from .operator import OPERATORS


REGEX_DOT_WHITESPACES = re.compile(r'\.\s*', re.A)


class Parser:
    _input: str
    _token: Token
    _tokens: Tokenizer

    def __init__(self, directive_str: str) -> None:
        self._input = directive_str

    def parse(self) -> DirectiveNode:
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
        directive = self._expect_directive()

        self._expect_eof()

        return directive

        # return RootNode.from_node(directive)

    # An _expect_<type> method
    # - should NOT next_token at the begining
    # - should next_token at the end
    # - should returns Node or Tuple[Node]

    def _expect_directive(self) -> DirectiveNode:
        loc = self._token.loc

        command = self._expect_command()

        if self._token.EOF or self._is(STR_PARAN_R):
            # There is no operator
            # return Node(
            #     TYPE_DIRECTIVE,
            #     (command, None, None),
            #     loc
            # )
            return DirectiveNode(
                loc=loc,
                command=command
            )

        operator = self._expect_operator()
        expression = self._expect_expression()

        # return Node(
        #     TYPE_DIRECTIVE,
        #     (command, operator, expression),
        #     loc
        # )
        return DirectiveNode(
            loc=loc,
            command=command,
            operator=operator,
            expression=expression
        )

    def _expect_command(self) -> CommandNode:
        loc = self._token.loc

        name, sub = self._expect_command_name()

        self._next_token()

        if self._is(STR_COLON):
            self._next_token()
            args = self._expect_arg([])
        else:
            args = []

        return CommandNode(
            loc=loc,
            name=name,
            sub=sub,
            args=args
        )

    def _expect_command_name(self) -> Tuple[ScalarNode, Optional[ScalarNode]]:
        self._check_normal()

        text = self._token.value
        loc = self._token.loc

        m = REGEX_DOT_WHITESPACES.search(text)

        if m is None:
            # There is no dot -> no sub command name
            name, sub = text, None
        else:
            start, end = m.span()
            name, sub = text[:start], text[end:]

            sub = ScalarNode(
                loc=(loc[0], loc[1] + start),
                value=sub
            )

        return ScalarNode(
            loc=loc,
            value=name
        ), sub

    def _check_normal(self) -> None:
        self._no_end()

        if self._token.special:
            raise self._unexpected()

    def _no_end(self) -> None:
        if self._token.EOF:
            raise DirectiveSyntaxError(
                self._input,
                'unexpected EOF',
                self._token
            )

    def _expect_arg(
        self,
        args: List[ArgumentNode]
    ) -> List[ArgumentNode]:
        self._no_end()

        # ( directive )
        if self._is(STR_PARAN_L):
            self._next_token()
            loc = self._token.loc

            argument = ArgumentNode(
                loc=loc,
                value=self._expect_directive()
            )

            self._expect(STR_PARAN_R)
            self._next_token()

        # normal arg
        elif not self._token.special:
            argument = ArgumentNode(
                loc=self._token.loc,
                value=ScalarNode(
                    loc=self._token.loc,
                    value=self._token.value
                )
            )
            self._next_token()

        else:
            raise self._unexpected()

        args.append(argument)

        if self._is(STR_COMMA):
            self._next_token()
            return self._expect_arg(args)

        return args

    def _is(self, value: str) -> bool:
        return self._token.value == value

    def _unexpected(self) -> DirectiveSyntaxError:
        return unexpected_token(self._input, self._token)

    def _expect(self, value: str) -> None:
        self._no_end()

        if not self._is(value):
            raise self._unexpected()

    def _next_token(self) -> None:
        self._token = next(self._tokens)

    def _expect_operator(self) -> OperatorNode:
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

        return OperatorNode(
            loc=token.loc,
            name=text
        )

    def _expect_expression(self) -> Union[ScalarNode, CommandNode]:
        self._check_normal()

        try:
            token = self._token
            num = float(token.value)  # type: ignore
            self._next_token()

            return ScalarNode(
                loc=token.loc,
                value=num
            )

        except ValueError:
            return self._expect_command()

    def _expect_eof(self) -> None:
        if self._token.EOF:
            return

        raise DirectiveSyntaxError(
            self._input,
            'expect EOF, but got `{}`',
            self._token
        )
