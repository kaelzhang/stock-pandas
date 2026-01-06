"""
Benchmark tests for comparing Rust and Python implementations.

Run with:
    make benchmark              # Run benchmarks with current backend
    make benchmark-compare      # Compare Rust vs Python performance
"""

import stock_pandas as sp

from .common import get_tencent


def create_fresh_stock(filename='tencent_full.csv'):
    """Create a fresh StockDataFrame without any cached columns."""
    return get_tencent(filename=filename)


class TestBenchmarkIndicators:
    """Benchmark tests for indicator calculations."""

    def test_benchmark_ma(self, benchmark):
        """Benchmark Simple Moving Average."""
        def run():
            stock = create_fresh_stock()
            return stock['ma:20']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_ema(self, benchmark):
        """Benchmark Exponential Moving Average."""
        def run():
            stock = create_fresh_stock()
            return stock['ema:20']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_macd(self, benchmark):
        """Benchmark MACD."""
        def run():
            stock = create_fresh_stock()
            return stock['macd']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_macd_signal(self, benchmark):
        """Benchmark MACD Signal."""
        def run():
            stock = create_fresh_stock()
            return stock['macd.signal']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_boll(self, benchmark):
        """Benchmark Bollinger Bands (middle)."""
        def run():
            stock = create_fresh_stock()
            return stock['boll']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_boll_upper(self, benchmark):
        """Benchmark Bollinger Bands (upper)."""
        def run():
            stock = create_fresh_stock()
            return stock['boll.upper']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_rsi(self, benchmark):
        """Benchmark RSI."""
        def run():
            stock = create_fresh_stock()
            return stock['rsi:14']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_kdj_k(self, benchmark):
        """Benchmark KDJ K."""
        def run():
            stock = create_fresh_stock()
            return stock['kdj.k']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_atr(self, benchmark):
        """Benchmark ATR."""
        def run():
            stock = create_fresh_stock()
            return stock['atr']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_llv(self, benchmark):
        """Benchmark LLV (Lowest of Low Value)."""
        def run():
            stock = create_fresh_stock()
            return stock['llv:20']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_hhv(self, benchmark):
        """Benchmark HHV (Highest of High Value)."""
        def run():
            stock = create_fresh_stock()
            return stock['hhv:20']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_bbw(self, benchmark):
        """Benchmark Bollinger Band Width."""
        def run():
            stock = create_fresh_stock()
            return stock['bbw']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_bbi(self, benchmark):
        """Benchmark BBI (Bull and Bear Index)."""
        def run():
            stock = create_fresh_stock()
            return stock['bbi']

        result = benchmark(run)
        assert len(result) > 0


class TestBenchmarkParsing:
    """Benchmark tests for directive parsing."""

    def test_benchmark_parse_simple(self, benchmark):
        """Benchmark parsing a simple directive."""
        from stock_pandas.directive.parse import parse
        from stock_pandas.directive.cache import DirectiveCache
        from stock_pandas.commands.base import BUILTIN_COMMANDS

        def run():
            cache = DirectiveCache()
            return parse('ma:20', cache, BUILTIN_COMMANDS)

        result = benchmark(run)
        assert result is not None

    def test_benchmark_parse_complex(self, benchmark):
        """Benchmark parsing a complex directive."""
        from stock_pandas.directive.parse import parse
        from stock_pandas.directive.cache import DirectiveCache
        from stock_pandas.commands.base import BUILTIN_COMMANDS

        def run():
            cache = DirectiveCache()
            return parse('macd.signal:12,26,9@close', cache, BUILTIN_COMMANDS)

        result = benchmark(run)
        assert result is not None

    def test_benchmark_parse_expression(self, benchmark):
        """Benchmark parsing an expression directive."""
        from stock_pandas.directive.parse import parse
        from stock_pandas.directive.cache import DirectiveCache
        from stock_pandas.commands.base import BUILTIN_COMMANDS

        def run():
            cache = DirectiveCache()
            return parse('ma:5 > ma:20', cache, BUILTIN_COMMANDS)

        result = benchmark(run)
        assert result is not None


class TestBenchmarkComplex:
    """Benchmark tests for complex operations."""

    def test_benchmark_multiple_indicators(self, benchmark):
        """Benchmark calculating multiple indicators at once."""
        def run():
            stock = create_fresh_stock()
            _ = stock['ma:5']
            _ = stock['ma:20']
            _ = stock['ema:12']
            _ = stock['macd']
            return stock['boll.upper']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_expression(self, benchmark):
        """Benchmark evaluating an expression."""
        def run():
            stock = create_fresh_stock()
            return stock['ma:5 > ma:20']

        result = benchmark(run)
        assert len(result) > 0

    def test_benchmark_cross(self, benchmark):
        """Benchmark cross detection."""
        def run():
            stock = create_fresh_stock()
            return stock['ma:5 >< ma:20']

        result = benchmark(run)
        assert len(result) > 0


def test_backend_info():
    """Print current backend information."""
    print(f"\nCurrent backend: {sp.get_backend()}")
    print(f"Rust available: {sp.is_rust_available()}")
