from stock_pandas.backend import use_rust, is_rust_available

from .parser import Parser
from .types import Directive
from .cache import DirectiveCache
from .command import (
    Context,
    Commands
)

# Import Rust parser if available
if is_rust_available():
    from stock_pandas_rs import parse_directive as _rs_parse_directive


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
    if use_rust():
        try:
            # The Rust parser will:
            # 1. Tokenize and parse the directive string
            # 2. Create Python AST nodes
            # 3. Call .create() to get the final Directive object
            directive = _rs_parse_directive(directive_str, commands)
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
