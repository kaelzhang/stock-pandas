import re
from typing import (
    Optional,
    Tuple,
    Iterator
)

# operators
# (
# )
# :
# ,
REGEX_SPECIAL_CHARS = re.compile(r'[\\=<>/]+|[():,\r\n]', re.A)

STR_CARRIAGE_RETURN = '\n'
STR_COLON = ':'
STR_COMMA = ','
STR_PARAN_L = '('
STR_PARAN_R = ')'

REGEX_NOT_WHITESPACE = re.compile(r'[^\s]', re.A)

Loc = Tuple[int, int]


class Token:
    __slots__ = (
        'value', 'loc', 'special', 'EOF'
    )

    def __init__(
        self,
        loc: Loc,
        value: Optional[str] = None,
        special: Optional[bool] = False,
        EOF: Optional[bool] = False
    ):
        self.value = value
        self.loc = loc
        self.special = special
        self.EOF = EOF


def create_normal_token(text, line, col) -> Optional[Token]:
    if not text:
        return

    m = REGEX_NOT_WHITESPACE.search(text)

    if m is None:
        # After `\n` and before `>`:
        #
        # abc \n
        #      > 1
        return

    start = m.span()[0]

    return Token(
        (line, col + start),
        text[start:].rstrip()
    )


class Tokenizer:
    def __init__(self, input: str) -> None:
        # We should not strip input here, or pos will be wrong
        self._input = input
        self._length = len(input)
        self._saved_token = None

        self._reset()

    def __iter__(self) -> Iterator['Token']:
        self._reset()
        return self

    def __next__(self) -> Token:
        if self._ended:
            raise StopIteration()

        return self._next()

    def _reset(self) -> None:
        self._pos = 0
        self._line = 1
        self._column = 1

        self._ended = False

    def _end(self) -> Token:
        self._ended = True
        return Token(
            loc=(self._line, self._column),
            EOF=True
        )

    def _next(self) -> Token:
        token = self._saved_token
        if token:
            self._saved_token = None
            return token

        m = REGEX_SPECIAL_CHARS.search(self._input, self._pos)

        # Reach the end,
        # We don't raise StopIteration, because we do not need this actually
        if m is None:
            normal_token = create_normal_token(
                self._input[self._pos:],
                self._line,
                self._column
            )

            self._column += self._length - self._pos
            self._pos = self._length

            return normal_token or self._end()

        special_start, special_end = m.span()

        # the text of the string before the special token
        text = self._input[self._pos:special_start]

        # the text of of special token
        special_text = m.group()

        pos = self._pos
        line = self._line
        col = self._column

        # Update the pos and column
        self._pos = special_end
        self._column += special_end - pos

        if special_text == STR_CARRIAGE_RETURN:
            # We will abandon CR token

            normal_token = create_normal_token(text, line, col)

            self._line += 1
            self._column = 1

            return normal_token if normal_token else self._next()

        else:
            special_token = Token(
                (line, col + special_start - pos),
                special_text,
                True
            )

            normal_token = create_normal_token(text, line, col)

            if normal_token:
                self._saved_token = special_token
                return normal_token
            else:
                return special_token
