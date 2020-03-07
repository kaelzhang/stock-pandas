from pandas import (
    DataFrame,
    Series
)

from .command_presets import COMMAND_PRESETS
from .parser import Directive


class ColumnInfo:
    def __init__(self, size, directive):
        self.size = size
        self.directive = directive

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

        # TODO: check if fulfilled
        if isinstance(result, Series):
            return result

        return StockDataFrame(result)

    # TODO: append should maintain StockDataFrame type

    def _calc(self, directive, create_column=False):
        directive = Directive.from_string(directive)
        directive.apply_presets(self.COMMAND_PRESETS)

        command = directive.command

        column_name = str(directive)

        if column_name in self._stock_columns:
            return self._fulfill_series(column_name)

        formula = command.formula
        series = formula(self, slice(None), *command.args)

        if create_column:
            self._stock_columns[column_name] = ColumnInfo(
                len(self),
                directive
            )
            self[column_name] = series

        return series, directive, column_name

    # Returns: Series
    def _fulfill_series(self, column_name):
        # TODO
        return self[column_name]

    def calc(self, *args):
        """Calculates according to the directive

        Args:
            directive (str): directive
            create_column (:obj:`bool`, optional):
        """

        series, *_ = self._calc(*args)

        return series

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

    def _init_column(self, raw_column) -> str:
        """
        Returns:
            str: the real column name
        """

        *_, column_name = self._calc(raw_column, True)
        return column_name
