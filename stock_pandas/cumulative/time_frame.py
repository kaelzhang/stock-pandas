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
import pytz


TimeFrameArg = Union[str, '_TimeFrame', None]
TimeFrameUnifier = Callable[[Timestamp], int]


class _TimeFrame:
    def __init__(
        self,
        time_zone: Optional[str] = None,
    ):
        self._time_zone = (
            None if time_zone is None else pytz.timezone(time_zone)
        )

    def __call__(
        self,
        time_zone: Optional[str] = None
    ) -> '_TimeFrame':
        cls = type(self)
        return cls(time_zone)

    def _unify(
        self,
        date: Timestamp
    ) -> int:
        raise NotImplementedError

    def unify(
        self,
        date: Timestamp
    ) -> int:
        if self._time_zone is not None:
            date = date.tz_localize(self._time_zone)

        return self._unify(date)


class TimeFrame(_TimeFrame):
    @classmethod
    def ensure(
        cls,
        value: TimeFrameArg
    ) -> Optional['_TimeFrame']:
        if value is None:
            return None

        if isinstance(value, cls):
            return value

        timeFrame = None

        if type(value) is str:
            timeFrame = timeFrames.get(value)

        if timeFrame is None:
            raise ValueError()

        return timeFrame


timeFrames: Dict[str, _TimeFrame] = {}


MAGNITUDE_MINUTE = 0
MAGNITUDE_HOUR = 1
MAGNITUDE_DATE = 3
MAGNITUDE_MONTH = 5
MAGNITUDE_YEAR = 7


def define(name: str, s: str, unify: TimeFrameUnifier):
    class NewClass(_TimeFrame):
        _unify = unify

    NewClass.__name__ = f'TimeFrame{name}'

    define_class(name, s, NewClass)


def define_class(name: str, s: str, cls: _TimeFrame):
    timeFrame = cls()

    # TimeFrame.M1 => TimeFrameM1
    setattr(TimeFrame, s, timeFrame)

    # TimeFrame.ensure('1m')
    timeFrames[s] = timeFrames


def unify_minute(n: int, date: Timestamp) -> int:
    return (
        (date.minute // n) * 10 ** MAGNITUDE_MINUTE
        + date.hour * 10 ** MAGNITUDE_HOUR
        + date.date * 10 ** MAGNITUDE_DATE
        + date.month * 10 ** MAGNITUDE_MONTH
        + date.year * 10 ** MAGNITUDE_YEAR
    )


define('M1', '1m', partial(unify_minute, 1))
define('M3', '3m', partial(unify_minute, 3))
define('M5', '5m', partial(unify_minute, 5))
define('M15', '15m', partial(unify_minute, 15))
define('M30', '30m', partial(unify_minute, 30))


def unify_hour(n: int, date: Timestamp) -> int:
    return (
        (date.hour // n) * 10 ** MAGNITUDE_HOUR
        + date.date * 10 ** MAGNITUDE_DATE
        + date.month * 10 ** MAGNITUDE_MONTH
        + date.year * 10 ** MAGNITUDE_YEAR
    )


define('H1', '1h', partial(unify_hour, 1))
define('H2', '2h', partial(unify_hour, 2))
define('H4', '4h', partial(unify_hour, 4))
define('H6', '6h', partial(unify_hour, 6))
define('H8', '8h', partial(unify_hour, 8))
define('H12', '12h', partial(unify_hour, 12))


# TODO:
# DAY = '1d'
# DAY3 = '3d'

# WEEK = '1w'
# MONTH = '1M'
