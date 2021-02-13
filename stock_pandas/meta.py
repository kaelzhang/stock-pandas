from typing import (
    Optional
)
from copy import deepcopy

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


KEY_ALIAS_MAP = '__stock_aliases_map'
KEY_COLUMNS_INFO_MAP = '__stock_columns_info_map'
KEY_DIRECTIVES_CACHE = '__stock_directives_cache'

OptionalSlice = Optional[slice]


def update_info_size(
    info: ColumnInfo,
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
        size = min(size, stop)

    if start is not None:
        size -= start

    return info.update(size)


def copy_directive_cache(source, target):
    source_stock_directives_cache = getattr(source, KEY_DIRECTIVES_CACHE, None)

    if source_stock_directives_cache is not None:
        object.__setattr__(
            target,
            KEY_DIRECTIVES_CACHE,
            source_stock_directives_cache
        )


def copy_clean_stock_metas(
    source,
    target,
    slice_obj: OptionalSlice = None,
    axis: int = 0
) -> None:
    copy_directive_cache(source, target)

    columns = target.columns

    # target_length = len(target)
    # source_length = len(source)

    need_clean = len(target) < len(source)

    source_aliases_map = getattr(source, KEY_ALIAS_MAP, None)

    if source_aliases_map is not None:
        aliases_map = {}
        for alias, column in source_aliases_map.items():
            # Column `column` might be dropped in `target`
            # by dataframe.drop(columns=some_columns)
            # so we need to check it

            # TODO: if alias is in columns, something wrong happened
            # - support .iloc, loc, and other indexing and setting methods
            if column in columns:
                aliases_map[alias] = column

        # Use `object.__setattr__` to avoid pandas UserWarning:
        # > Pandas doesn't allow columns to be created via a new attribute name
        object.__setattr__(target, KEY_ALIAS_MAP, aliases_map)

    source_columns_info_map = getattr(source, KEY_COLUMNS_INFO_MAP, None)

    if source_columns_info_map is not None:
        columns_info_map = {}
        for column, info in source_columns_info_map.items():
            if column in columns:

                # Set the size to 0,
                # which indicates that the column needs to be calculated again
                columns_info_map[
                    column
                ] = update_info_size(
                    info,
                    slice_obj,
                    axis
                ) if need_clean else info

        object.__setattr__(target, KEY_COLUMNS_INFO_MAP, columns_info_map)


def copy_stock_metas(
    source,
    target
) -> None:
    """Simply copy metadata from source to target
    """

    copy_directive_cache(source, target)

    source_aliases_map = getattr(source, KEY_ALIAS_MAP, None)
    if source_aliases_map is not None:
        object.__setattr__(target, KEY_ALIAS_MAP, source_aliases_map)

    source_columns_info_map = getattr(source, KEY_COLUMNS_INFO_MAP, None)
    if source_columns_info_map is not None:
        object.__setattr__(
            target,
            KEY_COLUMNS_INFO_MAP,
            deepcopy(source_columns_info_map)
        )


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
