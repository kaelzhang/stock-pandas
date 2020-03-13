from stock_pandas.directive.tokenizer import Tokenizer

def test_basic():
    input = """a: b
   > 11"""

    tokens = [
        ('a', False, (1, 1)),
        (':', True, (1, 2)),
        ('b', False, (1, 4)),
        ('>', True, (2, 4)),
        ('11', False, (2, 6))
    ]

    i = iter(Tokenizer(input))

    for token in tokens:
        got = next(i)
        print(got)
        assert got == token
