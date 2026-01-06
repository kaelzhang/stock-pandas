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
