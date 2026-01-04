import re
from typing import (
    Tuple,
    List,
    Optional,
    Union,
    # Type,
    # Dict
)

from .tokenizer import (
    Token,
    # Loc,
    Tokenizer,
    STR_COLON,
    STR_COMMA,
    STR_PARAN_L,
    STR_PARAN_R,
    # STR_MINUS,
    STR_TILDE
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
    LOGICAL_OPERATORS,

    UNARY_OPERATORS,
)

from .node import (
    ExpressionNode,
    UnaryExpressionNode,
    CommandNode,
    ArgumentNode,
    OperatorNode,
    ScalarNode
)

from stock_pandas.exceptions import (
    DirectiveSyntaxError,
    unexpected_token
)


REGEX_DOT_WHITESPACES = re.compile(r'\.\s*', re.A)


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
    LOGICAL_OPERATORS
]

ExpressionNodeTypes = Union[ExpressionNode, UnaryExpressionNode, ScalarNode]


class Parser:
    _input: str
    _token: Token
    _tokens: Tokenizer

    def __init__(self, directive_str: str) -> None:
        self._input = directive_str

    def parse(self) -> ExpressionNode:
        self._tokens = Tokenizer(self._input)

        self._next_token()
        directive = self._expect_directive()

        self._expect_eof()

        return directive

        # return RootNode.from_node(directive)

    # An _expect_<type> method
    # - should NOT next_token at the begining
    # - should next_token at the end
    # - should returns Node or Nodes

    # Actually bitwise expression
    def _expect_directive(self) -> ExpressionNodeTypes:
        return self._expect_expression(OPERATOR_PRIORITY.copy())

    def _expect_operator(
        self,
        operators: OperatorMap[OF]
    ) -> OperatorNode[OF]:
        """
        Expect an operator, if not found, raise
        """

        self._no_end()

        token = self._token
        text = token.value

        if (
            not token.special
            or (formula := operators.get(text)) is None
        ):
            raise DirectiveSyntaxError(
                self._input,
                '"{}" is an invalid operator',
                token
            )

        self._next_token()

        return OperatorNode[OF](
            loc=token.loc,
            name=text,
            formula=formula
        )

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
        formula = operators.get(value)

        if formula is None:
            return None

        self._next_token()

        return OperatorNode[OF](
            loc=self._token.loc,
            name=value,
            formula=formula
        )

    # def _expect_logical_expression(self) -> ExpressionNode:
    #     left = self._expect_bitwise_or_expression()

    #     while (
    #         (operator := self._detect_operator(LOGICAL_OPERATORS))
    #         and operator is not None
    #     ):
    #         right = self._expect_bitwise_or_expression()
    #         left = ExpressionNode(
    #             loc=left.loc,
    #             operator=operator,
    #             right=right
    #         )

    #     return left

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
            self._next_token()
            right = self._expect_expression(operator_priority.copy())
            left = ExpressionNode(
                loc=left.loc,
                operator=operator,
                right=right
            )

        return left

    def _expect_primary_expression(
        self
    ) -> ExpressionNodeTypes:
        unary = self._token.value
        loc = self._token.loc

        # We always need to detect whether there is a unary operator
        operator = self._detect_operator(UNARY_OPERATORS)

        if operator is not None:
            self._next_token()

        # We always need to detect whether there is a number
        value = self._token.value

        try:
            number = float(value)
        except ValueError:
            number = None

        if operator is None:
            if number is not None:
                self._next_token()
                return ScalarNode(
                    loc=loc,
                    value=number
                )
            else:
                return self._expect_primary_directive()


        if number is not None:
            if unary == STR_TILDE:
                return self._unexpected()

            self._next_token()
            return ScalarNode(
                loc=loc,
                value= - number
            )

        right = self._expect_primary_directive()
        self._next_token()

        return UnaryExpressionNode(
            loc=loc,
            operator=operator,
            expression=right
        )

    def _expect_primary_directive(self) -> ExpressionNode:
        if self._is(STR_PARAN_L):
            self._next_token()
            loc = self._token.loc
            directive = self._expect_directive()
            self._expect(STR_PARAN_R)
            self._next_token()
            return ExpressionNode(
                loc=loc,
                directive=directive
            )

        return self._expect_command()

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
