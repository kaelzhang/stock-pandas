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
    STR_PARAN_R,

    STR_MINUS,
    STR_TILDE,
    STR_AT,
)

from .operator import (
    OperatorFormula,
    OperatorMap,
    OF,

    MULTIPLICATION_OPERATORS,
    ADDITION_OPERATORS,
    STYLE_OPERATORS,
    EQUALITY_OPERATORS,
    RELATIONAL_OPERATORS,
    BITWISE_AND_OPERATORS,
    BITWISE_XOR_OPERATORS,
    BITWISE_OR_OPERATORS,
    # LOGICAL_OPERATORS,

    UNARY_OPERATORS,
)

from .node import (
    ExpressionNode,
    UnaryExpressionNode,
    ExpressionNodeTypes,
    CommandNode,
    ArgumentNode,
    SeriesArgumentNode,
    OperatorNode,
    ScalarNode
)

from .types import (
    NumberType
)

from stock_pandas.exceptions import (
    DirectiveSyntaxError,
    unexpected_token
)


REGEX_DOT_WHITESPACES = re.compile(r'\.\s*', re.A)
REGEX_NUMBER = re.compile(r'^(\d+)?(?P<frac>\.\d+)?$', re.A)

DEFAULT_COMMAND_NAME = 'column'


OperatorPriority = List[OperatorMap[OperatorFormula]]

# Lower priority processes eariler,
# and comes more to the right of the list
OPERATOR_PRIORITY: OperatorPriority = [
    MULTIPLICATION_OPERATORS,
    ADDITION_OPERATORS,
    STYLE_OPERATORS,
    EQUALITY_OPERATORS,
    RELATIONAL_OPERATORS,
    BITWISE_AND_OPERATORS,
    BITWISE_XOR_OPERATORS,
    BITWISE_OR_OPERATORS,
    # LOGICAL_OPERATORS
]


class Parser:
    _input: str
    _prev_token: Token
    _token: Token
    _the_next_token: Optional[Token] = None
    _tokens: Tokenizer

    def __init__(self, directive_str: str) -> None:
        self._input = directive_str
        self._tokens = Tokenizer(self._input)
        self._next_token(True)

    def parse(self) -> ExpressionNode:

        directive = self._expect_directive()

        self._expect_eof()

        return directive

    # An _expect_<type> method
    # - should NOT next_token at the begining
    # - should next_token at the end
    # - should returns Node or Nodes

    # `directive` in "syntax.ebnf"
    def _expect_directive(self) -> ExpressionNodeTypes:
        return self._expect_expression(OPERATOR_PRIORITY.copy())

    # def _expect_operator(
    #     self,
    #     operators: OperatorMap[OF]
    # ) -> OperatorNode[OF]:
    #     """
    #     Expect an operator, if not found, raise
    #     """

    #     self._no_end()

    #     token = self._token
    #     text = token.value

    #     if (
    #         not token.special
    #         or (formula := operators.get(text)) is None
    #     ):
    #         raise DirectiveSyntaxError(
    #             self._input,
    #             '"{}" is an invalid operator',
    #             token
    #         )

    #     self._next_token()

    #     return OperatorNode[OF](
    #         loc=token.loc,
    #         name=text,
    #         formula=formula
    #     )

    # `xxx_operator` in "syntax.ebnf"
    def _detect_operator(
        self,
        operators: OperatorMap[OF]
    ) -> Optional[OperatorNode[OF]]:
        """
        Expect an operator, ok if not found, then return None
        """

        if self._token.EOF:
            return None

        if not self._token.special:
            return None

        value = self._token.value
        operator = operators.get(value)

        if operator is None:
            return None

        self._next_token()

        formula, priority = operator

        return OperatorNode[OF](
            loc=self._token.loc,
            name=value,
            formula=formula,
            priority=priority
        )

    # `xxx_expression` in "syntax.ebnf"
    def _expect_expression(
        self,
        operator_priority: OperatorPriority
    ) -> ExpressionNodeTypes:
        if not operator_priority:
            return self._expect_primary_expression()

        operators = operator_priority.pop()
        left = self._expect_expression(operator_priority.copy())

        while (
            (operator := self._detect_operator(operators))
            and operator is not None
        ):
            right = self._expect_expression(OPERATOR_PRIORITY.copy())
            left = ExpressionNode(
                loc=left.loc,
                left=left,
                operator=operator,
                right=right
            )

        return left

    # `positive_number` in "syntax.ebnf"
    def _detect_positive_number(self) -> Optional[Union[int, float]]:
        if self._token.EOF or self._token.special:
            return None

        value = self._token.value
        m = REGEX_NUMBER.match(value)

        if m is None:
            return None

        self._next_token()

        return (
            float(value)
            if m.group('frac') is not None
            else int(value)
        )

    # `number` in "syntax.ebnf"
    def _detect_number(self) -> Optional[Union[int, float]]:
        is_minus = self._is(STR_MINUS)
        if is_minus:
            self._next_token()

        number = self._detect_positive_number()
        if number is not None:
            return - number if is_minus else number

        if is_minus:
            # We need to look back to STR_MINUS
            self._look_back()

        return None

    def _expect_primary_expression(
        self
    ) -> ExpressionNodeTypes:
        self._no_end()

        unary = self._token.value
        loc = self._token.loc

        # We always need to detect whether there is a unary operator
        operator = self._detect_operator(UNARY_OPERATORS)

        # We always need to detect whether there is a number
        number = self._detect_positive_number()

        if operator is None:
            if number is not None:
                return ScalarNode[NumberType](
                    loc=loc,
                    value=number
                )
            else:
                return self._expect_primary_directive()


        if number is not None:
            if unary == STR_TILDE:
                # The number should be the unexpected token
                self._look_back()
                raise self._unexpected()

            # Then there is a minus sign
            return ScalarNode[NumberType](
                loc=loc,
                value= - number
            )

        right = self._expect_primary_directive()

        return UnaryExpressionNode(
            loc=loc,
            operator=operator,
            expression=right
        )

    def _expect_primary_directive(self) -> ExpressionNodeTypes:
        if self._is(STR_PARAN_L):
            # For `wrapped_directive` in "syntax.ebnf"
            return self._expect_wrapped_directive()

        return self._expect_command()

    def _expect_wrapped_directive(self) -> ExpressionNodeTypes:
        self._next_token()
        directive = self._expect_directive()
        self._expect(STR_PARAN_R)
        self._next_token()
        return directive

    def _expect_command(self) -> CommandNode:
        loc = self._token.loc
        name, sub = self._expect_command_name()

        if self._is(STR_COLON):
            self._next_token()
            args = self._expect_arg([])
        else:
            args = []

        if self._is(STR_AT):
            self._next_token()
            series = self._expect_series([])
        else:
            series = []

        return CommandNode(
            loc=loc,
            name=name,
            sub=sub,
            args=args,
            series=series
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

            sub = ScalarNode[str](
                loc=(loc[0], loc[1] + start),
                value=sub
            )

        self._next_token()
        return ScalarNode[str](
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
        if self._token.EOF:
            return args

        loc = self._token.loc
        number = self._detect_number()
        argument = None

        if number is not None:
            argument = ArgumentNode(
                loc=loc,
                value=ScalarNode[NumberType](
                    loc=loc,
                    value=number
                )
            )
        elif not self._token.special:
            argument = ArgumentNode(
                loc=loc,
                value=ScalarNode[str](
                    loc=loc,
                    value=self._token.value
                )
            )
            self._next_token()

        if argument is not None:
            args.append(argument)

        if self._is(STR_COMMA):
            if argument is None:
                # It allows to define a default argument:
                # `boll:,2` <=> `boll:20,2`
                args.append(
                    ArgumentNode(
                        loc=loc,
                        value=None
                    )
                )

            self._next_token()
            return self._expect_arg(args)

        return args

    def _generate_series_argument(self) -> SeriesArgumentNode:
        loc = self._token.loc
        argument = SeriesArgumentNode(
            loc=loc,
            value=ScalarNode[str](
                loc=loc,
                value=self._token.value
            )
        )
        self._next_token()
        return argument

    def _expect_series(
        self,
        series: List[SeriesArgumentNode]
    ) -> List[SeriesArgumentNode]:
        argument = None

        if self._is(STR_PARAN_L):
            argument = self._expect_wrapped_directive()
        elif not self._token.special:
            argument = self._generate_series_argument()

        if argument is not None:
            series.append(argument)

        if self._is(STR_COMMA):
            if argument is None:
                # It allows to define a default series argument:
                # `command:@,low` <=> `command@high,low`
                series.append(
                    SeriesArgumentNode(
                        loc=self._token.loc,
                        value=None
                    )
                )

            self._next_token()
            return self._expect_series(series)

        return series

    def _is(self, value: str) -> bool:
        return self._token.value == value

    def _unexpected(self) -> DirectiveSyntaxError:
        return unexpected_token(self._input, self._token)

    def _expect(self, value: str) -> None:
        self._no_end()

        if not self._is(value):
            raise self._unexpected()

    def _next_token(self, init: bool = False) -> None:
        if init:
            self._token = next(self._tokens)
            self._prev_token = self._token
            return

        self._prev_token = self._token

        if self._the_next_token is not None:
            self._token = self._the_next_token
            self._the_next_token = None
            return

        self._token = next(self._tokens)

    def _look_back(self) -> None:
        self._the_next_token = self._token
        self._token = self._prev_token

    def _expect_eof(self) -> None:
        if self._token.EOF:
            return

        raise DirectiveSyntaxError(
            self._input,
            'expect EOF, but got `{}`',
            self._token
        )
