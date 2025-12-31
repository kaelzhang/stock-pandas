from stock_pandas.common import (
    period_to_int,
    column_enums
)

from stock_pandas.directive.command import (
    CommandArg
)


arg_period = CommandArg(coerce=period_to_int)
arg_column_high = CommandArg('high', column_enums)
arg_column_low = CommandArg('low', column_enums)
arg_column_close = CommandArg('close', column_enums)
arg_required = CommandArg()
