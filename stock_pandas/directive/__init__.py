from .parser import Parser
from .factory import create_by_node
from .types import Directive
from .cache import DirectiveCache


directive_cache = DirectiveCache()


def parse(
    directive_str: str,
    cache: DirectiveCache
) -> Directive:
    directive_str = directive_str.strip()

    cached = cache.get(directive_str)
    if cached is not None:
        return cached

    ast = Parser(directive_str).parse()

    directive, _ = create_by_node(ast, directive_str, cache)

    return cache.set(directive_str, directive)


def directive_stringify(directive_str: str) -> str:
    return str(parse(directive_str, directive_cache))
