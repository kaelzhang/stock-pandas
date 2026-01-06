import pytest

from stock_pandas import (
    StockDataFrame,
    CommandDefinition,
    CommandPreset,
    CommandArg,
    CommandArgInputType,
    DirectiveCache
)

from stock_pandas.directive.parse import parse

from .common import (
    create_stock
)


@pytest.fixture
def stock():
    return create_stock()


def test_sub_class(stock: StockDataFrame):
    commands = StockDataFrame.COMMANDS.copy()
    commands2 = commands.copy()

    cache = DirectiveCache()

    assert str(
        parse('ma:5', cache, commands)
    ) == 'ma:5'

    ma = commands['ma'].preset

    def period_coerce(value: CommandArgInputType) -> int:
        return int(value) + 10

    commands2['ma'] = CommandDefinition(
        CommandPreset(
            formula=ma.formula,
            lookback=ma.lookback,
            args=[
                CommandArg(
                    default=2,
                    # Actually, the coercer changed
                    coerce=period_coerce
                )
            ],
            series=ma.series
        )
    )

    cache2 = DirectiveCache()

    assert str(
        parse('ma:5', cache2, commands2)
    ) == 'ma:15'


def test_define_command(stock: StockDataFrame):
    """Test that define_command properly registers a command."""
    # Get original ma definition
    original_ma = StockDataFrame.COMMANDS['ma'].preset

    # Create a custom command
    def custom_formula(period, series):
        return series.rolling(period).mean() * 2

    def custom_lookback(period):
        return period - 1

    custom_def = CommandDefinition(
        CommandPreset(
            formula=custom_formula,
            lookback=custom_lookback,
            args=[CommandArg(5)],
            series=original_ma.series
        )
    )

    # Create a subclass to avoid polluting the main class
    class TestStockDataFrame(StockDataFrame):
        pass

    # Define a new command
    TestStockDataFrame.define_command('custom_ma', custom_def)

    # Verify the command was registered
    assert 'custom_ma' in TestStockDataFrame.COMMANDS
    assert TestStockDataFrame.COMMANDS['custom_ma'] == custom_def
