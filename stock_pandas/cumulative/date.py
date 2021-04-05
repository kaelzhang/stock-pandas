from typing import TypeVar

from functools import partial

from pandas import (
    DataFrame,
    Series,
    to_datetime
)


T = TypeVar('T')


def apply_date(
    date_col: str,
    to_datetime_kwargs: dict,
    allow_list: bool,
    data: T
) -> T:
    if isinstance(data, DataFrame):
        if date_col not in data.columns:
            return data

        df = data.copy()
        apply_date_to_df(df, date_col, to_datetime_kwargs)

        return df

    if isinstance(data, Series):
        if date_col not in data.keys():
            return data

        series: Series = data.copy()
        apply_date_to_series(series, date_col, to_datetime_kwargs)

        return series

    if isinstance(data, dict):
        date_series = data.get(date_col)

        if date_series is None:
            return data

        series = Series(data)
        apply_date_to_series(series, date_col, to_datetime_kwargs)

        return series

    if allow_list and isinstance(data, list):
        apply = partial(apply_date, date_col, to_datetime_kwargs, False)
        return list(map(apply, data))

    prefix = '' if allow_list else 'list of '

    raise TypeError(f'the data to append to a stock data frame with a date column must be of type DataFrame, Series/dict-like object or list of these, but got {prefix}{type(data)}')


def apply_date_to_series(
    series: Series,
    date_col: str,
    to_datetime_kwargs: dict
):
    date = series[date_col]
    series.drop(date_col, inplace=True)
    series.rename(
        to_datetime(date, **to_datetime_kwargs), inplace=True
    )


def apply_date_to_df(
    df: DataFrame,
    date_col: str,
    to_datetime_kwargs: dict
):
    df[date_col] = to_datetime(df[date_col], **to_datetime_kwargs)
    df.set_index(date_col, inplace=True)
