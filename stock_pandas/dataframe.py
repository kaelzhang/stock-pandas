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
            real_name = init_columns(self, item)

            result = self.retype(super().__getitem__(real_name))

        return fulfill_series(result) if isinstance(
            result, StockSeries
        ) else result

    @staticmethod
    def retype(data_frame, index_column='date'):
        """Converts `pandas.DataFrame` instance to `StockDataFrame`

        Args:
            data_frame (pd.DataFrame):
            index_column (:obj:`str`, optional): name of the column that will be used as index. Defaults to `date`

        Returns:
            StockDataFrame
        """

        if not isinstance(data_frame, pd.DataFrame):
            data_frame = pd.DataFrame(data_frame)

        # use all lower case for column name
        data_frame.columns = map(lambda c: c.lower(), data_frame.columns)
        index_column = index_column.lower()

        if index_column in data_frame.columns:
            data_frame.set_index(index_column, inplace=True)

        data_frame = StockDataFrame(data_frame)

        return data_frame
