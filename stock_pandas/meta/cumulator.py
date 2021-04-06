from typing import (
    Callable,
    Dict,
    List,
    Optional
)

from numpy import ndarray
from pandas import (
    DataFrame,
    Series,
    concat
)
from pandas._libs.tslibs import Timestamp

from stock_pandas.properties import KEY_CUMULATOR
from stock_pandas.common import set_attr

from .utils import (
    ColumnInfo,

    init_stock_metas,
    copy_stock_metas,
    copy_clean_stock_metas,
    # ensure_return_type
)

from .date import (
    apply_date,
    apply_date_to_df
)

from .time_frame import (
    TimeFrame,
    TimeFrameArg
)


Cumulator = Callable[[ndarray], float]
Cumulators = Dict[str, Cumulator]
ToAppend = List[Series]


def first(array: ndarray) -> float:
    return array[0]


def high(array: ndarray) -> float:
    return array.max()


def low(array: ndarray) -> float:
    return array.min()


def last(array: ndarray) -> float:
    return array[-1]


def add(array: ndarray) -> float:
    return array.sum()


def cum_append_type_error(date_col: Optional[str] = None) -> ValueError:
    message = 'the target to be `cum_append()`ed must have a DateTimeIndex'

    if date_col is None:
        return ValueError(message)

    return ValueError(f'{message} or a "{date_col}" column')


def append(
    df: 'MetaDataFrame',
    to_append: ToAppend,
    *args, **kwargs
) -> 'MetaDataFrame':
    duplicates = df[to_append[0].name:]

    return df.drop(duplicates.index).append(to_append, *args, **kwargs)


class _Cumulator:
    CUMULATORS: Dict[str, Cumulator] = {
        'open': first,
        'high': high,
        'low': low,
        'close': last,
        'volume': add
    }

    _to_cumulate: Optional[DataFrame]
    _to_append: ToAppend

    def __repr__(self) -> str:
        return f'<Cumulator date_col:{self._date_col}, time_frame:{self._time_frame}>'

    def init(
        self,
        df,
        source,
        date_col: Optional[str] = None,
        to_datetime_kwargs: dict = {},
        time_frame: TimeFrameArg = None,
        cumulators: Optional[Cumulators] = None
    ):
        is_meta_df = isinstance(source, MetaDataFrame)

        if date_col is not None:
            self._date_col = date_col
            self._to_datetime_kwargs = to_datetime_kwargs

            if is_meta_df:
                source_cumulator = source._cumulator

                if source_cumulator._date_col is None:
                    # Which means the source stock data frame has no date column, so we have to apply it
                    apply_date_to_df(
                        df,
                        date_col,
                        to_datetime_kwargs,
                        check=True
                    )
                elif source_cumulator._date_col != date_col:
                    raise ValueError(f'refuse to set date column as "{date_col}" since the original stock data frame already have a date column "{source_cumulator._date_col}"')
            else:
                apply_date_to_df(
                    df,
                    date_col,
                    to_datetime_kwargs,
                    check=True
                )
        else:
            if is_meta_df:
                # We should copy the source's cumulator settings
                self._merge_date_col(source._cumulator)
            else:
                self._date_col = None

        if time_frame is None:
            if is_meta_df:
                self._merge_time_frame(source._cumulator)
            else:
                self._time_frame = None

            return

        self._time_frame = TimeFrame.ensure(time_frame)

        self._cumulators = (
            # None means use the default cumulators
            cumulators if cumulators is not None
            else self.CUMULATORS
        ).copy()

        self._to_cumulate = None

    def _merge_date_col(self, source_cumulator: '_Cumulator'):
        self._date_col = source_cumulator._date_col

        if source_cumulator._date_col is None:
            return

        self._to_datetime_kwargs = source_cumulator._to_datetime_kwargs

    def _merge_time_frame(self, source_cumulator: '_Cumulator'):
        self._time_frame = source_cumulator._time_frame

        if source_cumulator._time_frame is None:
            return

        self._cumulators = source_cumulator._cumulators.copy()
        self._to_cumulate = source_cumulator._to_cumulate

    def add(self, column_name, cumulator: Cumulator):
        self._cumulators[column_name] = cumulator

    def apply_date_col(self, other):
        if self._date_col is not None:
            other = apply_date(
                self._date_col,
                self._to_datetime_kwargs,
                True,
                other
            )

        return other

    def cum_append(
        self,
        to: 'MetaDataFrame',
        # TODO:
        # support other types
        other: DataFrame,
        *args, **kwargs
    ) -> DataFrame:
        if self._date_col is None or self._time_frame is None:
            raise ValueError('date_col and time_frame must be specified before calling cum_append()')

        if not len(other):
            raise ValueError('the data frame to be appended is empty')

        other = self._convert_to_date_df(other)

        last_timestamp = (
            None if self._to_cumulate is None
            else self._to_cumulate[-1].iloc[-1].name
        )

        start = None
        last = None
        self._to_append = []

        for timestamp in other.index:
            if not isinstance(timestamp, Timestamp):
                raise cum_append_type_error(self._date_col)

            if start is None:
                start = timestamp

            if last_timestamp is None:
                last_timestamp = timestamp
                continue

            if (
                self._time_frame.unify(last_timestamp)
                != self._time_frame.unify(timestamp)
            ):
                self._cumulate(
                    # For a data frame of TimestampIndex,
                    # indexing are performed in a close range
                    None if last is None else other[start:last]
                )
                self._pre_append(True)

                start = timestamp

            last = timestamp

        self._cumulate(other[start:])
        # Append the rows even the latest time frame is not closed
        self._pre_append()

        new = append(to, self._to_append, *args, **kwargs)
        self._to_append.clear()

        return new

    def _convert_to_date_df(
        self,
        other: DataFrame
    ) -> DataFrame:
        date_col = self._date_col
        to_datetime_kwargs = self._to_datetime_kwargs

        if date_col is not None and date_col in other.columns:
            other = other.copy()
            apply_date_to_df(other, date_col, to_datetime_kwargs)

        return other

    def _cumulate(
        self,
        to_cumulate: Optional[DataFrame]
    ) -> Optional[DataFrame]:
        """
        Concat the givin data frame to self._to_cumulate
        """

        to_concat = [
            item
            for item in [to_cumulate, self._to_cumulate]
            if item is not None
        ]

        if not to_concat:
            return

        self._to_cumulate = (
            concat(to_concat) if len(to_concat) == 2
            else to_concat[0]
        )

    def _pre_append(
        self,
        clean: bool = False
    ):
        """
        Cumulate self._to_cumulate and append to self._to_append

        Args:
            clean (:obj:`bool`, optional): True then clean self._to_cumulate
        """

        to_cumulate = self._to_cumulate

        if to_cumulate is None:
            return

        if clean:
            self._to_cumulate = None

        if len(to_cumulate) == 1:
            # We do not need to cumulate
            self._to_append.append(to_cumulate.iloc[0])
            return

        # Use the values of the last row except columns of self._cumulators
        cumulated = to_cumulate.iloc[-1].copy()

        # Use the index of the first row
        cumulated.rename(to_cumulate.iloc[0].name)

        for column_name in cumulated.index:
            cumulator = self._cumulators.get(column_name)

            if cumulator is not None:
                cumulated[column_name] = cumulator(
                    cumulated[column_name].to_numpy()
                )

        self._to_append.append(cumulated)


class MetaDataFrame(DataFrame):
    """
    The subclass of pandas.DataFrame which ensures return type of all kinds methods to be MetaDataFrame
    """

    _stock_indexer_slice: Optional[slice] = None
    _stock_indexer_axis: int = 0

    _stock_aliases_map: Dict[str, str]
    _stock_columns_info_map: Dict[str, ColumnInfo]

    # Methods that used by pandas and sub classes
    # --------------------------------------------------------------------

    # TODO:
    # whether *args, **kwargs here are necessary
    def __finalize__(self, other, *args, **kwargs) -> 'MetaDataFrame':
        """
        Propagate metadata from other to self.

        This method overrides `DataFrame.__finalize__`
        which ensures the meta info of StockDataFrame
        """

        super().__finalize__(other, *args, **kwargs)

        if isinstance(other, MetaDataFrame):
            copy_clean_stock_metas(
                other,
                self,
                other._stock_indexer_slice,
                other._stock_indexer_axis
            )

        return self

    def _slice(self, slice_obj: slice, axis: int = 0) -> 'MetaDataFrame':
        """
        This method is called in several cases, self.iloc[slice] for example

        We mark the slice and axis here to prevent extra calculations
        """

        self._stock_indexer_slice = slice_obj
        self._stock_indexer_axis = axis

        try:
            result = super()._slice(slice_obj, axis)
        except Exception as e:
            raise e
        finally:
            self._stock_indexer_slice = None
            self._stock_indexer_axis = 0

        return result

    # --------------------------------------------------------------------

    def __init__(
        self,
        data=None,
        date_col: Optional[str] = None,
        to_datetime_kwargs: dict = {},
        time_frame: TimeFrameArg = None,
        cumulators: Optional[Cumulators] = None,
        source: Optional['MetaDataFrame'] = None,
        *args,
        **kwargs
    ) -> None:
        """
        Creates a stock data frame

        Args:
            data (ndarray, Iterable, dict, DataFrame, StockDataFrame): data
            date_col (:obj:`str`, optional): If set, then the column named `date_col` will convert and set as the DateTimeIndex of the data frame
            to_datetime_kwargs (dict): the keyworded arguments to be passed to `pandas.to_datetime()`. It only takes effect if `date_col` is specified.
            time_frame (str, TimeFrame): defines the time frame of the stock
            source (:obj:`StockDataFrame`, optional): the source to copy meta data from if the source is a StockDataFrame. Defaults to `data`
            *args: other pandas.DataFrame arguments
            **kwargs: other pandas.DataFrame keyworded arguments
        """

        DataFrame.__init__(self, data, *args, **kwargs)

        if self.columns.nlevels > 1:
            # For now, I admit,
            # there are a lot of works to support MultiIndex dataframes
            raise ValueError(
                'stock-pandas does not support dataframes with MultiIndex columns'
            )

        if source is None:
            source = data

        if isinstance(source, MetaDataFrame):
            copy_stock_metas(source, self)
        else:
            init_stock_metas(self)

        self._cumulator.init(
            self,
            source,
            date_col=date_col,
            to_datetime_kwargs=to_datetime_kwargs,
            time_frame=time_frame,
            cumulators=cumulators
        )

    @property
    def _cumulator(self) -> _Cumulator:
        cumulator = getattr(self, KEY_CUMULATOR, None)

        if cumulator is None:
            cumulator = _Cumulator()
            set_attr(self, KEY_CUMULATOR, cumulator)

        return cumulator

    # Public Methods of stock-pandas
    # --------------------------------------------------------------------

    def add_cumulator(self, column_name: str, cumulator: Cumulator) -> None:
        self._cumulator.add(column_name, cumulator)

    def append(self, other, *args, **kwargs) -> 'MetaDataFrame':
        """
        Appends row(s) of other to the end of caller, applying date_col to the newly-appended row(s) if possible, and returning a new object

        The args of this method is the same as `pandas.DataFrame.append`
        """

        other = self._cumulator.apply_date_col(other)
        concatenated = super().append(other, *args, **kwargs)

        # Subclass could override property _constructor to change the
        # return type
        Constructor = self._constructor

        if isinstance(concatenated, Constructor):
            # super().append will lose metas
            concatenated._cumulator.init(
                concatenated,
                self
            )
        else:
            # If `self` is an empty StockDataFrame,
            # super().append() returns a DataFrame
            concatenated = Constructor(concatenated, source=self)

        return concatenated

    def cum_append(
        self,
        other,
        *args,
        **kwargs
    ) -> 'MetaDataFrame':
        """
        Appends row(s) of other to the end of caller, applying date_col to the newly-appended row(s) if possible, and returning a new object

        The args of this method is the same as `pandas.DataFrame.append`
        """

        return self._cumulator.cum_append(
            self,
            other,
            *args, **kwargs
        )
