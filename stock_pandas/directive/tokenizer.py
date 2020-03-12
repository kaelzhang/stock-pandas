import re

# operators
# (
# )
# :
# ,
REGEX_SPECIAL_CHARS = re.compile('[=<>/\\]+|[():,\r\n]', re.A)

STR_CARRIAGE_RETURN = '\n'
STR_COLON = ':'
STR_DOT = '.'

EOF = (None, None)


REGEX_NOT_WHITESPACE = re.compile('[^\s]', re.A)

def create_normal_token(text, pos, line, col):
    if not text:
        return

    # print(text, pos, line, col)
    m = REGEX_NOT_WHITESPACE.search(text)

    if m is None:
        # After `\n` and before `>`:
        #
        # abc \n
        #      > 1
        return

    start = m.span()[0]

    return (
        # value
        text[start:].rstrip(),
        # is_special
        False,
        # pos
        pos + start,
        # location
        (line, col + start)
    )


class Tokenizer:
    def __init__(self, input: str):
        self._input = input.strip()
        self._pos = 0
        self._line = 1
        self._column = 1
        self._saved_token = None

    def __iter__(self):
        self._pos = 0
        return self

    def _end(self):
        return create_normal_token(
            self._input[self._pos:],
            self._pos,
            self._line,
            self._column
        ) or EOF

    def _next(self):
        token = self._saved_token
        if token:
            self._saved_token = None
            return token

        m = REGEX_SPECIAL_CHARS.search(self._input, self._pos)

        # Reach the end,
        # We don't raise StopIteration, because we do not need this actually
        if m is None:
            return self._end()

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

        normal_token = create_normal_token(text, pos, line, col)
        # print('normal token', normal_token, special_text == STR_CARRIAGE_RETURN)

        if special_text == STR_CARRIAGE_RETURN:
            # We will abandon CR token

            self._line += 1
            self._column = 1

            return normal_token if normal_token else self._next()

        else:
            special_token = (
                special_text,
                True,
                special_start,
                (line, col + special_start - pos)
            )

            if normal_token:
                self._saved_token = special_token
                return normal_token
            else:
                return special_token


    def __next__(self):
        return self._next()







