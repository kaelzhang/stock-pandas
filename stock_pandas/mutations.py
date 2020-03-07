from .series import StockSeries
from .parser import ColumnName

def init_columns(df, columns):
    """
    Returns:
        str: the real column names
        list: the list of real column names
    """
    if isinstance(columns, list):
        return [init_column(df, column) for column in columns]
    else:
        return init_column(df, columns)

def init_column(df, raw_column):
    """
    Returns:
        str: the real column name
    """
    column = ColumnName.from_string(raw_column)
    command = column.command
    name = command.name

    command_preset = df.INDICATORS.get(name, None)

    if not command_preset:
        raise ValueError(f'command "{name}" is not supported')

    formula, args_settings = command_preset

    command.apply_args_settings(args_settings)

    real_column_name = str(column)

    # TODO
    df[real_column_name] = formula(df, slice(None), *command.args)

    return real_column_name

def fulfill_series(result):
    return result
