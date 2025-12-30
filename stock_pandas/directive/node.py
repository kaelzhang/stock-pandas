from typing import (
    Optional,
    Union
)

from .types import (
    Directive
)
from .operator import OPERATORS
from .tokenizer import Loc


class Context:
    __slots__ = (
        'input',
        'loc',
        'cache'
    )

    def __init__(
        self,
        input: str,
        loc: Loc,
        cache: DirectiveCache,
        commands: Dict[]
    ):
        self.input = input
        self.loc = loc
        self.cache = cache


class MetaNode:
    """
    The meta node which is used to distinguish the type of Node and RootNode
    """

    # __slots__ = ('label', 'data', 'loc')

    # label: int
    # data: NodeData
    loc: Loc

    # def __init__(self, t, data, loc):
    #     self.label = t
    #     self.data = data
    #     self.loc = loc


class Node(MetaNode):
    ...


class RootNode(MetaNode):
    @classmethod
    def from_node(cls, node: MetaNode) -> 'RootNode':
        return cls(
            node.label,
            node.data,
            node.loc
        )


ExpressionNode = Union['ScalarNode', 'CommandNode']


class DirectiveNode(Node):
    command: 'CommandNode'
    operator: Optional['OperatorNode']
    expression: Optional[ExpressionNode]
    # loc: Loc

    def __init__(
        self,
        command: 'CommandNode',
        operator: Optional['OperatorNode'],
        expression: Optional[ExpressionNode],
        loc: Loc
    ) -> None:
        self.command = command
        self.operator = operator
        self.expression = expression
        self.loc = loc

    def create(
        self,
        context: Context
    ) -> Directive:
        directive = (
            Directive(self.command)
            if self.operator is None
            else Directive(self.command, self.operator, self.expression)
        )

        context.cache.set(str(directive), directive)

        return directive


class CommandNode(Node):
    name: str
    sub: Optional[str]
    args: List['ArgumentNode']
    loc: Loc

    def __init__(
        self,
        name: str,
        sub: Optional[str],
        args: List['ArgumentNode'],
        loc: Loc
    ) -> None:
        self.name = name
        self.sub = sub
        self.args = args
        self.loc = loc


class ArgumentNode(Node):
    value: Union['DirectiveNode', 'ScalarNode']
    loc: Loc

    def __init__(
        self,
        value: Union['DirectiveNode', 'ScalarNode'],
        loc: Loc
    ) -> None:
        self.value = value
        self.loc = loc


class OperatorNode(Node):
    operator: str
    loc: Loc

    def __init__(
        self,
        operator: str,
        loc: Loc
    ) -> None:
        self.operator = operator
        self.loc = loc

    def create(self, _: Context) -> Operator:
        return Operator(self.operator, OPERATORS.get(self.operator))


class ScalarNode(Node):
    def __init__(
        self,
        value: str,
        loc: Loc
    ) -> None:
        self.value = value
        self.loc = loc

    def create(self):
        return self.value

