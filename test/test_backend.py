"""Tests for the backend module."""

import os
import pytest
import stock_pandas as sp
from stock_pandas.backend import (
    use_rust,
    set_backend,
    get_backend,
    is_rust_available,
    _get_env_preference,
)


class TestBackend:
    """Test backend switching functionality."""

    _original_env: str | None = None

    def setup_method(self):
        """Reset backend before each test, preserving original env var."""
        # Save original environment variable
        self._original_env = os.environ.get('STOCK_PANDAS_BACKEND')
        set_backend('auto')

    def teardown_method(self):
        """Restore original backend after each test."""
        set_backend('auto')
        # Restore original environment variable
        if self._original_env is not None:
            os.environ['STOCK_PANDAS_BACKEND'] = self._original_env
        elif 'STOCK_PANDAS_BACKEND' in os.environ:
            # Only delete if we didn't have one originally
            del os.environ['STOCK_PANDAS_BACKEND']

    def test_is_rust_available(self):
        """Test that Rust is available."""
        assert is_rust_available() is True

    def test_default_backend(self):
        """Test default backend is Rust when available."""
        # Clear env var for this specific test
        if 'STOCK_PANDAS_BACKEND' in os.environ:
            del os.environ['STOCK_PANDAS_BACKEND']
        set_backend('auto')
        assert get_backend() == 'rust'
        assert use_rust() is True

    def test_set_backend_python(self):
        """Test setting backend to Python."""
        set_backend('python')
        assert get_backend() == 'python'
        assert use_rust() is False

    def test_set_backend_rust(self):
        """Test setting backend to Rust."""
        set_backend('rust')
        assert get_backend() == 'rust'
        assert use_rust() is True

    def test_set_backend_auto(self):
        """Test setting backend to auto."""
        # Clear env var for this specific test
        if 'STOCK_PANDAS_BACKEND' in os.environ:
            del os.environ['STOCK_PANDAS_BACKEND']
        set_backend('python')
        assert get_backend() == 'python'
        set_backend('auto')
        assert get_backend() == 'rust'

    def test_set_backend_case_insensitive(self):
        """Test that backend setting is case insensitive."""
        # Clear env var for this specific test
        if 'STOCK_PANDAS_BACKEND' in os.environ:
            del os.environ['STOCK_PANDAS_BACKEND']
        set_backend('PYTHON')
        assert get_backend() == 'python'
        set_backend('RUST')
        assert get_backend() == 'rust'
        set_backend('Auto')
        assert get_backend() == 'rust'

    def test_set_backend_invalid(self):
        """Test that invalid backend raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            set_backend('invalid')
        assert "Invalid backend" in str(exc_info.value)

    def test_env_preference_rust(self):
        """Test environment variable preference for Rust."""
        os.environ['STOCK_PANDAS_BACKEND'] = 'rust'
        set_backend('auto')  # Reset user preference
        assert _get_env_preference() is True
        assert use_rust() is True

    def test_env_preference_python(self):
        """Test environment variable preference for Python."""
        os.environ['STOCK_PANDAS_BACKEND'] = 'python'
        set_backend('auto')  # Reset user preference
        assert _get_env_preference() is False
        assert use_rust() is False

    def test_env_preference_none(self):
        """Test no environment variable set."""
        if 'STOCK_PANDAS_BACKEND' in os.environ:
            del os.environ['STOCK_PANDAS_BACKEND']
        assert _get_env_preference() is None

    def test_env_preference_empty(self):
        """Test empty environment variable."""
        os.environ['STOCK_PANDAS_BACKEND'] = ''
        assert _get_env_preference() is None

    def test_user_preference_overrides_env(self):
        """Test that user preference overrides environment variable."""
        os.environ['STOCK_PANDAS_BACKEND'] = 'rust'
        set_backend('python')
        assert get_backend() == 'python'

    def test_module_level_exports(self):
        """Test that functions are exported at module level."""
        assert hasattr(sp, 'set_backend')
        assert hasattr(sp, 'get_backend')
        assert hasattr(sp, 'is_rust_available')
        assert hasattr(sp, 'use_rust')
