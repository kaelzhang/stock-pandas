# from enum import Enum as _Enum


# class Enum(_Enum):
#     def __str__(self) -> str:
#         return str(self.value)


# class TimeFrame(Enum):
#     M1 = '1m'
#     M3 = '3m'
#     M5 = '5m'
#     M15 = '15m'
#     M30 = '30m'

#     H = '1h'
#     H2 = '2h'
#     H4 = '4h'
#     H6 = '6h'
#     H8 = '8h'
#     H12 = '12h'

#     DAY = '1d'
#     DAY3 = '3d'

#     WEEK = '1w'
#     MONTH = '1M'


from typing import (
    Optional,
    Union
)


TimeFrameArg = Union[str, 'TimeFrame', None]


class TimeFrame:
    @classmethod
    def ensure(
        cls,
        value: TimeFrameArg
    ) -> Optional['TimeFrame']:
        if value is None:
            return None

    def __init__(self):
        ...


# TimeFrame.M1 =
