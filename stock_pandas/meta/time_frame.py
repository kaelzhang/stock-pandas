from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Union
)

from functools import partial

from pandas import (
    Timestamp
)


TimeFrameUnifier = Callable[[Timestamp], int]

class TimeFrame:
    M1: 'TimeFrame'
    M3: 'TimeFrame'
    M5: 'TimeFrame'
    M15: 'TimeFrame'
    M30: 'TimeFrame'
    H1: 'TimeFrame'
    H2: 'TimeFrame'
    H4: 'TimeFrame'
    H6: 'TimeFrame'
    H8: 'TimeFrame'
    H12: 'TimeFrame'
    D1: 'TimeFrame'
    D3: 'TimeFrame'
    W1: 'TimeFrame'
    Month1: 'TimeFrame'
    Y1: 'TimeFrame'

    _unify: TimeFrameUnifier

    def unify(self, date: Timestamp) -> int:
        """
        Unify a timestamp to an integer

        Args:
            date (Timestamp): the timestamp to be unified

        Returns:
            int
        """
        return self._unify(date)


TimeFrameArg = Union[str, TimeFrame, None]

timeFrames: Dict[str, TimeFrame] = {}


def ensure_time_frame(value: Union[str, TimeFrame]) -> Optional['TimeFrame']:
    if isinstance(value, TimeFrame):
        return value

    timeFrame = None

    if isinstance(value, str):
        timeFrame = timeFrames.get(value)

    if timeFrame is None:
        raise ValueError(f'"{value}" is an invalid time frame')

    return timeFrame


MAGNITUDE_MINUTE = 1
MAGNITUDE_HOUR   = 100
MAGNITUDE_DATE   = 10000
MAGNITUDE_MONTH  = 1000000
MAGNITUDE_YEAR   = 100000000


def define(
    suffix: str,
    name: Union[str, List[str]],
    unify: TimeFrameUnifier
) -> TimeFrame:
    class NewClass(TimeFrame):
        _unify = unify

    NewClass.__name__ = f'TimeFrame{suffix}'

    timeFrame = NewClass()

    names = name if isinstance(name, list) else [name]

    for name in names:
        timeFrames[name] = timeFrame

    return timeFrame


def unify_minute(n: int, date: Timestamp) -> int:
    # 202501311235
    return int(
        (date.minute // n) * MAGNITUDE_MINUTE
        + date.hour * MAGNITUDE_HOUR
        + date.day * MAGNITUDE_DATE
        + date.month * MAGNITUDE_MONTH
        + date.year * MAGNITUDE_YEAR
    )


TimeFrame.M1 = define('M1', '1m', partial(unify_minute, 1))
TimeFrame.M3 = define('M3', '3m', partial(unify_minute, 3))
TimeFrame.M5 = define('M5', '5m', partial(unify_minute, 5))
TimeFrame.M15 = define('M15', '15m', partial(unify_minute, 15))
TimeFrame.M30 = define('M30', '30m', partial(unify_minute, 30))


def unify_hour(n: int, date: Timestamp) -> int:
    return int(
        (date.hour // n) * MAGNITUDE_HOUR
        + date.day * MAGNITUDE_DATE
        + date.month * MAGNITUDE_MONTH
        + date.year * MAGNITUDE_YEAR
    )


TimeFrame.H1 = define('H1', '1h', partial(unify_hour, 1))
TimeFrame.H2 = define('H2', '2h', partial(unify_hour, 2))
TimeFrame.H4 = define('H4', '4h', partial(unify_hour, 4))
TimeFrame.H6 = define('H6', '6h', partial(unify_hour, 6))
TimeFrame.H8 = define('H8', '8h', partial(unify_hour, 8))
TimeFrame.H12 = define('H12', '12h', partial(unify_hour, 12))


def unify_date(n: int, date: Timestamp) -> int:
    return int(
        (date.day // n) * MAGNITUDE_DATE
        + date.month * MAGNITUDE_MONTH
        + date.year * MAGNITUDE_YEAR
    )


TimeFrame.D1 = define('D1', ['1d', '1D'], partial(unify_date, 1))
TimeFrame.D3 = define('D3', ['3d', '3D'], partial(unify_date, 3))
TimeFrame.W1 = define('W1', '1w', partial(unify_date, 7))


def unify_month(n: int, date: Timestamp) -> int:
    return int(
        (date.month // n) * MAGNITUDE_MONTH
        + date.year * MAGNITUDE_YEAR
    )


TimeFrame.M1 = define('Month1', '1M', partial(unify_month, 1))


def unify_year(n: int, date: Timestamp) -> int:
    return int(
        (date.year // n) * MAGNITUDE_YEAR
    )


TimeFrame.Y1 = define('Y1', '1y', partial(unify_year, 1))
