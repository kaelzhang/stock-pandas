from stock_pandas.directive.parser import Parser

def test_basic():
    input = 'increase:(ma:20,close),3'

    parser = Parser(input)

    print(parser.parse())
