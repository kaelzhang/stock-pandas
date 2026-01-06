from stock_pandas.backend import use_rust

from .parser import Parser
from .types import Directive
from .cache import DirectiveCache
from .command import (
    Context,
    Commands
)

# Lazy import for Rust parser
_rs_parse_directive = None


def _get_rs_parse_directive():
    """Lazy load Rust parser to avoid circular imports."""
    global _rs_parse_directive
    if _rs_parse_directive is None:
        try:
            from stock_pandas_rs import parse_directive
            _rs_parse_directive = parse_directive
        except ImportError:
            pass
    return _rs_parse_directive


def parse(
    directive_str: str,
    cache: DirectiveCache,
    commands: Commands
) -> Directive:
    """Parse a directive string into a Directive object.

    This function uses the Rust-based parser when available for better
    performance, falling back to the Python implementation otherwise.

    Args:
        directive_str: The directive string to parse
        cache: The directive cache for memoization
        commands: The available commands dictionary

    Returns:
        A Directive object (Command, Expression, or UnaryExpression)
    """
    directive_str = directive_str.strip()

    # Check cache first
    cached = cache.get(directive_str)
    if cached is not None:
        return cached

    # Try to use Rust parser when available and enabled
    rs_parse = _get_rs_parse_directive()
    if use_rust() and rs_parse is not None:
        try:
            # The Rust parser will:
            # 1. Tokenize and parse the directive string
            # 2. Create Python AST nodes
            # 3. Call .create() to get the final Directive object
            directive = rs_parse(directive_str, commands)
            return cache.set(directive_str, directive)
        except Exception:
            # Fall back to Python parser if Rust fails
            pass

    # Fall back to Python-based parser
    ast = Parser(directive_str).parse()

    directive = ast.create(
        Context(
            input=directive_str,
            cache=cache,
            commands=commands
        )
    )

    return cache.set(directive_str, directive)
