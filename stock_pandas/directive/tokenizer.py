import re
from typing import (
    Optional,
    Tuple
)

# operators
# (
# )
# :
# ,
REGEX_SPECIAL_CHARS = re.compile(r'[\=<>/]+|[():,\r\n]', re.A)

STR_CARRIAGE_RETURN = '\n'
STR_COLON = ':'
STR_COMMA = ','
STR_PARAN_L = '('
STR_PARAN_R = ')'

REGEX_NOT_WHITESPACE = re.compile(r'[^\s]', re.A)


class Token:
    def __init__(
        self,
        value: Optional[str]=None,
        loc: Optional[Tuple[int, int]]=None,
        special: Optional[bool]=False
    ):
        self.value = value
        self.loc = loc
        self.special = special

EOF = Token()


def create_normal_token(text, line, col):
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
        text[start:].rstrip(),
        (line, col + start)
    )


class Tokenizer:
    def __init__(self, input: str):
        # We should not strip input here, or pos will be wrong
        self._input = input
        self._length = len(input)
        self._saved_token = None

        self._reset()

    def __iter__(self):
        self._reset()
        return self

    def __next__(self):
        if self._ended:
            raise StopIteration()

        return self._next()

    def _reset(self):
        self._pos = 0
        self._line = 1
        self._column = 1

        self._ended = False

    def _end(self):
        self._ended = True
        return EOF

    def _next(self):
        token = self._saved_token
        if token:
            self._saved_token = None
            return token

        m = REGEX_SPECIAL_CHARS.search(self._input, self._pos)

        # Reach the end,
        # We don't raise StopIteration, because we do not need this actually
        if m is None:
            rest = self._input[self._pos:]
            self._pos = self._length

            return create_normal_token(
                rest,
                self._line,
                self._column
            ) or self._end()

        print(m, m.group(), m.span())

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
                special_text,
                (line, col + special_start - pos),
                True
            )

            normal_token = create_normal_token(text, line, col)

            if normal_token:
                self._saved_token = special_token
                return normal_token
            else:
                return special_token
