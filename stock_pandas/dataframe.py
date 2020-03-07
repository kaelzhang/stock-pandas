from pandas import (
    DataFrame,
    Series
)

from .presets import COMMAND_PRESETS
from .parser import ColumnName


class StockDataFrame(DataFrame):

    COMMAND_PRESETS = COMMAND_PRESETS

    def __init__(self, *args,
        date_column = 'date',
        **kwargs
    ):
        DataFrame.__init__(self, *args, **kwargs)

        # if date_column:
        #     self.set_index()

        self._stock_aliases = {}
        self._stock_columns = {}

    def alias(self, as_name, src_name) -> None:
        """Defines column alias

        Args:
            as_name (str): the alias name
            src_name (str): the name of the original column

        Returns:
            None
        """
        columns = self.columns
        if as_name in columns:
            raise ValueError(f'column "{as_name}" already exists')

        if src_name not in columns:
            raise ValueError(f'column "{src_name}" not exists')

        self._stock_aliases[as_name] = src_name

    def _map_alias(self, item):
        if type(item) is not str:
            return item

        return self._stock_aliases.get(item, item)

    def _map_aliases(self, item):
        if isinstance(item, list):
            return [self._map_alias(x) for x in item]

        return self._map_alias(item)


    def __getitem__(self, item):
        item = self._map_aliases(item)

        try:
            result = super().__getitem__(item)
        except KeyError:
            # This method might raise
            real_name = self._init_columns(item)

            result = super().__getitem__(real_name)

        if isinstance(result, Series):
            return result

        return StockDataFrame(result)

        # return fulfill_series(result) if isinstance(
        #     result, StockSeries
        # ) else result

    def _init_columns(self, columns):
        """
        Returns:
            str: the real column names
            list: the list of real column names
        """
        if isinstance(columns, list):
            return [self._init_column(column) for column in columns]
        else:
            return self._init_column(columns)

    def _apply_command_preset(self, command):
        if command.formula:
            return
            name = command.name

    def _init_column(self, raw_column):
        """
        Returns:
            str: the real column name
        """

        column = ColumnName.from_string(raw_column)
        column.apply_presets(self.COMMAND_PRESETS)

        command = column.command
        formula = command.formula

        real_column_name = str(column)

        # TODO
        self[real_column_name] = formula(self, slice(None), *command.args)

        return real_column_name
