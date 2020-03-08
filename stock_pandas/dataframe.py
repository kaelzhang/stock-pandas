from pandas import (
    DataFrame,
    Series
)

from .command_presets import COMMAND_PRESETS
from .directive import Directive
from .common import (
    copy_stock_metas
)


class ColumnInfo:
    def __init__(self, size, directive, period):
        self.size = size
        self.directive = directive
        self.period = period


class StockDataFrame(DataFrame):

    COMMAND_PRESETS = COMMAND_PRESETS

    def __init__(self,
                 data=None,
                 # date_column = 'date',
                 stock_aliases={},
                 stock_columns={},
                 *args,
                 **kwargs
                 ):
        DataFrame.__init__(self, data, *args, **kwargs)

        # if date_column:
        #     self.set_index()

        if isinstance(data, StockDataFrame):
            copy_stock_metas(data, self)
        else:
            self._stock_aliases = stock_aliases
            self._stock_columns = stock_columns

        self._create_column = False

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
        if not isinstance(item, str):
            return item

        return self._stock_aliases.get(item, item)

    def _map_aliases(self, item):
        if isinstance(item, list):
            return [self._map_alias(x) for x in item]

        return self._map_alias(item)

    def _parse_directive(self, directive):
        directive = Directive.from_string(directive)
        directive.apply_presets(self.COMMAND_PRESETS)
        return directive

    def __getitem__(self, item):
        item = self._map_aliases(item)

        try:
            result = super().__getitem__(item)
        except KeyError:
            # This method might raise
            self._create_column = True
            real_name = self._init_columns(item)
            self._create_column = False

            result = super().__getitem__(real_name)

        # TODO: check if fulfilled
        if isinstance(result, Series):
            return result
            # return self._fulfill_series(result)

        return StockDataFrame(result)

    def _ensure_stock_type(self, df):
        return StockDataFrame(
            df,
            stock_aliases=self._stock_aliases,
            stock_columns=self._stock_columns
        )

    def append(self, *args, **kwargs):
        return self._ensure_stock_type(super().append(*args))

    def _fulfill_series(self, column_name):
        column_info = self._stock_columns.get(column_name)
        size = len(self)

        series = self[column_name]

        if size == column_info.size:
            # Already fulfilled
            return series

        delta = size - column_info.size
        offset_slice = slice(- column_info.period - delta + 1, None)
        fulfill_slice = slice(- delta, None)

        partial, _ = column_info.directive.run(self, offset_slice)

        series[fulfill_slice] = partial[fulfill_slice]

        column_info.size = size

        return series

    def _calc(self, directive):
        directive = self._parse_directive(directive)

        column_name = str(directive)

        # TODO: column deletion by pandas
        if column_name in self._stock_columns:
            return self._fulfill_series(column_name), directive, column_name

        series, period = directive.run(
            self,
            # create the whole series
            slice(None)
        )

        if self._create_column:
            self._stock_columns[column_name] = ColumnInfo(
                len(self),
                directive,
                period
            )
            self[column_name] = series

        return series, directive, column_name

    def calc(self, directive, create_column=None):
        """Calculates according to the directive.

        This method is **NOT** Thread-safe.

        Args:
            directive (str): directive
            create_column (:obj:`bool`, optional): whether we should create a column for the calculated series.

        Returns:
            pandas.Series
        """

        # We should call self.calc() without `create_column`
        # inside command formulas
        explicit_create_column = isinstance(create_column, bool)

        if explicit_create_column:
            self._create_column = create_column
        else:
            # cases
            # 1. called by users
            # 2. or called by command formulas
            create_column = self._create_column

        series, *_ = self._calc(directive)

        if explicit_create_column:
            # Set back to default value, since we complete calculatiing
            self._create_column = False

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

        *_, column_name = self._calc(raw_column)
        return column_name
