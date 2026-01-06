"""
Backend configuration module for stock-pandas.

This module provides a centralized way to control whether Rust or Python
implementations are used for indicator calculations and directive parsing.
"""

import os
from typing import Optional

# Check if Rust extension is available
_RUST_AVAILABLE = False
try:
    import stock_pandas_rs  # noqa: F401
    _RUST_AVAILABLE = True
except ImportError:  # pragma: no cover
    pass

# User preference for using Rust (None means auto-detect)
_user_preference: Optional[bool] = None


def _get_env_preference() -> Optional[bool]:
    """Get the Rust preference from environment variable."""
    env_value = os.environ.get('STOCK_PANDAS_BACKEND', '').lower()
    if env_value == 'rust':
        return True
    elif env_value == 'python':
        return False
    return None


def use_rust() -> bool:
    """Check if Rust backend should be used.

    Returns:
        True if Rust backend should be used, False otherwise.
    """
    global _user_preference

    # User preference takes highest priority
    if _user_preference is not None:
        return _user_preference and _RUST_AVAILABLE

    # Environment variable is next
    env_pref = _get_env_preference()
    if env_pref is not None:
        return env_pref and _RUST_AVAILABLE

    # Default: use Rust if available
    return _RUST_AVAILABLE


def set_backend(backend: str) -> None:
    """Set the backend to use for indicator calculations.

    Args:
        backend: Either 'rust' or 'python'. Use 'auto' to reset to
                 automatic detection (use Rust if available).

    Raises:
        ValueError: If backend is not 'rust', 'python', or 'auto'.
        RuntimeError: If 'rust' is requested but Rust extension is not available.

    Example:
        >>> import stock_pandas
        >>> stock_pandas.set_backend('python')  # Force Python implementation
        >>> stock_pandas.set_backend('rust')    # Force Rust implementation
        >>> stock_pandas.set_backend('auto')    # Auto-detect (default)
    """
    global _user_preference

    backend = backend.lower()
    if backend == 'rust':
        if not _RUST_AVAILABLE:  # pragma: no cover
            raise RuntimeError(
                "Rust backend requested but stock_pandas_rs extension "
                "is not available. Please ensure it is properly installed."
            )
        _user_preference = True
    elif backend == 'python':
        _user_preference = False
    elif backend == 'auto':
        _user_preference = None
    else:
        raise ValueError(
            f"Invalid backend: {backend}. Must be 'rust', 'python', or 'auto'."
        )


def get_backend() -> str:
    """Get the current backend being used.

    Returns:
        'rust' if Rust backend is being used, 'python' otherwise.
    """
    return 'rust' if use_rust() else 'python'


def is_rust_available() -> bool:
    """Check if Rust extension is available.

    Returns:
        True if stock_pandas_rs extension is installed, False otherwise.
    """
    return _RUST_AVAILABLE
