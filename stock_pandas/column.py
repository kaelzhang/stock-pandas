import re

COLUMNS = [
    'open',
    'high',
    'low',
    'close'
]


def is_ohlc_column(column: str):
    return column in COLUMNS


class Command:
    def __init__(self, command, sub, args):
        self.name = command
        self.sub = sub
        self.args = args

REGEX_COMMAND = r'^([a-z]+)(\.[a-z]+)?\s*(:[a-z0-9-.\s]+(?:,[a-z0-9-.\s]+)*)?$'

def parse_command(name: str):
    name = name.strip()
    match = re.match(REGEX_COMMAND, name)

    if not match:
        raise ValueError('invalid command `{}`'.format(name))

    command, sub, args = match.group(1, 2, 3)
    sub = sub[1:].strip() if sub else None
    args = [a.strip() for a in args[1:].split(',')] if args else []

    return Command(command, sub, args)


def parse_expression(expression):
    if not expression:
        return

    try:
        return float(expression)
    except ValueError:
        return parse_command(expression)

REGEX_COLUMN_NAME = r'^([a-z0-9.:,\s]+)(?:([=<>/\\]+)([\S\s]+))?$'

def parse_column_name(name: str):
    name = name.strip()
    match = re.match(REGEX_COLUMN_NAME, name)

    if not match:
        raise ValueError('invalid column name `{}`'.format(name))

    raw_command, operator, expression = match.group(1, 2, 3)

    return parse_command(raw_command), operator, parse_expression(expression)
