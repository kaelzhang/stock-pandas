from .parser import Parser
from .types import Directive
from .cache import DirectiveCache
from .command import (
    Context,
    Commands
)


def parse(
    directive_str: str,
    cache: DirectiveCache,
    commands: Commands
) -> Directive:
    directive_str = directive_str.strip()

    cached = cache.get(directive_str)
    if cached is not None:
        return cached

    ast = Parser(directive_str).parse()

    directive = ast.create(
        Context(
            input=directive_str,
            loc=ast.loc,
            cache=cache,
            commands=commands
        )
    )

    return cache.set(directive_str, directive)
