import re

from stock_pandas.common import is_blank

# operators
# (
# )
# :
# ,
REGEX_SPECIAL_CHARS = re.compile('[=<>/\\]+|[():,\r\n]', re.A)

STR_CARRIAGE_RETURN = '\n'


class Tokenizer:
    def __init__(self, input: str):
        self._input = input
        self._pos = 0
        self._line = 1
        self._column = 1
        self._saved_token = None

    def __iter__(self):
        self._pos = 0
        return self

    def _next(self):
        token = self._saved_token
        if token:
            self._saved_token = None
            return token

        m = REGEX_SPECIAL_CHARS.search(self._input, self._pos)

        # Reach the end,
        # We don't raise StopIteration, because we do not need this actually
        if m is None:
            return None

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

        # abc \n
        #      > 1
        normal_is_blank = is_blank(text)

        if special_text == STR_CARRIAGE_RETURN:
            # We will abandon CR token

            self._line += 1
            self._column = 1

            if normal_is_blank:
                # abandon all, and return next
                return self._next()
            else:
                return (
                    # value
                    text,
                    # is_special
                    False,
                    # pos
                    pos,
                    # location
                    (line, col)
                )

        else:
            special_token = (
                special_text,
                True,
                special_start,
                (line, col + special_start - pos)
            )

            if normal_is_blank:
                # Just return the special token
                return special_token
            else:
                self._saved_token = special_token

                return (
                    text,
                    False,
                    pos,
                    (line, col)
                )

    def __next__(self):
        return self._next()







