from typing import (
    TypeVar,
    Union
)

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

        data = data.copy()
        apply_date_to_df(data, date_col)

        return data

    if isinstance(data, Series):
        if date_col not in data.keys():
            return data

        data: Series = data.copy()
        date = data[date_col]
        data.drop(date_col, inplace=True)
        data.rename(
            to_datetime(date, **to_datetime_kwargs)
        )
        return data

    if isinstance(data, dict):
        date_series = data.get(date_col)

        if date_series is None:
            return data

        data = data.copy()
        data[date_col] = to_datetime(date_series, **to_datetime_kwargs)
        return data

    if allow_list and isinstance(data, list):
        apply = partial(apply_date, to_datetime_kwargs, False)
        return map(apply, data)

    raise TypeError('the data to append to a stock data frame with a date column must be of type DataFrame, Series/dict-like object or list of these')


def apply_date_to_df(
    data: Union[DataFrame, Series],
    date_col: str,
    to_datetime_kwargs: dict
):
    data[date_col] = to_datetime(data[date_col], **to_datetime_kwargs)
    data.set_index(date_col, inplace=True)
