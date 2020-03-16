from stock_pandas.common import (
    period_to_int
)


class CommandPreset:
    __slots__ = (
        'formula',
        'args',
        'subs_map',
        'sub_aliases_map'
    )

    def __init__(
        self,
        formula=None,
        args=None,
        subs_map=None,
        sub_aliases_map=None
    ):
        self.formula = formula
        self.args = args
        self.subs_map = subs_map
        self.sub_aliases_map = sub_aliases_map


COMMANDS = {}


arg_period = (
    # Default value for the first argument,
    # `None` indicates that it is not an optional argument
    None,
    # Validator and setter for the first argument.
    # The function could throw
    period_to_int
)
