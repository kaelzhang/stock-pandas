import pandas as pd
import numpy as np

from .indicators import INDICATORS
from .series import StockSeries
from .mutations import (
    init_columns,
    fulfill_series
)


class StockDataFrame(pd.DataFrame):

    INDICATORS = INDICATORS

    def __getitem__(self, item):
        try:
            result = self.retype(super().__getitem__(item))
        except KeyError:
            # This method might raise
            init_columns(self, item)

            result = self.retype(super().__getitem__(item))

        return fulfill_series(result) if isinstance(
            result, StockSeries
        ) else result
