from typing import (
    Optional
)
from copy import (
    copy,
    deepcopy
)

from pandas import DataFrame

from .directive import Directive


class ColumnInfo:
    __slots__ = (
        'size',
        'directive',
        'period'
    )

    size: int
    directive: Directive
    period: int

    def __init__(
        self,
        size: int,
        directive: Directive,
        period: int
    ) -> None:
        self.size = size
        self.directive = directive
        self.period = period

    def __deepcopy__(self, _) -> 'ColumnInfo':
        return ColumnInfo(
            self.size,
            self.directive,
            self.period
        )

    def update(self, size) -> 'ColumnInfo':
        """Creates a new ColumnInfo and update the size
        """

        return ColumnInfo(
            size,
            self.directive,
            self.period
        )

    def __repr__(self) -> str:
        return f'<ColumnInfo {self.directive}, size:{self.size}, period:{self.period}>'  # noqa: E501


KEY_ALIAS_MAP = '_stock_aliases_map'
KEY_COLUMNS_INFO_MAP = '_stock_columns_info_map'

OptionalSlice = Optional[slice]


def update_info_size(
    info: ColumnInfo,
    source_length: int,
    slice_obj: OptionalSlice,
    axis: int
) -> ColumnInfo:
    if (
        # The slicing is not for rows but the rows has been truncated
        axis == 1
        or slice_obj is None
        or slice_obj.step is not None
    ):
        return info.update(0)

    size = info.size
    stop = slice_obj.stop
    start = slice_obj.start

    if stop is not None:
        if stop < 0:
            stop = source_length + stop

        # Case 1:
        #          stop
        #           |       size
        #           |        |
        # ---------------------------------

        # Case 2:
        #                   stop
        #          size      |
        #           |        |
        # ---------------------------------
        size = min(size, stop)

    if start is not None:
        if start < 0:
            start = source_length + start

        size -= start

    return info.update(size)


def set_attr(target, key, value) -> None:
    object.__setattr__(target, key, value)


def init_stock_metas(target) -> None:
    set_attr(target, KEY_ALIAS_MAP, {})
    set_attr(target, KEY_COLUMNS_INFO_MAP, {})


def copy_stock_metas(
    source,
    target
) -> None:
    """Simply copy metadata from source to target
    """

    set_attr(
        target,
        KEY_ALIAS_MAP,
        copy(getattr(source, KEY_ALIAS_MAP))
    )

    set_attr(
        target,
        KEY_COLUMNS_INFO_MAP,
        deepcopy(getattr(source, KEY_COLUMNS_INFO_MAP))
    )


def copy_clean_stock_metas(
    source,
    target,
    slice_obj: OptionalSlice = None,
    axis: int = 0
) -> None:
    columns = target.columns

    source_aliases_map = getattr(source, KEY_ALIAS_MAP)

    aliases_map = {}
    for alias, column in source_aliases_map.items():
        # Column `column` might be dropped in `target`
        # by dataframe.drop(columns=some_columns)
        # so we need to check it

        # TODO: if alias is in columns, something wrong happened
        # - support .iloc, loc, and other indexing and setting methods
        if column in columns:
            aliases_map[alias] = column

    set_attr(target, KEY_ALIAS_MAP, aliases_map)

    source_length = len(source)

    need_clean = len(target) < source_length
    source_columns_info_map = getattr(source, KEY_COLUMNS_INFO_MAP)

    columns_info_map = {}
    for column, info in source_columns_info_map.items():
        if column in columns:

            # Set the size to 0,
            # which indicates that the column needs to be calculated again
            columns_info_map[
                column
            ] = update_info_size(
                info,
                source_length,
                slice_obj,
                axis
            ) if need_clean else info

    set_attr(target, KEY_COLUMNS_INFO_MAP, columns_info_map)


def ensure_return_type(
    cls,
    method: str,
    should_apply_constructor: bool
) -> None:
    def helper(self, *args, **kwargs):
        ret = getattr(super(cls, self), method)(*args, **kwargs)

        if should_apply_constructor:
            ret = cls(ret)

        copy_stock_metas(self, ret)

        return ret

    helper.__doc__ = getattr(DataFrame, method).__doc__

    setattr(cls, method, helper)
