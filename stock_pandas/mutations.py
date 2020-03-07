from .series import StockSeries
from .parser import ColumnName

def init_columns(df, columns):
    if isinstance(columns, list):
        for column in columns:
            init_column(column)
    else:
        init_column(column)

def init_column(df, column):
    command, operator, expression = parse_column_name(column)

    name = command.name

    command_preset = df.INDICATORS.get(name, None)

    if not command_preset:
        raise ValueError(f'command "{name}" not supported')

    formula, args_settings = command_preset

    args = coerce_args(name, command.args, args_settings)

def fulfill_series(result):
    return result
