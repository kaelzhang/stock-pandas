from typing import Tuple

from pandas import (
    DataFrame,
    Series,
    to_datetime
)
import numpy as np

from .directive import parse

from .common import (
    copy_stock_metas,
    set_stock_metas,
    ensure_return_type
)


class ColumnInfo:
    def __init__(self, size, directive, period) -> None:
        self.size = size
        self.directive = directive
        self.period = period


class StockDataFrame(DataFrame):
    """The wrapper class for `pandas.DataFrame`

    Args definitions are the same as `pandas.DataFrame`
    """

    def __init__(
        self,
        data=None,
        date_column=None,
        create_stock_metas: bool = True,
        *args,
        **kwargs
    ) -> None:
        DataFrame.__init__(self, data, *args, **kwargs)

        if isinstance(data, StockDataFrame):
            copy_stock_metas(data, self)
        elif create_stock_metas:
            set_stock_metas(self)

        self._create_column = False

        if date_column:
            self[date_column] = to_datetime(self[date_column])
            self.set_index(date_column, inplace=True)

    def __getitem__(self, key):
        key = self._map_key(key)

        result = super().__getitem__(key)

        if isinstance(result, Series):
            # The series has already been fulfilled by
            # `self._get_or_calc_series()`
            return result

        return StockDataFrame(result)

    def exec(
        self,
        directive_str: str,
        create_column: bool = None
    ) -> np.ndarray:
        """Executes the given directive and
        returns a numpy ndarray according to the directive.

        This method is **NOT** Thread-safe.

        Args:
            directive (str): directive
            create_column (:obj:`bool`, optional): whether we should create a
            column for the calculated series.

        Returns:
            np.ndarray
        """

        if self._is_normal_column(directive_str):
            return self[directive_str].to_numpy()

        # We should call self.exec() without `create_column`
        # inside command formulas
        explicit_create_column = isinstance(create_column, bool)
        original_create_column = self._create_column

        if explicit_create_column:
            self._create_column = create_column
        else:
            # cases
            # 1. called by users
            # 2. or called by command formulas
            create_column = self._create_column

        series = self._calc(directive_str)

        if explicit_create_column:
            # Set back to default value, since we complete calculatiing
            self._create_column = original_create_column

        return series

    def alias(self, as_name, src_name) -> None:
        """Defines column alias or directive alias

        Args:
            as_name (str): the alias name
            src_name (str): the name of the original column, or directive

        Returns:
            None
        """
        columns = self.columns
        if as_name in columns:
            raise ValueError(f'column "{as_name}" already exists')

        if src_name not in columns:
            raise ValueError(f'column "{src_name}" not exists')

        self._stock_aliases_map[as_name] = src_name

    def _map_key(self, key):
        if isinstance(key, str):
            return self._map_keys([key])[0]

        if isinstance(key, list):
            return self._map_keys(key)

        return key

    def _map_keys(self, keys):
        columns = self.columns

        mapped = []

        for key in keys:
            if not isinstance(key, str):
                # It might be an `pandas.DataFrame` indexer type,
                # or an KeyError which we should let pandas raise
                mapped.append(key)
                continue

            if key in columns:
                # There exists a column named `key`
                mapped.append(key)
                continue

            # Map alias, if the key is an alias
            alias = self._stock_aliases_map.get(key, None)

            if alias is not None:
                mapped.append(alias)
                continue

            # Not exists
            directive = self._parse_directive(key)

            # It is a valid directive
            # If the column exists, then fulfill it,
            #   else create it
            column_name, _ = self._get_or_calc_series(directive, True)

            # Append the real column name to the mapped key,
            #   So `pandas.DataFrame.__getitem__` could index the right column
            mapped.append(column_name)

        return mapped

    def _parse_directive(self, directive_str: str):
        return parse(directive_str, self._stock_directives_cache)

    def _get_or_calc_series(
        self,
        directive,
        create_column: bool
    ) -> Tuple[str, np.ndarray]:
        """Gets the series column corresponds the `directive` or
        calculate by using the `directive`

        Args:
            directive (Directive): the parsed `Directive` instance
            create_column (bool): whether we should create a column for the
            calculated series

        Returns:
            Tuple[str, np.ndarray]: the name of the series, and the series
        """

        name = str(directive)

        if name in self._stock_columns_info_map:
            return name, self._fulfill_series(name)

        array, period = directive.run(
            self,
            # create the whole series
            slice(None)
        )

        if create_column:
            self._stock_columns_info_map[name] = ColumnInfo(
                len(self),
                directive,
                period
            )
            self[name] = array

        return name, array

    def _fulfill_series(self, column_name: str) -> np.ndarray:
        column_info = self._stock_columns_info_map.get(column_name)
        size = len(self)

        series = self[column_name]

        if size == column_info.size:
            # Already fulfilled
            return series.to_numpy()

        delta = size - column_info.size
        offset_slice = slice(- column_info.period - delta + 1, None)
        fulfill_slice = slice(- delta, None)

        partial, _ = column_info.directive.run(self, offset_slice)

        series[fulfill_slice] = partial[fulfill_slice]

        column_info.size = size

        return series.to_numpy()

    def _is_normal_column(self, column_name):
        return column_name in self.columns and \
            column_name not in self._stock_columns_info_map

    def _calc(self, directive_str: str) -> np.ndarray:
        directive = self._parse_directive(directive_str)

        _, series = self._get_or_calc_series(directive, self._create_column)

        return series

    def _ensure_stock_type(self, df):
        new = StockDataFrame(df, create_stock_metas=False)
        # TODO: check columns and alises
        copy_stock_metas(self, new)
        return new


METHODS_TO_ENSURE_RETURN_TYPE = [
    'append',
    'drop',
    'set_index'
]

for method in METHODS_TO_ENSURE_RETURN_TYPE:
    ensure_return_type(StockDataFrame, method)
