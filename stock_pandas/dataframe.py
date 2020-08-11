from typing import (
    Tuple,
    Type,
    Union,
    List,
    Optional
)

from pandas import (
    DataFrame,
    Series,
    to_datetime
)
from pandas.core.generic import NDFrame

import numpy as np

from .directive import parse

from .common import (
    meta_property,
    copy_stock_metas,
    ensure_return_type,

    KEY_ALIAS_MAP,
    KEY_COLUMNS_INFO_MAP,
    KEY_DIRECTIVES_CACHE,

    DirectiveCache
)


class ColumnInfo:
    def __init__(self, size, directive, period) -> None:
        self.size = size
        self.directive = directive
        self.period = period

    def update(self, size) -> 'ColumnInfo':
        """Creates a new ColumnInfo and update the size
        """

        return ColumnInfo(
            size,
            self.directive,
            self.period
        )


class StockDataFrame(DataFrame):
    """The wrapper class for `pandas.DataFrame`

    Args definitions are the same as `pandas.DataFrame`
    """

    _create_column: bool

    _stock_aliases_map = meta_property(
        KEY_ALIAS_MAP, lambda: {}
    )

    _stock_columns_info_map = meta_property(
        KEY_COLUMNS_INFO_MAP, lambda: {}
    )

    _stock_directives_cache = meta_property(
        KEY_DIRECTIVES_CACHE, lambda: DirectiveCache()
    )

    @property
    def _constructor(self) -> Type['StockDataFrame']:
        """This method overrides `DataFrame._constructor`
        which ensures the return type of several DataFrame methods
        """

        return StockDataFrame

    def __finalize__(self, other, *args, **kwargs) -> 'StockDataFrame':
        """This method overrides `DataFrame.__finalize__`
        which ensures the meta info of StockDataFrame
        """

        super().__finalize__(other, *args, **kwargs)

        if isinstance(other, StockDataFrame):
            copy_stock_metas(other, self)

        return self

    def __init__(
        self,
        data=None,
        date_column=None,
        *args,
        **kwargs
    ) -> None:
        DataFrame.__init__(self, data, *args, **kwargs)

        if self.columns.nlevels > 1:
            # For now, I admit,
            # there are a lot of works to support MultiIndex dataframes
            raise ValueError(
                'stock-pandas does not support dataframes with MultiIndex columns'  # noqa:E501
            )

        if isinstance(data, StockDataFrame):
            copy_stock_metas(data, self)

        self._create_column = False

        if date_column:
            self[date_column] = to_datetime(self[date_column])
            self.set_index(date_column, inplace=True)

    def __getitem__(self, key) -> Union[Series, 'StockDataFrame']:
        if isinstance(key, str):
            key = self._map_single_key(key)

            # We just return super __getitem__,
            # because the result must be series
            return super().__getitem__(key)

        if isinstance(key, list):
            key = self._map_keys(key)

        # else: key of another type

        result = super().__getitem__(key)

        if isinstance(result, Series):
            # The series has already been fulfilled by
            # `self._get_or_calc_series()`
            return result

        result = StockDataFrame(result)

        return result

    def get_column(self, key: str) -> Series:
        """Gets the column directly from dataframe by key.

        This method applies column name aliases before getting the value.
        """

        origin_key = key

        if key in self._stock_aliases_map:
            # Map alias, if the key is an alias
            key = self._stock_aliases_map[key]

        try:
            return self._get_item_cache(key)
        except KeyError:
            raise KeyError(f'column "{origin_key}" not found')

    def exec(
        self,
        directive_str: str,
        create_column: Optional[bool] = None
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
            # Vscode extension pyright could not handle this, so type ignore
            self._create_column = create_column  # type: ignore
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

    def _map_keys(self, keys) -> List:
        return [
            self._map_single_key(key)
            for key in keys
        ]

    def _map_single_key(self, key):
        if not isinstance(key, str):
            # It might be an `pandas.DataFrame` indexer type,
            # or an KeyError which we should let pandas raise
            return key

        if key in self._stock_aliases_map:
            # Map alias, if the key is an alias
            key = self._stock_aliases_map[key]

        if self._is_normal_column(key):
            # There exists a column named `key`,
            # and it is a normal column
            return key

        # Not exists
        directive = self._parse_directive(key)

        # It is a valid directive
        # If the column exists, then fulfill it,
        #   else create it
        column_name, _ = self._get_or_calc_series(directive, True)

        # Append the real column name to the mapped key,
        #   So `pandas.DataFrame.__getitem__` could index the right column
        return column_name

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

            self._set_new_item(name, array)

        return name, array

    def _set_new_item(
        self,
        name: str,
        value: np.ndarray
    ) -> None:
        """Set a new column and avoid SettingWithCopyWarning by using
        pandas internal APIs

        see: https://github.com/pandas-dev/pandas/blob/v1.1.0/pandas/core/frame.py#L3114
        """  # noqa: E501

        NDFrame._set_item(self, name, value)

    def _fulfill_series(self, column_name: str) -> np.ndarray:
        column_info = self._stock_columns_info_map.get(column_name)
        size = len(self)

        array = self.get_column(column_name).to_numpy()

        if size == column_info.size:
            # Already fulfilled
            return array

        neg_delta = column_info.size - size

        # Sometimes, there is not enough items to calculate
        calc_delta = max(
            neg_delta - column_info.period + 1,
            - size
        )

        calc_slice = slice(calc_delta, None)
        fulfill_slice = slice(neg_delta, None)

        partial, _ = column_info.directive.run(self, calc_slice)

        if neg_delta == calc_delta:
            array = partial
        else:
            array[fulfill_slice] = partial[fulfill_slice]

        self._set_new_item(column_name, array)

        column_info.size = size

        return array

    def _is_normal_column(self, column_name) -> bool:
        return column_name in self.columns and \
            column_name not in self._stock_columns_info_map

    def _calc(self, directive_str: str) -> np.ndarray:
        directive = self._parse_directive(directive_str)

        _, series = self._get_or_calc_series(directive, self._create_column)

        return series


METHODS_TO_ENSURE_RETURN_TYPE = [
    ('append', False),
    ('astype', True)
]

for method, should_apply_constructor in METHODS_TO_ENSURE_RETURN_TYPE:
    ensure_return_type(StockDataFrame, method, should_apply_constructor)
