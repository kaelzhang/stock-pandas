from typing import (
    Callable,
    Dict,
    Optional,
    Union
)
from functools import partial

from pandas import (
    Timestamp
)


class TimeFrame:
    def unify(
        self,
        date: Timestamp
    ) -> int:
        raise NotImplementedError


TimeFrameArg = Union[str, TimeFrame, None]
TimeFrameUnifier = Callable[[Timestamp], int]

timeFrames: Dict[str, TimeFrame] = {}


def ensure_time_frame(value: Union[str, TimeFrame]) -> Optional['TimeFrame']:
    if isinstance(value, TimeFrame):
        return value

    timeFrame = None

    if type(value) is str:
        timeFrame = timeFrames.get(value)

    if timeFrame is None:
        raise ValueError(f'"{value}" is an invalid time frame')

    return timeFrame


MAGNITUDE_MINUTE = 0
MAGNITUDE_HOUR = 1
MAGNITUDE_DATE = 3
MAGNITUDE_MONTH = 5
MAGNITUDE_YEAR = 7


def define(suffix: str, name: str, unify_: TimeFrameUnifier) -> TimeFrame:
    class NewClass(TimeFrame):
        unify = unify_

    NewClass.__name__ = f'TimeFrame{suffix}'

    timeFrame = NewClass()

    # ensure_time_frame('1m')
    timeFrames[name] = timeFrame

    return timeFrame


def unify_minute(n: int, date: Timestamp) -> int:
    return (
        (date.minute // n) * 10 ** MAGNITUDE_MINUTE
        + date.hour * 10 ** MAGNITUDE_HOUR
        + date.day * 10 ** MAGNITUDE_DATE
        + date.month * 10 ** MAGNITUDE_MONTH
        + date.year * 10 ** MAGNITUDE_YEAR
    )


TimeFrame.M1 = define('M1', '1m', partial(unify_minute, 1))
TimeFrame.M3 = define('M3', '3m', partial(unify_minute, 3))
TimeFrame.M5 = define('M5', '5m', partial(unify_minute, 5))
TimeFrame.M15 = define('M15', '15m', partial(unify_minute, 15))
TimeFrame.M30 = define('M30', '30m', partial(unify_minute, 30))


def unify_hour(n: int, date: Timestamp) -> int:
    return (
        (date.hour // n) * 10 ** MAGNITUDE_HOUR
        + date.day * 10 ** MAGNITUDE_DATE
        + date.month * 10 ** MAGNITUDE_MONTH
        + date.year * 10 ** MAGNITUDE_YEAR
    )


TimeFrame.H1 = define('H1', '1h', partial(unify_hour, 1))
TimeFrame.H2 = define('H2', '2h', partial(unify_hour, 2))
TimeFrame.H4 = define('H4', '4h', partial(unify_hour, 4))
TimeFrame.H6 = define('H6', '6h', partial(unify_hour, 6))
TimeFrame.H8 = define('H8', '8h', partial(unify_hour, 8))
TimeFrame.H12 = define('H12', '12h', partial(unify_hour, 12))


# TODO:
# DAY = '1d'
# DAY3 = '3d'

# WEEK = '1w'
# MONTH = '1M'
