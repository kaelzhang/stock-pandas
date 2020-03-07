from .series import StockSeries
from .utils import parse_column_name

def init_columns(df, columns):
    if isinstance(columns, list):
        for column in columns:
            init_column(column)
    else:
        init_column(column)

def init_column(df, column):
    pass
