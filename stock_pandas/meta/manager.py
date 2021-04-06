import weakref

from pandas import DataFrame

# from stock_pandas._libs.indexer import IndexerBase

from stock_pandas.properties import (
    KEY_TIME_FRAME_MANAGER
)

from stock_pandas.common import (
    set_attr
)


class TimeFrameManager:
    def __init__(self, obj: DataFrame):
        self.obj = obj
        self._frames = {}


# Mixin
# -------------------------------------------------------

class TimeFrameMixin:
    """
    Usage::

        stock.timeFrame['15m']
    """

    @property
    def timeFrame(self) -> TimeFrameManager:
        manager = getattr(self, KEY_TIME_FRAME_MANAGER)

        if manager is None:
            manager = TimeFrameManager(self)
            set_attr(self, KEY_TIME_FRAME_MANAGER, weakref.ref(manager))

        return manager
